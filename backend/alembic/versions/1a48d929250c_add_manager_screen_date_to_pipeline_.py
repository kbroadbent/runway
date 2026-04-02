"""add manager_screen_date to pipeline_entries

Revision ID: 1a48d929250c
Revises: 0001
Create Date: 2026-04-01 12:04:17.548169

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a48d929250c'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('pipeline_entries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('manager_screen_date', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('pipeline_entries', schema=None) as batch_op:
        batch_op.drop_column('manager_screen_date')
