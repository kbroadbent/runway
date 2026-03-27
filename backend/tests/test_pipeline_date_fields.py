"""Tests for pipeline entry date fields.

PipelineEntry should have nullable date columns for each field defined in
STAGE_DATE_FIELDS: applied_date, recruiter_screen_date, tech_screen_date,
onsite_date, offer_date, offer_expiration_date. These fields should be
exposed in the read schema, updatable via the update schema, and
round-trip through the API.
"""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Company, JobPosting, PipelineEntry
from app.constants import STAGE_DATE_FIELDS


# ---------------------------------------------------------------------------
# Collect all date field names from STAGE_DATE_FIELDS
# ---------------------------------------------------------------------------
ALL_DATE_FIELD_NAMES = [
    field_name
    for fields in STAGE_DATE_FIELDS.values()
    for field_name, _ in fields
]


# ---------------------------------------------------------------------------
# Model-level tests
# ---------------------------------------------------------------------------


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
    company = Company(name="Test Co")
    db.add(company)
    db.flush()
    posting = JobPosting(title="Engineer", company_id=company.id, source="manual")
    db.add(posting)
    db.flush()
    entry = PipelineEntry(job_posting_id=posting.id, stage="interested", position=0)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@pytest.mark.parametrize("field_name", ALL_DATE_FIELD_NAMES)
def test_pipeline_entry_has_date_column(field_name):
    """PipelineEntry model should have a column for each STAGE_DATE_FIELDS entry."""
    assert hasattr(PipelineEntry, field_name), (
        f"PipelineEntry is missing column '{field_name}'"
    )


@pytest.mark.parametrize("field_name", ALL_DATE_FIELD_NAMES)
def test_date_column_exists_in_table(db, field_name):
    """The pipeline_entries table should have each date column."""
    engine = db.get_bind()
    columns = {c["name"] for c in inspect(engine).get_columns("pipeline_entries")}
    assert field_name in columns, (
        f"Column '{field_name}' missing from pipeline_entries table"
    )


@pytest.mark.parametrize("field_name", ALL_DATE_FIELD_NAMES)
def test_date_columns_default_to_none(pipeline_entry, field_name):
    """Date fields should be nullable and default to None."""
    assert getattr(pipeline_entry, field_name) is None


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_pipeline_entry_read_schema_includes_date_fields():
    """PipelineEntryRead should declare all date fields."""
    from app.schemas.pipeline import PipelineEntryRead

    schema_fields = set(PipelineEntryRead.model_fields.keys())
    for field_name in ALL_DATE_FIELD_NAMES:
        assert field_name in schema_fields, (
            f"PipelineEntryRead is missing field '{field_name}'"
        )


def test_pipeline_entry_update_schema_includes_date_fields():
    """PipelineEntryUpdate should accept all date fields."""
    from app.schemas.pipeline import PipelineEntryUpdate

    schema_fields = set(PipelineEntryUpdate.model_fields.keys())
    for field_name in ALL_DATE_FIELD_NAMES:
        assert field_name in schema_fields, (
            f"PipelineEntryUpdate is missing field '{field_name}'"
        )


def test_pipeline_entry_update_date_fields_are_optional():
    """Date fields in PipelineEntryUpdate should be optional (default None)."""
    from app.schemas.pipeline import PipelineEntryUpdate

    instance = PipelineEntryUpdate()
    for field_name in ALL_DATE_FIELD_NAMES:
        assert getattr(instance, field_name) is None, (
            f"PipelineEntryUpdate.{field_name} should default to None"
        )


# ---------------------------------------------------------------------------
# API round-trip tests
# ---------------------------------------------------------------------------


@pytest.fixture
def posting_id(client):
    resp = client.post("/api/postings", json={
        "title": "Eng", "company_name": "Acme", "source": "manual",
    })
    return resp.json()["id"]


def _get_entry_id(client, posting_id):
    data = client.get("/api/pipeline").json()
    for entries in data.values():
        for e in entries:
            if e["job_posting"]["id"] == posting_id:
                return e["id"]
    raise AssertionError(f"No pipeline entry for posting {posting_id}")


def test_api_pipeline_entry_returns_date_fields(client, posting_id):
    """GET /api/pipeline should include date fields in each entry."""
    data = client.get("/api/pipeline").json()
    entry = next(
        e for es in data.values() for e in es
        if e["job_posting"]["id"] == posting_id
    )
    for field_name in ALL_DATE_FIELD_NAMES:
        assert field_name in entry, (
            f"Pipeline entry response missing '{field_name}'"
        )
        assert entry[field_name] is None


def test_api_update_applied_date(client, posting_id):
    """PUT /api/pipeline/{id} should accept and persist applied_date."""
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}", json={
        "applied_date": "2026-03-25T12:00:00",
    })
    assert resp.status_code == 200
    assert resp.json()["applied_date"] is not None


def test_api_update_offer_dates(client, posting_id):
    """PUT /api/pipeline/{id} should accept offer_date and offer_expiration_date."""
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}", json={
        "offer_date": "2026-04-01T09:00:00",
        "offer_expiration_date": "2026-04-15T17:00:00",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["offer_date"] is not None
    assert body["offer_expiration_date"] is not None


def test_api_clear_date_field(client, posting_id):
    """Setting a date field to null should clear it."""
    eid = _get_entry_id(client, posting_id)
    # Set it first
    client.put(f"/api/pipeline/{eid}", json={
        "applied_date": "2026-03-25T12:00:00",
    })
    # Clear it
    resp = client.put(f"/api/pipeline/{eid}", json={
        "applied_date": None,
    })
    assert resp.status_code == 200
    assert resp.json()["applied_date"] is None
