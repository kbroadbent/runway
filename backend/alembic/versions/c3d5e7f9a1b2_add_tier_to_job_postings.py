"""add_tier_to_job_postings

Revision ID: c3d5e7f9a1b2
Revises: a3f8b2c91d4e
Create Date: 2026-03-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d5e7f9a1b2'
down_revision: Union[str, Sequence[str], None] = ('b1e2f3a4d5c6', 'b2e4f1d9a7c3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('job_postings', sa.Column('tier', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('job_postings', 'tier')
