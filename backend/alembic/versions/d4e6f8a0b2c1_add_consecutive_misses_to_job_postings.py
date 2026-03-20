"""add consecutive_misses to job_postings

Revision ID: d4e6f8a0b2c1
Revises: c3d5e7f9a1b2
Create Date: 2026-03-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e6f8a0b2c1'
down_revision: Union[str, Sequence[str], None] = 'c3d5e7f9a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('job_postings',
        sa.Column('consecutive_misses', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('job_postings', 'consecutive_misses')
