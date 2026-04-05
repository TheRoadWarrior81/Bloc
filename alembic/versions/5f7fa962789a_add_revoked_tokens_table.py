"""add revoked_tokens table

Revision ID: 5f7fa962789a
Revises: ac3759135ecd
Create Date: 2026-04-05 20:45:00.021262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f7fa962789a'
down_revision: Union[str, Sequence[str], None] = 'ac3759135ecd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
        CREATE TABLE revoked_tokens (
            jti TEXT PRIMARY KEY,
            revoked_at TIMESTAMP DEFAULT NOW(),
            expires_at TIMESTAMP NOT NULL
        );
        CREATE INDEX idx_revoked_tokens_expires ON revoked_tokens(expires_at);
    """)

def downgrade():
    op.execute("DROP TABLE IF EXISTS revoked_tokens;")