"""backfill_companies_from_company_name

Revision ID: b2e4f1d9a7c3
Revises: a3f8b2c91d4e
Create Date: 2026-03-17

Reads the legacy company_name text column from job_postings (if it exists),
creates Company records for each unique name, and links postings via company_id.
Also drops the company_name column if present.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = 'b2e4f1d9a7c3'
down_revision: Union[str, Sequence[str], None] = 'a3f8b2c91d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(conn, table: str, column: str) -> bool:
    result = conn.execute(text(f"PRAGMA table_info({table})"))
    return any(row[1] == column for row in result)


def upgrade() -> None:
    conn = op.get_bind()

    if not _has_column(conn, 'job_postings', 'company_name'):
        return

    # Get all postings with a company_name but no company_id
    rows = conn.execute(text(
        "SELECT id, company_name FROM job_postings "
        "WHERE company_name IS NOT NULL AND company_name != '' AND company_id IS NULL"
    )).fetchall()

    # Build unique name → company_id mapping
    name_to_id: dict[str, int] = {}
    for posting_id, company_name in rows:
        if company_name in name_to_id:
            continue
        existing = conn.execute(
            text("SELECT id FROM companies WHERE name = :name"),
            {"name": company_name}
        ).fetchone()
        if existing:
            name_to_id[company_name] = existing[0]
        else:
            result = conn.execute(
                text("INSERT INTO companies (name) VALUES (:name)"),
                {"name": company_name}
            )
            name_to_id[company_name] = result.lastrowid

    # Link postings to their companies
    for posting_id, company_name in rows:
        if company_name in name_to_id:
            conn.execute(
                text("UPDATE job_postings SET company_id = :cid WHERE id = :pid"),
                {"cid": name_to_id[company_name], "pid": posting_id}
            )

    # Drop the now-redundant column
    with op.batch_alter_table('job_postings') as batch_op:
        batch_op.drop_column('company_name')


def downgrade() -> None:
    with op.batch_alter_table('job_postings') as batch_op:
        batch_op.add_column(sa.Column('company_name', sa.String(), nullable=True))
