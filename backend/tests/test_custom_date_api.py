"""Tests for custom date CRUD API endpoints and stage_dates on move.

These endpoints are required by the KeyDates frontend component:
- GET    /api/pipeline/{entry_id}/dates
- POST   /api/pipeline/{entry_id}/dates
- PUT    /api/pipeline/{entry_id}/dates/{date_id}
- DELETE /api/pipeline/{entry_id}/dates/{date_id}

And the move endpoint should persist stage_dates atomically:
- PUT    /api/pipeline/{entry_id}/move  (with stage_dates in body)
"""

import pytest


@pytest.fixture
def posting_id(client):
    resp = client.post("/api/postings", json={
        "title": "Engineer", "company_name": "DateCo", "source": "manual",
    })
    return resp.json()["id"]


def _get_entry_id(client, posting_id):
    data = client.get("/api/pipeline").json()
    for entries in data.values():
        for e in entries:
            if e["job_posting"]["id"] == posting_id:
                return e["id"]
    raise AssertionError(f"No pipeline entry for posting {posting_id}")


# ---------------------------------------------------------------------------
# GET /api/pipeline/{entry_id}/dates — list custom dates
# ---------------------------------------------------------------------------


def test_list_custom_dates_returns_empty_list(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.get(f"/api/pipeline/{eid}/dates")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_custom_dates_returns_404_for_missing_entry(client):
    resp = client.get("/api/pipeline/99999/dates")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/pipeline/{entry_id}/dates — create custom date
# ---------------------------------------------------------------------------


def test_create_custom_date_returns_201(client, posting_id):
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


def test_create_custom_date_appears_in_list(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    client.post(f"/api/pipeline/{eid}/dates", json={
        "label": "Deadline",
        "date": "2026-05-15",
    })
    resp = client.get(f"/api/pipeline/{eid}/dates")
    assert resp.status_code == 200
    dates = resp.json()
    assert len(dates) == 1
    assert dates[0]["label"] == "Deadline"


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


def test_create_custom_date_returns_404_for_missing_entry(client):
    resp = client.post("/api/pipeline/99999/dates", json={
        "label": "Test",
        "date": "2026-04-01",
    })
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/pipeline/{entry_id}/dates/{date_id} — update custom date
# ---------------------------------------------------------------------------


def test_update_custom_date_label(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/dates", json={
        "label": "Old Label",
        "date": "2026-04-01",
    })
    date_id = create_resp.json()["id"]
    resp = client.put(f"/api/pipeline/{eid}/dates/{date_id}", json={
        "label": "New Label",
    })
    assert resp.status_code == 200
    assert resp.json()["label"] == "New Label"
    assert resp.json()["date"] == "2026-04-01"


def test_update_custom_date_date(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/dates", json={
        "label": "Event",
        "date": "2026-04-01",
    })
    date_id = create_resp.json()["id"]
    resp = client.put(f"/api/pipeline/{eid}/dates/{date_id}", json={
        "date": "2026-06-15",
    })
    assert resp.status_code == 200
    assert resp.json()["date"] == "2026-06-15"
    assert resp.json()["label"] == "Event"


def test_update_custom_date_returns_404_for_missing_date(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/dates/99999", json={
        "label": "Nope",
    })
    assert resp.status_code == 404


def test_update_custom_date_rejects_empty_label(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/dates", json={
        "label": "Valid",
        "date": "2026-04-01",
    })
    date_id = create_resp.json()["id"]
    resp = client.put(f"/api/pipeline/{eid}/dates/{date_id}", json={
        "label": "",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /api/pipeline/{entry_id}/dates/{date_id} — delete custom date
# ---------------------------------------------------------------------------


def test_delete_custom_date_returns_204(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/dates", json={
        "label": "To Delete",
        "date": "2026-04-01",
    })
    date_id = create_resp.json()["id"]
    resp = client.delete(f"/api/pipeline/{eid}/dates/{date_id}")
    assert resp.status_code == 204


def test_delete_custom_date_removes_from_list(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    create_resp = client.post(f"/api/pipeline/{eid}/dates", json={
        "label": "Ephemeral",
        "date": "2026-04-01",
    })
    date_id = create_resp.json()["id"]
    client.delete(f"/api/pipeline/{eid}/dates/{date_id}")
    resp = client.get(f"/api/pipeline/{eid}/dates")
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_delete_custom_date_returns_404_for_missing_date(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.delete(f"/api/pipeline/{eid}/dates/99999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Move endpoint: stage_dates persistence
# ---------------------------------------------------------------------------


def test_move_with_stage_dates_persists_applied_date(client, posting_id):
    """Moving to 'applied' with stage_dates should set applied_date on the entry."""
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "applied",
        "stage_dates": {"applied_date": "2026-03-20"},
    })
    assert resp.status_code == 200
    assert resp.json()["applied_date"] == "2026-03-20"


def test_move_with_stage_dates_persists_verbal_offer_date(client, posting_id):
    """Moving to 'offer_verbal' with stage_dates should set offer_date."""
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "offer_verbal",
        "stage_dates": {
            "offer_date": "2026-04-01",
        },
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["offer_date"] == "2026-04-01"


def test_move_without_stage_dates_still_works(client, posting_id):
    """Moving without stage_dates should work as before (no dates set)."""
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={
        "to_stage": "applied",
    })
    assert resp.status_code == 200
    assert resp.json()["applied_date"] is None


def test_move_ignores_invalid_stage_date_fields(client, posting_id):
    """stage_dates with fields not in STAGE_DATE_FIELDS should be ignored, not error."""
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


# ---------------------------------------------------------------------------
# custom_dates included in pipeline entry read responses
# ---------------------------------------------------------------------------


def test_pipeline_list_includes_custom_dates(client, posting_id):
    """GET /api/pipeline should include custom_dates array in each entry."""
    eid = _get_entry_id(client, posting_id)
    # Create a custom date first
    client.post(f"/api/pipeline/{eid}/dates", json={
        "label": "Visible in list",
        "date": "2026-05-01",
    })
    resp = client.get("/api/pipeline")
    assert resp.status_code == 200
    entry = next(
        e for es in resp.json().values() for e in es
        if e["job_posting"]["id"] == posting_id
    )
    assert "custom_dates" in entry
    assert len(entry["custom_dates"]) == 1
    assert entry["custom_dates"][0]["label"] == "Visible in list"
