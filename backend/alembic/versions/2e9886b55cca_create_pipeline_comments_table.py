"""create pipeline comments table

Revision ID: 2e9886b55cca
Revises: 049fa99a0ad8
Create Date: 2026-03-22 11:16:35.593694

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e9886b55cca'
down_revision: Union[str, Sequence[str], None] = '049fa99a0ad8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pipeline_comments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('pipeline_entry_id', sa.Integer(), sa.ForeignKey('pipeline_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('pipeline_comments')
