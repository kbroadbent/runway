"""add rejected_date to pipeline_entries

Revision ID: e1c7761e3577
Revises: a2eab2b0eed2
Create Date: 2026-04-10 21:55:05.354931

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1c7761e3577'
down_revision: Union[str, Sequence[str], None] = 'a2eab2b0eed2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('pipeline_entries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rejected_date', sa.Date(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('pipeline_entries', schema=None) as batch_op:
        batch_op.drop_column('rejected_date')
