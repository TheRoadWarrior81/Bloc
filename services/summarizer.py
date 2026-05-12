import time
from groq import Groq
from config import settings
from auth import get_db, release_db
from bloc_logger import get_logger

logger = get_logger("summarizer")

client = Groq(api_key=settings.GROQ_API_KEY)

_SUMMARY_PROMPT = """\
You are summarizing recent activity in a group chat.
Below are the last {n} messages in chronological order.
Write a 3-5 sentence digest of what has been discussed.
Be factual and concise. Do not invent anything not present in the messages.

Messages:
{formatted_messages}

Summary:"""


def summarize_circle(circle_id: int, n: int = 50) -> dict:
    """
    Fetch the last n messages from circle_id, send to Groq,
    return a digest string plus metadata. Logs the call to ai_logs.
    """
    # ── 1. Fetch messages ────────────────────────────────────────────────────
    conn = get_db()
    rows = []
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT m.content, u.username, m.created_at
                FROM messages m
                JOIN users u ON u.id = m.user_id
                WHERE m.circle_id = %s
                ORDER BY m.created_at DESC
                LIMIT %s
                """,
                (circle_id, n),
            )
            rows = cur.fetchall()
    finally:
        release_db(conn)

    if not rows:
        return {"summary": "No messages yet in this circle.", "message_count": 0}

    # Reverse so oldest → newest (we fetched DESC)
    rows = list(reversed(rows))
    formatted = "\n".join(f"[{row[1]}]: {row[0]}" for row in rows)
    prompt = _SUMMARY_PROMPT.format(n=len(rows), formatted_messages=formatted)

    # ── 2. Call Groq ─────────────────────────────────────────────────────────
    start = time.perf_counter()
    error_str = None
    summary_text = None
    input_tokens = 0

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0.3,
        )
        summary_text = response.choices[0].message.content.strip()
        input_tokens = response.usage.prompt_tokens
    except Exception as e:
        error_str = str(e)
        logger.error(f"summarize failed circle_id={circle_id}: {e}")

    latency_ms = int((time.perf_counter() - start) * 1000)

    # ── 3. Log to ai_logs ────────────────────────────────────────────────────
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO ai_logs (feature, input_tokens, latency_ms, error)
            VALUES (%s, %s, %s, %s)
            """,
            ("summarize_circle", input_tokens, latency_ms, error_str),
        )
        conn.commit()
        logger.info(
            f"summarized circle_id={circle_id} messages={len(rows)} "
            f"tokens={input_tokens} latency={latency_ms}ms"
        )
    except Exception as e:
        conn.rollback()
        logger.error(f"summarize_circle db write failed: {e}")
    finally:
        cur.close()
        release_db(conn)

    if error_str:
        raise RuntimeError(error_str)

    return {"summary": summary_text, "message_count": len(rows)}