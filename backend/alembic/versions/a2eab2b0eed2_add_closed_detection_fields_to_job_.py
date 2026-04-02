"""add closed detection fields to job_postings

Revision ID: a2eab2b0eed2
Revises: 1a48d929250c
Create Date: 2026-04-01 23:24:29.279887

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2eab2b0eed2'
down_revision: Union[str, Sequence[str], None] = '1a48d929250c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('job_postings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_closed_detected', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('closed_check_dismissed', sa.Boolean(), server_default='0', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('job_postings', schema=None) as batch_op:
        batch_op.drop_column('closed_check_dismissed')
        batch_op.drop_column('is_closed_detected')
