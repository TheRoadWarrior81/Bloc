"""baseline

Revision ID: 591170e3861c
Revises: 
Create Date: 2026-04-02 17:28:45.442682

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '591170e3861c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_table('circles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('invite_code', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invite_code')
    )
    op.create_table('user_circles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('circle_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), server_default='member'),
        sa.Column('joined_at', sa.TIMESTAMP(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['circle_id'], ['circles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'circle_id')
    )
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('circle_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['circle_id'], ['circles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('messages')
    op.drop_table('user_circles')
    op.drop_table('circles')
    op.drop_table('users')


