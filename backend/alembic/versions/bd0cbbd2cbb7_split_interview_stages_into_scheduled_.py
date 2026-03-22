"""split interview stages into scheduled and completed

Revision ID: bd0cbbd2cbb7
Revises: d4e6f8a0b2c1
Create Date: 2026-03-22 11:03:34.982359

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd0cbbd2cbb7'
down_revision: Union[str, Sequence[str], None] = 'd4e6f8a0b2c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


STAGE_MAP = {
    "recruiter_screen": "recruiter_screen_scheduled",
    "tech_screen": "tech_screen_scheduled",
    "onsite": "onsite_scheduled",
}

REVERSE_MAP = {v: k for k, v in STAGE_MAP.items()}


def upgrade() -> None:
    for old, new in STAGE_MAP.items():
        op.execute(f"UPDATE pipeline_entries SET stage = '{new}' WHERE stage = '{old}'")
        op.execute(f"UPDATE pipeline_history SET from_stage = '{new}' WHERE from_stage = '{old}'")
        op.execute(f"UPDATE pipeline_history SET to_stage = '{new}' WHERE to_stage = '{old}'")


def downgrade() -> None:
    for new, old in REVERSE_MAP.items():
        op.execute(f"UPDATE pipeline_entries SET stage = '{old}' WHERE stage = '{new}'")
        op.execute(f"UPDATE pipeline_history SET from_stage = '{old}' WHERE from_stage = '{new}'")
        op.execute(f"UPDATE pipeline_history SET to_stage = '{old}' WHERE to_stage = '{new}'")
    # Also collapse _completed back to the base stage name
    for base in ["recruiter_screen", "tech_screen", "onsite"]:
        completed = f"{base}_completed"
        op.execute(f"UPDATE pipeline_entries SET stage = '{base}' WHERE stage = '{completed}'")
        op.execute(f"UPDATE pipeline_history SET from_stage = '{base}' WHERE from_stage = '{completed}'")
        op.execute(f"UPDATE pipeline_history SET to_stage = '{base}' WHERE to_stage = '{completed}'")
