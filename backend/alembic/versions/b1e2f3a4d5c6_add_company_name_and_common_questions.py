"""add company_name and common_questions

Revision ID: b1e2f3a4d5c6
Revises: a3f8b2c91d4e
Create Date: 2026-03-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b1e2f3a4d5c6'
down_revision: Union[str, None] = 'a3f8b2c91d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('job_postings', sa.Column('company_name', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('common_questions', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('job_postings', 'company_name')
    op.drop_column('companies', 'common_questions')
