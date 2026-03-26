"""add date fields to pipeline_entries

Revision ID: 58b62f5263bc
Revises: b89f7a3cc2f4
Create Date: 2026-03-25 18:29:24.844141

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58b62f5263bc'
down_revision: Union[str, Sequence[str], None] = 'b89f7a3cc2f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('pipeline_entries', sa.Column('applied_date', sa.DateTime(), nullable=True))
    op.add_column('pipeline_entries', sa.Column('recruiter_screen_date', sa.DateTime(), nullable=True))
    op.add_column('pipeline_entries', sa.Column('tech_screen_date', sa.DateTime(), nullable=True))
    op.add_column('pipeline_entries', sa.Column('onsite_date', sa.DateTime(), nullable=True))
    op.add_column('pipeline_entries', sa.Column('offer_date', sa.DateTime(), nullable=True))
    op.add_column('pipeline_entries', sa.Column('offer_expiration_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('pipeline_entries', 'offer_expiration_date')
    op.drop_column('pipeline_entries', 'offer_date')
    op.drop_column('pipeline_entries', 'onsite_date')
    op.drop_column('pipeline_entries', 'tech_screen_date')
    op.drop_column('pipeline_entries', 'recruiter_screen_date')
    op.drop_column('pipeline_entries', 'applied_date')
