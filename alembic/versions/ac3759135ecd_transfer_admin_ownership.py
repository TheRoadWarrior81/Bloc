"""transfer_admin_ownership

Revision ID: ac3759135ecd
Revises: 591170e3861c
Create Date: 2026-04-03 18:39:20.503304

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac3759135ecd'
down_revision: Union[str, Sequence[str], None] = '591170e3861c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
