"""add_notes_to_job_postings

Revision ID: b89f7a3cc2f4
Revises: 2e9886b55cca
Create Date: 2026-03-23 19:59:55.618335

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b89f7a3cc2f4'
down_revision: Union[str, Sequence[str], None] = '2e9886b55cca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('job_postings', sa.Column('notes', sa.Text(), nullable=True))
    op.execute("""
        UPDATE job_postings
        SET notes = (
            SELECT pe.notes FROM pipeline_entries pe
            WHERE pe.job_posting_id = job_postings.id
              AND pe.notes IS NOT NULL
              AND pe.notes != ''
        )
        WHERE EXISTS (
            SELECT 1 FROM pipeline_entries pe
            WHERE pe.job_posting_id = job_postings.id
              AND pe.notes IS NOT NULL
              AND pe.notes != ''
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('job_postings', 'notes')
