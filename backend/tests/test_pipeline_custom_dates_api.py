"""Tests for custom date CRUD API endpoints on pipeline entries."""

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


# --- Create custom date ---


def test_create_custom_date(client, posting_id):
    """POST /api/pipeline/{entry_id}/custom-dates should create a custom date."""
    eid = _get_entry_id(client, posting_id)
    resp = client.post(f"/api/pipeline/{eid}/custom-dates", json={
        "label": "Follow-up call",
        "date": "2026-04-01",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["label"] == "Follow-up call"
    assert body["date"] == "2026-04-01"
    assert "id" in body
    assert "created_at" in body


def test_create_custom_date_returns_404_for_missing_entry(client):
    """POST to nonexistent entry should return 404."""
    resp = client.post("/api/pipeline/99999/custom-dates", json={
        "label": "Test",
        "date": "2026-04-01",
    })
    assert resp.status_code == 404


def test_create_custom_date_rejects_empty_label(client, posting_id):
    """POST with empty label should return 422."""
    eid = _get_entry_id(client, posting_id)
    resp = client.post(f"/api/pipeline/{eid}/custom-dates", json={
        "label": "",
        "date": "2026-04-01",
    })
    assert resp.status_code == 422


def test_create_custom_date_rejects_missing_date(client, posting_id):
    """POST without date should return 422."""
    eid = _get_entry_id(client, posting_id)
    resp = client.post(f"/api/pipeline/{eid}/custom-dates", json={
        "label": "Test",
    })
    assert resp.status_code == 422


def test_create_custom_date_rejects_label_over_100_chars(client, posting_id):
    """POST with label >100 chars should return 422."""
    eid = _get_entry_id(client, posting_id)
    resp = client.post(f"/api/pipeline/{eid}/custom-dates", json={
        "label": "x" * 101,
        "date": "2026-04-01",
    })
    assert resp.status_code == 422


# --- List custom dates ---


def test_list_custom_dates(client, posting_id):
    """GET /api/pipeline/{entry_id}/custom-dates should list all custom dates."""
    eid = _get_entry_id(client, posting_id)
    client.post(f"/api/pipeline/{eid}/custom-dates", json={"label": "Date A", "date": "2026-04-01"})
    client.post(f"/api/pipeline/{eid}/custom-dates", json={"label": "Date B", "date": "2026-05-01"})
    resp = client.get(f"/api/pipeline/{eid}/custom-dates")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    labels = {d["label"] for d in resp.json()}
    assert labels == {"Date A", "Date B"}


def test_list_custom_dates_returns_empty_list_when_none(client, posting_id):
    """GET with no custom dates should return empty list."""
    eid = _get_entry_id(client, posting_id)
    resp = client.get(f"/api/pipeline/{eid}/custom-dates")
    assert resp.status_code == 200
    assert resp.json() == []


# --- Update custom date ---


def test_update_custom_date_label(client, posting_id):
    """PUT /api/pipeline/custom-dates/{id} should update the label."""
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/custom-dates", json={
        "label": "Old label",
        "date": "2026-04-01",
    })
    cd_id = create_resp.json()["id"]
    resp = client.put(f"/api/pipeline-custom-dates/{cd_id}", json={"label": "New label"})
    assert resp.status_code == 200
    assert resp.json()["label"] == "New label"
    assert resp.json()["date"] == "2026-04-01"  # date unchanged


def test_update_custom_date_date(client, posting_id):
    """PUT should update the date."""
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/custom-dates", json={
        "label": "Deadline",
        "date": "2026-04-01",
    })
    cd_id = create_resp.json()["id"]
    resp = client.put(f"/api/pipeline-custom-dates/{cd_id}", json={"date": "2026-05-15"})
    assert resp.status_code == 200
    assert resp.json()["date"] == "2026-05-15"
    assert resp.json()["label"] == "Deadline"  # label unchanged


def test_update_custom_date_both_fields(client, posting_id):
    """PUT should update both label and date."""
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/custom-dates", json={
        "label": "Old",
        "date": "2026-04-01",
    })
    cd_id = create_resp.json()["id"]
    resp = client.put(f"/api/pipeline-custom-dates/{cd_id}", json={
        "label": "New",
        "date": "2026-06-01",
    })
    assert resp.status_code == 200
    assert resp.json()["label"] == "New"
    assert resp.json()["date"] == "2026-06-01"


def test_update_custom_date_returns_404_for_missing(client):
    """PUT to nonexistent custom date should return 404."""
    resp = client.put("/api/pipeline-custom-dates/99999", json={"label": "Test"})
    assert resp.status_code == 404


def test_update_custom_date_rejects_empty_label(client, posting_id):
    """PUT with empty label should return 422."""
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/custom-dates", json={
        "label": "Valid",
        "date": "2026-04-01",
    })
    cd_id = create_resp.json()["id"]
    resp = client.put(f"/api/pipeline-custom-dates/{cd_id}", json={"label": ""})
    assert resp.status_code == 422


# --- Delete custom date ---


def test_delete_custom_date(client, posting_id):
    """DELETE /api/pipeline-custom-dates/{id} should remove the custom date."""
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/custom-dates", json={
        "label": "To delete",
        "date": "2026-04-01",
    })
    cd_id = create_resp.json()["id"]
    resp = client.delete(f"/api/pipeline-custom-dates/{cd_id}")
    assert resp.status_code == 204
    # Verify it's gone
    list_resp = client.get(f"/api/pipeline/{eid}/custom-dates")
    assert len(list_resp.json()) == 0


def test_delete_custom_date_returns_404_for_missing(client):
    """DELETE on nonexistent custom date should return 404."""
    resp = client.delete("/api/pipeline-custom-dates/99999")
    assert resp.status_code == 404


# --- Custom dates in pipeline entry response ---


def test_custom_dates_included_in_pipeline_entry_read(client, posting_id):
    """Custom dates should appear in the pipeline list entry response."""
    eid = _get_entry_id(client, posting_id)
    client.post(f"/api/pipeline/{eid}/custom-dates", json={
        "label": "Deadline",
        "date": "2026-04-01",
    })
    data = client.get("/api/pipeline").json()
    entry = None
    for entries in data.values():
        for e in entries:
            if e["job_posting"]["id"] == posting_id:
                entry = e
                break
    assert entry is not None
    assert "custom_dates" in entry
    assert len(entry["custom_dates"]) == 1
    assert entry["custom_dates"][0]["label"] == "Deadline"
