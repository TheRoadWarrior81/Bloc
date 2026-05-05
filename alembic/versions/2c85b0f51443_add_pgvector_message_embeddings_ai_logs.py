"""add_pgvector_message_embeddings_ai_logs

Revision ID: 2c85b0f51443
Revises: 5f7fa962789a
Create Date: 2026-05-05 01:05:16.629897
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '2c85b0f51443'
down_revision: Union[str, Sequence[str], None] = '5f7fa962789a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector extension enabled manually on Neon via SQL editor
    # (CREATE EXTENSION inside Alembic transaction is unreliable on Neon)

    op.execute("""
        CREATE TABLE IF NOT EXISTS message_embeddings (
            id          SERIAL PRIMARY KEY,
            message_id  INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
            embedding   vector(3072) NOT NULL,
            created_at  TIMESTAMP DEFAULT NOW(),
            UNIQUE(message_id)
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_message_embeddings_vector
        ON message_embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_logs (
            id              SERIAL PRIMARY KEY,
            feature         TEXT NOT NULL,
            input_tokens    INTEGER,
            output_tokens   INTEGER,
            latency_ms      INTEGER,
            error           TEXT,
            created_at      TIMESTAMP DEFAULT NOW()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai_logs")
    op.execute("DROP TABLE IF EXISTS message_embeddings")