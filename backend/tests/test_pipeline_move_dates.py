"""Tests for move handler persisting stage dates."""

import pytest
from app.models import Company, JobPosting, PipelineEntry, PipelineHistory  # noqa: F401


@pytest.fixture
def posting_id(client):
    resp = client.post("/api/postings", json={"title": "Eng", "company_name": "Acme", "source": "manual"})
    return resp.json()["id"]


def _get_entry_id(client, posting_id):
    data = client.get("/api/pipeline").json()
    for entries in data.values():
        for e in entries:
            if e["job_posting"]["id"] == posting_id:
                return e["id"]
    raise AssertionError(f"No pipeline entry found for posting {posting_id}")


# --- Move without dates ---


def test_move_without_dates_leaves_date_fields_null(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applied"})
    assert resp.status_code == 200
    assert resp.json()["applied_date"] is None


def test_move_without_dates_still_changes_stage(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applied"})
    assert resp.status_code == 200
    assert resp.json()["stage"] == "applied"


# --- Move with stage_dates ---


def test_move_with_stage_dates_persists_applied_date(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "applied",
        "stage_dates": {"applied_date": "2026-03-20"},
    })
    assert resp.status_code == 200
    assert resp.json()["applied_date"] == "2026-03-20"


def test_move_with_stage_dates_persists_verbal_offer_date(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "offer_verbal",
        "stage_dates": {
            "offer_date": "2026-04-01",
        },
    })
    assert resp.status_code == 200
    assert resp.json()["offer_date"] == "2026-04-01"


def test_move_with_stage_dates_persists_written_offer_expiration(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "offer_written",
        "stage_dates": {
            "offer_expiration_date": "2026-04-15",
        },
    })
    assert resp.status_code == 200
    assert resp.json()["offer_expiration_date"] == "2026-04-15"


def test_move_with_stage_dates_persists_recruiter_screen_date(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "recruiter_screen_scheduled",
        "stage_dates": {"recruiter_screen_date": "2026-03-25"},
    })
    assert resp.status_code == 200
    assert resp.json()["recruiter_screen_date"] == "2026-03-25"


def test_move_with_stage_dates_ignores_invalid_field_names(client, posting_id):
    """Invalid field names in stage_dates should be silently ignored."""
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "applied",
        "stage_dates": {
            "applied_date": "2026-03-20",
            "bogus_field": "2026-01-01",
        },
    })
    assert resp.status_code == 200
    assert resp.json()["applied_date"] == "2026-03-20"


def test_move_with_empty_stage_dates_dict(client, posting_id):
    """Empty stage_dates dict should work the same as no dates."""
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "applied",
        "stage_dates": {},
    })
    assert resp.status_code == 200
    assert resp.json()["stage"] == "applied"
    assert resp.json()["applied_date"] is None


def test_move_with_null_date_value_in_stage_dates(client, posting_id):
    """A null value in stage_dates should set the field to null."""
    eid = _get_entry_id(client, posting_id)
    # First set a date
    client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "applied",
        "stage_dates": {"applied_date": "2026-03-20"},
    })
    # Then clear it
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "applying",
        "stage_dates": {"applied_date": None},
    })
    assert resp.status_code == 200
    assert resp.json()["applied_date"] is None


# --- Response includes date fields ---


def test_move_response_includes_all_date_fields(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applied"})
    body = resp.json()
    for field in ["applied_date", "recruiter_screen_date", "tech_screen_date",
                   "onsite_date", "offer_date", "offer_expiration_date"]:
        assert field in body, f"Missing date field: {field}"


def test_list_pipeline_response_includes_date_fields(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "applied",
        "stage_dates": {"applied_date": "2026-03-20"},
    })
    resp = client.get("/api/pipeline")
    entries = resp.json()["applied"]
    assert len(entries) == 1
    assert entries[0]["applied_date"] == "2026-03-20"
