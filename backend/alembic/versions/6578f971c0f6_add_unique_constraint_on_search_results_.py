"""add unique constraint on search_results(search_profile_id, job_posting_id)

Revision ID: 6578f971c0f6
Revises: 92cc6b5d5ecf
Create Date: 2026-03-25 18:37:39.996452

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6578f971c0f6'
down_revision: Union[str, Sequence[str], None] = '92cc6b5d5ecf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove duplicate SearchResult rows before adding the unique constraint.
    # Keep the row with the latest run_date for each (search_profile_id, job_posting_id) pair.
    op.execute(
        """
        DELETE FROM search_results
        WHERE id NOT IN (
            SELECT MAX(id) FROM search_results
            GROUP BY search_profile_id, job_posting_id
        )
        """
    )
    with op.batch_alter_table('search_results') as batch_op:
        batch_op.create_unique_constraint('uq_search_result_profile_posting', ['search_profile_id', 'job_posting_id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('search_results') as batch_op:
        batch_op.drop_constraint('uq_search_result_profile_posting', type_='unique')
