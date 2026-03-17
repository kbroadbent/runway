"""add_status_to_job_postings

Revision ID: a3f8b2c91d4e
Revises: 7c9c3a07f2c5
Create Date: 2026-03-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f8b2c91d4e'
down_revision: Union[str, Sequence[str], None] = '7c9c3a07f2c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('job_postings', sa.Column('status', sa.String(), nullable=False, server_default='saved'))
    op.drop_column('job_postings', 'is_active')


def downgrade() -> None:
    op.add_column('job_postings', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    op.drop_column('job_postings', 'status')
