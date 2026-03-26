"""Tests for moving pipeline entries with stage_dates."""

import pytest
from app.models import Company, JobPosting, PipelineEntry, PipelineHistory, InterviewNote  # noqa: F401


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


def test_move_with_stage_dates_sets_date_on_entry(client, posting_id):
    """Moving to 'applied' with stage_dates should set applied_date on the entry."""
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "applied",
        "stage_dates": {"applied_date": "2026-03-20"},
    })
    assert resp.status_code == 200
    assert resp.json()["stage"] == "applied"
    assert resp.json()["applied_date"] == "2026-03-20"


def test_move_with_multiple_stage_dates(client, posting_id):
    """Moving to 'offer' with multiple stage_dates should set all provided dates."""
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "offer",
        "stage_dates": {
            "offer_date": "2026-04-01",
            "offer_expiration_date": "2026-04-15",
        },
    })
    assert resp.status_code == 200
    assert resp.json()["offer_date"] == "2026-04-01"
    assert resp.json()["offer_expiration_date"] == "2026-04-15"


def test_move_without_stage_dates_preserves_existing_dates(client, posting_id):
    """Moving without stage_dates should not clear previously set dates."""
    eid = _get_entry_id(client, posting_id)
    # First move to applied with a date
    client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "applied",
        "stage_dates": {"applied_date": "2026-03-20"},
    })
    # Then move to recruiter_screen_scheduled without stage_dates
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "recruiter_screen_scheduled",
    })
    assert resp.status_code == 200
    assert resp.json()["applied_date"] == "2026-03-20"


def test_move_without_stage_dates_does_not_auto_set_dates(client, posting_id):
    """Moving without stage_dates should leave date fields as null."""
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "applied",
    })
    assert resp.status_code == 200
    assert resp.json()["applied_date"] is None


def test_move_stage_dates_with_none_clears_date(client, posting_id):
    """Passing None in stage_dates should clear a previously set date."""
    eid = _get_entry_id(client, posting_id)
    # Set the date
    client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "applied",
        "stage_dates": {"applied_date": "2026-03-20"},
    })
    # Move again with None to clear it
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "recruiter_screen_scheduled",
        "stage_dates": {"applied_date": None},
    })
    assert resp.status_code == 200
    assert resp.json()["applied_date"] is None


def test_update_entry_with_stage_date_field(client, posting_id):
    """PUT /api/pipeline/{id} should accept and persist stage date fields."""
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}", json={
        "applied_date": "2026-03-20",
    })
    assert resp.status_code == 200
    assert resp.json()["applied_date"] == "2026-03-20"


def test_pipeline_entry_read_includes_all_date_fields(client, posting_id):
    """Pipeline list response should include all stage date fields."""
    data = client.get("/api/pipeline").json()
    entry = None
    for entries in data.values():
        for e in entries:
            if e["job_posting"]["id"] == posting_id:
                entry = e
                break
    assert entry is not None
    for field in ["applied_date", "recruiter_screen_date", "tech_screen_date",
                  "onsite_date", "offer_date", "offer_expiration_date"]:
        assert field in entry, f"{field} missing from pipeline entry response"
