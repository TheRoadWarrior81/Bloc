import time
from google import genai
from google.genai import types
from config import settings
from auth import get_db, release_db
from bloc_logger import get_logger

logger = get_logger("embeddings")

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_embedding(text: str) -> list[float]:
    """Call Gemini text-embedding-004 and return a 768-dim vector."""
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
    )
    return result.embeddings[0].values


def embed_message(message_id: int, content: str) -> None:
    """Generate an embedding for a message and store it in message_embeddings.
    Also logs the call to ai_logs."""
    start = time.perf_counter()
    error_str = None
    embedding = None

    try:
        embedding = generate_embedding(content)
    except Exception as e:
        error_str = str(e)
        logger.error(f"embedding failed message_id={message_id}: {e}")

    latency_ms = int((time.perf_counter() - start) * 1000)

    conn = get_db()
    cur = conn.cursor()
    try:
        if embedding:
            cur.execute(
                """
                INSERT INTO message_embeddings (message_id, embedding)
                VALUES (%s, %s)
                ON CONFLICT (message_id) DO NOTHING
                """,
                (message_id, str(embedding))
            )

        cur.execute(
            """
            INSERT INTO ai_logs (feature, input_tokens, latency_ms, error)
            VALUES (%s, %s, %s, %s)
            """,
            ("embed_message", len(content.split()), latency_ms, error_str)
        )
        conn.commit()
        logger.info(f"embedded message_id={message_id} latency={latency_ms}ms")
    except Exception as e:
        conn.rollback()
        logger.error(f"embed_message db write failed: {e}")
    finally:
        cur.close()
        release_db(conn)

def search_messages(query: str, circle_id: int, limit: int = 10) -> list[dict]:
    """Embed query and return ranked messages by cosine similarity."""
    query_embedding = generate_embedding(query)
    embedding_str = str(query_embedding)  # matches how embed_message stores vectors

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    m.id,
                    m.content,
                    m.sender_id,
                    m.created_at,
                    me.embedding <=> %s::vector AS distance
                FROM message_embeddings me
                JOIN messages m ON m.id = me.message_id
                WHERE m.circle_id = %s
                ORDER BY distance ASC
                LIMIT %s
                """,
                (embedding_str, circle_id, limit),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": row[0],
                    "content": row[1],
                    "sender_id": row[2],
                    "created_at": row[3].isoformat(),
                    "score": round(1 - float(row[4]), 4),
                }
                for row in rows
            ]
    finally:
        release_db(conn)