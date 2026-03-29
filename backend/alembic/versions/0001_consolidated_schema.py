"""consolidated schema

Revision ID: 0001
Revises:
Create Date: 2026-03-28

Squashed from 15 incremental migrations into a single baseline.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('website', sa.String(), nullable=True),
        sa.Column('glassdoor_rating', sa.Float(), nullable=True),
        sa.Column('glassdoor_url', sa.String(), nullable=True),
        sa.Column('levels_salary_data', sa.Text(), nullable=True),
        sa.Column('levels_url', sa.String(), nullable=True),
        sa.Column('blind_url', sa.String(), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('last_researched_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('common_questions', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'search_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('search_term', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('remote_filter', sa.String(), nullable=True),
        sa.Column('salary_min', sa.Integer(), nullable=True),
        sa.Column('salary_max', sa.Integer(), nullable=True),
        sa.Column('job_type', sa.String(), nullable=True),
        sa.Column('sources', sa.Text(), nullable=True),
        sa.Column('run_interval', sa.Integer(), nullable=True),
        sa.Column('is_auto_enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('exclude_terms', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'job_postings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('remote_type', sa.String(), nullable=True),
        sa.Column('salary_min', sa.Integer(), nullable=True),
        sa.Column('salary_max', sa.Integer(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('date_posted', sa.DateTime(), nullable=True),
        sa.Column('date_saved', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('status', sa.String(), server_default='saved', nullable=False),
        sa.Column('raw_content', sa.Text(), nullable=True),
        sa.Column('tier', sa.Integer(), nullable=True),
        sa.Column('consecutive_misses', sa.Integer(), server_default='0', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('lead_source', sa.String(), server_default='cold_apply', nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('title', 'company_id', name='uq_job_postings_title_company'),
        sa.UniqueConstraint('url', name='uq_job_postings_url'),
    )
    op.create_table(
        'pipeline_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_posting_id', sa.Integer(), nullable=False),
        sa.Column('stage', sa.String(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('next_action', sa.String(), nullable=True),
        sa.Column('next_action_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('applied_date', sa.DateTime(), nullable=True),
        sa.Column('recruiter_screen_date', sa.DateTime(), nullable=True),
        sa.Column('tech_screen_date', sa.DateTime(), nullable=True),
        sa.Column('onsite_date', sa.DateTime(), nullable=True),
        sa.Column('offer_date', sa.DateTime(), nullable=True),
        sa.Column('offer_expiration_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['job_posting_id'], ['job_postings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_posting_id'),
    )
    op.create_table(
        'search_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('search_profile_id', sa.Integer(), nullable=False),
        sa.Column('job_posting_id', sa.Integer(), nullable=False),
        sa.Column('run_date', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('is_new', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['job_posting_id'], ['job_postings.id']),
        sa.ForeignKeyConstraint(['search_profile_id'], ['search_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('search_profile_id', 'job_posting_id', name='uq_search_result_profile_posting'),
    )
    op.create_table(
        'interview_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pipeline_entry_id', sa.Integer(), nullable=False),
        sa.Column('round', sa.String(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('interviewers', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('outcome', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['pipeline_entry_id'], ['pipeline_entries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'pipeline_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pipeline_entry_id', sa.Integer(), nullable=False),
        sa.Column('from_stage', sa.String(), nullable=True),
        sa.Column('to_stage', sa.String(), nullable=True),
        sa.Column('note', sa.String(), nullable=True),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('event_type', sa.String(), server_default='stage_change', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pipeline_entry_id'], ['pipeline_entries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'pipeline_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pipeline_entry_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['pipeline_entry_id'], ['pipeline_entries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'pipeline_custom_dates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pipeline_entry_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['pipeline_entry_id'], ['pipeline_entries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('pipeline_custom_dates')
    op.drop_table('pipeline_comments')
    op.drop_table('pipeline_history')
    op.drop_table('interview_notes')
    op.drop_table('search_results')
    op.drop_table('pipeline_entries')
    op.drop_table('job_postings')
    op.drop_table('search_profiles')
    op.drop_table('companies')
