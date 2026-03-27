"""add_lead_source_to_job_postings

Revision ID: e1a2b3c4d5f6
Revises: d4e6f8a0b2c1
Create Date: 2026-03-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1a2b3c4d5f6'
down_revision: Union[str, Sequence[str], None] = 'd4e6f8a0b2c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('job_postings') as batch_op:
        batch_op.add_column(sa.Column('lead_source', sa.String(), nullable=False, server_default='cold_apply'))


def downgrade() -> None:
    with op.batch_alter_table('job_postings') as batch_op:
        batch_op.drop_column('lead_source')
