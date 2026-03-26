"""Tests for pipeline event date columns and PipelineCustomDate model."""

from datetime import date, datetime

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Company, JobPosting, PipelineEntry


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def pipeline_entry(db):
    """Create a pipeline entry for testing."""
    company = Company(name="Test Co")
    db.add(company)
    db.flush()
    posting = JobPosting(title="Engineer", company_id=company.id, source="linkedin")
    db.add(posting)
    db.flush()
    entry = PipelineEntry(job_posting_id=posting.id, stage="applied", position=0)
    db.add(entry)
    db.flush()
    return entry


# --- PipelineEntry date columns ---


def test_pipeline_entries_table_has_applied_date_column(db):
    engine = db.get_bind()
    columns = {c["name"] for c in inspect(engine).get_columns("pipeline_entries")}
    assert "applied_date" in columns


def test_pipeline_entries_table_has_recruiter_screen_date_column(db):
    engine = db.get_bind()
    columns = {c["name"] for c in inspect(engine).get_columns("pipeline_entries")}
    assert "recruiter_screen_date" in columns


def test_pipeline_entries_table_has_tech_screen_date_column(db):
    engine = db.get_bind()
    columns = {c["name"] for c in inspect(engine).get_columns("pipeline_entries")}
    assert "tech_screen_date" in columns


def test_pipeline_entries_table_has_onsite_date_column(db):
    engine = db.get_bind()
    columns = {c["name"] for c in inspect(engine).get_columns("pipeline_entries")}
    assert "onsite_date" in columns


def test_pipeline_entries_table_has_offer_date_column(db):
    engine = db.get_bind()
    columns = {c["name"] for c in inspect(engine).get_columns("pipeline_entries")}
    assert "offer_date" in columns


def test_pipeline_entries_table_has_offer_expiration_date_column(db):
    engine = db.get_bind()
    columns = {c["name"] for c in inspect(engine).get_columns("pipeline_entries")}
    assert "offer_expiration_date" in columns


def test_pipeline_entry_date_columns_are_nullable(pipeline_entry, db):
    """All date columns should default to None."""
    db.refresh(pipeline_entry)
    assert pipeline_entry.applied_date is None
    assert pipeline_entry.recruiter_screen_date is None
    assert pipeline_entry.tech_screen_date is None
    assert pipeline_entry.onsite_date is None
    assert pipeline_entry.offer_date is None
    assert pipeline_entry.offer_expiration_date is None


def test_pipeline_entry_accepts_date_values(db):
    company = Company(name="Date Co")
    db.add(company)
    db.flush()
    posting = JobPosting(title="Engineer", company_id=company.id, source="linkedin")
    db.add(posting)
    db.flush()
    entry = PipelineEntry(
        job_posting_id=posting.id,
        stage="offer",
        position=0,
        applied_date=date(2026, 1, 15),
        recruiter_screen_date=date(2026, 1, 20),
        tech_screen_date=date(2026, 2, 1),
        onsite_date=date(2026, 2, 10),
        offer_date=date(2026, 3, 1),
        offer_expiration_date=date(2026, 3, 15),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    assert entry.applied_date == date(2026, 1, 15)
    assert entry.offer_expiration_date == date(2026, 3, 15)


# --- PipelineCustomDate model ---


def test_pipeline_custom_dates_table_exists(db):
    engine = db.get_bind()
    tables = inspect(engine).get_table_names()
    assert "pipeline_custom_dates" in tables


def test_pipeline_custom_dates_table_has_expected_columns(db):
    engine = db.get_bind()
    columns = {c["name"] for c in inspect(engine).get_columns("pipeline_custom_dates")}
    assert columns >= {"id", "pipeline_entry_id", "label", "date", "created_at"}


def test_create_custom_date(pipeline_entry, db):
    from app.models import PipelineCustomDate

    custom = PipelineCustomDate(
        pipeline_entry_id=pipeline_entry.id,
        label="Follow-up call",
        date=date(2026, 4, 1),
    )
    db.add(custom)
    db.commit()
    db.refresh(custom)
    assert custom.id is not None
    assert custom.label == "Follow-up call"
    assert custom.date == date(2026, 4, 1)
    assert custom.created_at is not None


def test_custom_date_belongs_to_pipeline_entry(pipeline_entry, db):
    from app.models import PipelineCustomDate

    custom = PipelineCustomDate(
        pipeline_entry_id=pipeline_entry.id,
        label="Deadline",
        date=date(2026, 5, 1),
    )
    db.add(custom)
    db.commit()
    db.refresh(custom)
    assert custom.pipeline_entry.id == pipeline_entry.id


def test_pipeline_entry_has_custom_dates_relationship(pipeline_entry, db):
    from app.models import PipelineCustomDate

    c1 = PipelineCustomDate(
        pipeline_entry_id=pipeline_entry.id, label="Date A", date=date(2026, 6, 1)
    )
    c2 = PipelineCustomDate(
        pipeline_entry_id=pipeline_entry.id, label="Date B", date=date(2026, 7, 1)
    )
    db.add_all([c1, c2])
    db.commit()
    db.refresh(pipeline_entry)
    assert len(pipeline_entry.custom_dates) == 2
    labels = {cd.label for cd in pipeline_entry.custom_dates}
    assert labels == {"Date A", "Date B"}


def test_custom_dates_cascade_delete_with_pipeline_entry(db):
    from app.models import PipelineCustomDate

    company = Company(name="Cascade Co")
    db.add(company)
    db.flush()
    posting = JobPosting(title="Engineer", company_id=company.id, source="linkedin")
    db.add(posting)
    db.flush()
    entry = PipelineEntry(job_posting_id=posting.id, stage="applied", position=0)
    db.add(entry)
    db.flush()
    custom = PipelineCustomDate(
        pipeline_entry_id=entry.id, label="Test", date=date(2026, 1, 1)
    )
    db.add(custom)
    db.commit()
    custom_id = custom.id

    db.delete(entry)
    db.commit()
    assert db.get(PipelineCustomDate, custom_id) is None


def test_pipeline_custom_date_exported_from_models():
    """PipelineCustomDate should be importable from app.models."""
    from app.models import PipelineCustomDate

    assert PipelineCustomDate is not None
    assert PipelineCustomDate.__tablename__ == "pipeline_custom_dates"
