"""repair corrupted scheduled_at values from earlier migration

Revision ID: b3c5d7e2a1f4
Revises: f79da34f7c4e
Create Date: 2026-04-27 00:00:00.000000

Migration 9797022522f8 altered interview_notes.scheduled_at from DateTime
to Date. SQLite's NUMERIC type affinity on the new column coerced existing
datetime strings (e.g. '2026-03-24 11:00:00.000000') into the integer 2026
(numeric prefix), permanently corrupting the dates for rows present at the
time of that migration.

This migration restores the known dates by id. Values were recovered from
a database backup (rows 2/3/4) and from calendar invites in email
(rows 7/8/9/10/15). It only updates rows whose current value is exactly
2026 (the corruption sentinel), so re-running on a clean database is a
no-op.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b3c5d7e2a1f4'
down_revision: Union[str, Sequence[str], None] = 'f79da34f7c4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


REPAIRS = [
    (2, '2026-03-24'),
    (3, '2026-03-24'),
    (4, '2026-03-25'),
    (7, '2026-04-09'),
    (8, '2026-04-09'),
    (9, '2026-04-10'),
    (10, '2026-04-13'),
    (15, '2026-04-14'),
]


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    for note_id, iso_date in REPAIRS:
        conn.exec_driver_sql(
            "UPDATE interview_notes SET scheduled_at = ? "
            "WHERE id = ? AND CAST(scheduled_at AS TEXT) = '2026'",
            (iso_date, note_id),
        )


def downgrade() -> None:
    """Downgrade schema."""
    # The corruption is not reversible — leave repaired values in place.
    pass
