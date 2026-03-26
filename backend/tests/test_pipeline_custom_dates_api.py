"""Tests for custom date CRUD endpoints on pipeline entries."""

import pytest
from app.models import Company, JobPosting, PipelineEntry  # noqa: F401


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


# --- POST create custom date ---


def test_create_custom_date(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.post(f"/api/pipeline/{eid}/dates", json={
        "label": "Follow-up call",
        "date": "2026-04-01",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["label"] == "Follow-up call"
    assert body["date"] == "2026-04-01"
    assert "id" in body
    assert "created_at" in body


def test_create_custom_date_returns_404_for_nonexistent_entry(client):
    resp = client.post("/api/pipeline/99999/dates", json={
        "label": "Test",
        "date": "2026-04-01",
    })
    assert resp.status_code == 404


def test_create_custom_date_rejects_empty_label(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.post(f"/api/pipeline/{eid}/dates", json={
        "label": "",
        "date": "2026-04-01",
    })
    assert resp.status_code == 422


def test_create_custom_date_rejects_label_over_100_chars(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.post(f"/api/pipeline/{eid}/dates", json={
        "label": "x" * 101,
        "date": "2026-04-01",
    })
    assert resp.status_code == 422


# --- GET list custom dates ---


def test_list_custom_dates_returns_empty_initially(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.get(f"/api/pipeline/{eid}/dates")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_custom_dates_returns_created_dates(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    client.post(f"/api/pipeline/{eid}/dates", json={"label": "Date A", "date": "2026-05-01"})
    client.post(f"/api/pipeline/{eid}/dates", json={"label": "Date B", "date": "2026-06-01"})
    resp = client.get(f"/api/pipeline/{eid}/dates")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_custom_dates_ordered_by_date_ascending(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    client.post(f"/api/pipeline/{eid}/dates", json={"label": "Later", "date": "2026-08-01"})
    client.post(f"/api/pipeline/{eid}/dates", json={"label": "Earlier", "date": "2026-03-01"})
    client.post(f"/api/pipeline/{eid}/dates", json={"label": "Middle", "date": "2026-05-15"})
    resp = client.get(f"/api/pipeline/{eid}/dates")
    assert resp.status_code == 200
    dates = resp.json()
    assert dates[0]["label"] == "Earlier"
    assert dates[1]["label"] == "Middle"
    assert dates[2]["label"] == "Later"


# --- PUT update custom date ---


def test_update_custom_date_label(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/dates", json={"label": "Old", "date": "2026-04-01"})
    did = create_resp.json()["id"]
    resp = client.put(f"/api/pipeline/{eid}/dates/{did}", json={"label": "New"})
    assert resp.status_code == 200
    assert resp.json()["label"] == "New"
    assert resp.json()["date"] == "2026-04-01"  # date unchanged


def test_update_custom_date_date(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/dates", json={"label": "Test", "date": "2026-04-01"})
    did = create_resp.json()["id"]
    resp = client.put(f"/api/pipeline/{eid}/dates/{did}", json={"date": "2026-05-01"})
    assert resp.status_code == 200
    assert resp.json()["date"] == "2026-05-01"
    assert resp.json()["label"] == "Test"  # label unchanged


def test_update_custom_date_returns_404_for_nonexistent_date(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/dates/99999", json={"label": "New"})
    assert resp.status_code == 404


def test_update_custom_date_rejects_empty_label(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/dates", json={"label": "Test", "date": "2026-04-01"})
    did = create_resp.json()["id"]
    resp = client.put(f"/api/pipeline/{eid}/dates/{did}", json={"label": ""})
    assert resp.status_code == 422


# --- DELETE custom date ---


def test_delete_custom_date(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/dates", json={"label": "Test", "date": "2026-04-01"})
    did = create_resp.json()["id"]
    resp = client.delete(f"/api/pipeline/{eid}/dates/{did}")
    assert resp.status_code == 204
    # Verify it's gone
    list_resp = client.get(f"/api/pipeline/{eid}/dates")
    assert len(list_resp.json()) == 0


def test_delete_custom_date_returns_404_for_nonexistent_date(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.delete(f"/api/pipeline/{eid}/dates/99999")
    assert resp.status_code == 404


# --- Custom dates in pipeline entry response ---


def test_pipeline_entry_response_includes_custom_dates(client, posting_id):
    """custom_dates field should appear in pipeline list responses."""
    eid = _get_entry_id(client, posting_id)
    client.post(f"/api/pipeline/{eid}/dates", json={"label": "Deadline", "date": "2026-04-15"})
    resp = client.get("/api/pipeline")
    entries = [e for es in resp.json().values() for e in es]
    entry = next(e for e in entries if e["id"] == eid)
    assert "custom_dates" in entry
    assert len(entry["custom_dates"]) == 1
    assert entry["custom_dates"][0]["label"] == "Deadline"
