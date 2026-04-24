"""split offer into verbal and written substages

Revision ID: f79da34f7c4e
Revises: 9797022522f8
Create Date: 2026-04-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f79da34f7c4e'
down_revision: Union[str, Sequence[str], None] = '9797022522f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate existing 'offer' stage entries to 'offer_verbal'."""
    op.execute("UPDATE pipeline_entries SET stage = 'offer_verbal' WHERE stage = 'offer'")
    op.execute("UPDATE pipeline_history SET from_stage = 'offer_verbal' WHERE from_stage = 'offer'")
    op.execute("UPDATE pipeline_history SET to_stage = 'offer_verbal' WHERE to_stage = 'offer'")


def downgrade() -> None:
    """Merge offer substages back into 'offer'."""
    op.execute("UPDATE pipeline_entries SET stage = 'offer' WHERE stage IN ('offer_verbal', 'offer_written')")
    op.execute("UPDATE pipeline_history SET from_stage = 'offer' WHERE from_stage IN ('offer_verbal', 'offer_written')")
    op.execute("UPDATE pipeline_history SET to_stage = 'offer' WHERE to_stage IN ('offer_verbal', 'offer_written')")
