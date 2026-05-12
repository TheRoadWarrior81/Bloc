"""
scripts/backfill_embeddings.py

One-shot script to embed all messages not yet in message_embeddings.
Run once from Codespaces against production DB:

    DB_URL=<your_direct_db_url> python scripts/backfill_embeddings.py

Or if DB_URL_DIRECT is set in .env, just run:

    python scripts/backfill_embeddings.py
"""

import os
import sys
import time
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Prefer DB_URL_DIRECT for direct connection (bypasses pooler, safer for scripts)
DB_URL = os.getenv("DB_URL_DIRECT") or os.getenv("DB_URL")
if not DB_URL:
    print("ERROR: No DB_URL_DIRECT or DB_URL found in environment.")
    sys.exit(1)

# Add project root to path so we can import services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.embeddings import embed_message

SLEEP_BETWEEN_CALLS = 0.5  # seconds — stays well under Gemini free tier RPM


def fetch_unembedded_messages(conn) -> list[tuple[int, str]]:
    """Return (id, content) for all messages not yet in message_embeddings."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT m.id, m.content
            FROM messages m
            WHERE NOT EXISTS (
                SELECT 1 FROM message_embeddings me
                WHERE me.message_id = m.id
            )
            ORDER BY m.id ASC
            """
        )
        return cur.fetchall()


def main():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True

    try:
        rows = fetch_unembedded_messages(conn)
    finally:
        conn.close()

    total = len(rows)
    if total == 0:
        print("✓ All messages already embedded. Nothing to do.")
        return

    print(f"Found {total} message(s) without embeddings. Starting backfill...")
    print(f"Estimated time: ~{round(total * SLEEP_BETWEEN_CALLS / 60, 1)} min\n")

    success = 0
    failed = 0

    for i, (message_id, content) in enumerate(rows, start=1):
        try:
            embed_message(message_id=message_id, content=content)
            success += 1
            print(f"[{i}/{total}] ✓ message_id={message_id}")
        except Exception as e:
            failed += 1
            print(f"[{i}/{total}] ✗ message_id={message_id} — {e}")

        if i < total:
            time.sleep(SLEEP_BETWEEN_CALLS)

    print(f"\nDone. {success} succeeded, {failed} failed.")
    if failed:
        print("Re-run the script to retry failed messages — it skips already-embedded ones.")


if __name__ == "__main__":
    main()