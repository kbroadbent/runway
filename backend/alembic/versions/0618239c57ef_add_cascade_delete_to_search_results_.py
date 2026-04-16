"""add cascade delete to search_results.job_posting_id FK

Revision ID: 0618239c57ef
Revises: e1c7761e3577
Create Date: 2026-04-14 10:24:09.149239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0618239c57ef'
down_revision: Union[str, Sequence[str], None] = 'e1c7761e3577'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    naming_convention = {
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
    with op.batch_alter_table('search_results', schema=None, naming_convention=naming_convention) as batch_op:
        batch_op.drop_constraint('fk_search_results_job_posting_id_job_postings', type_='foreignkey')
        batch_op.create_foreign_key('fk_search_results_job_posting_id_job_postings', 'job_postings', ['job_posting_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('search_results', schema=None) as batch_op:
        batch_op.drop_constraint('fk_search_results_job_posting_id_job_postings', type_='foreignkey')
        batch_op.create_foreign_key('fk_search_results_job_posting_id_job_postings', 'job_postings', ['job_posting_id'], ['id'])
