"""remove outcome and convert scheduled_at to date on interview_notes

Revision ID: 9797022522f8
Revises: 0618239c57ef
Create Date: 2026-04-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9797022522f8'
down_revision: Union[str, Sequence[str], None] = '0618239c57ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Truncate datetime strings to date-only ISO format BEFORE altering the
    # column type. SQLite's NUMERIC affinity on the new Date column would
    # otherwise coerce a value like '2026-03-24 11:00:00' into the integer
    # 2026 (numeric prefix), permanently destroying the date.
    op.execute(
        "UPDATE interview_notes "
        "SET scheduled_at = substr(scheduled_at, 1, 10) "
        "WHERE scheduled_at IS NOT NULL"
    )
    with op.batch_alter_table('interview_notes', schema=None) as batch_op:
        batch_op.drop_column('outcome')
        batch_op.alter_column('scheduled_at',
                              existing_type=sa.DateTime(),
                              type_=sa.Date(),
                              existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('interview_notes', schema=None) as batch_op:
        batch_op.alter_column('scheduled_at',
                              existing_type=sa.Date(),
                              type_=sa.DateTime(),
                              existing_nullable=True)
        batch_op.add_column(sa.Column('outcome', sa.String(), nullable=True))
