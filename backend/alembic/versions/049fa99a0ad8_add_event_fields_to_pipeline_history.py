"""add event fields to pipeline history

Revision ID: 049fa99a0ad8
Revises: bd0cbbd2cbb7
Create Date: 2026-03-22 11:06:09.565149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '049fa99a0ad8'
down_revision: Union[str, Sequence[str], None] = 'bd0cbbd2cbb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pipeline_history',
        sa.Column('event_type', sa.String(), nullable=False, server_default='stage_change'))
    op.add_column('pipeline_history',
        sa.Column('description', sa.Text(), nullable=True))
    op.add_column('pipeline_history',
        sa.Column('event_date', sa.DateTime(), nullable=True))
    # Make to_stage nullable for manual events
    with op.batch_alter_table('pipeline_history') as batch_op:
        batch_op.alter_column('to_stage', existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE pipeline_history SET to_stage = '' WHERE to_stage IS NULL")
    with op.batch_alter_table('pipeline_history') as batch_op:
        batch_op.alter_column('to_stage', existing_type=sa.String(), nullable=False)
    op.drop_column('pipeline_history', 'event_date')
    op.drop_column('pipeline_history', 'description')
    op.drop_column('pipeline_history', 'event_type')
