import pytest


@pytest.fixture
def pipeline_entry_id(client):
    resp = client.post("/api/postings", json={"title": "Eng", "company_name": "Acme", "source": "manual"})
    pid = resp.json()["id"]
    data = client.get("/api/pipeline").json()
    for entries in data.values():
        for e in entries:
            if e["job_posting_id"] == pid:
                return e["id"]


def test_add_manual_event(client, pipeline_entry_id):
    resp = client.post(f"/api/pipeline/{pipeline_entry_id}/history", json={
        "description": "Coffee chat with hiring manager",
        "event_date": "2026-03-15T10:00:00",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_type"] == "manual"
    assert data["description"] == "Coffee chat with hiring manager"
    assert data["from_stage"] is None
    assert data["to_stage"] is None


def test_add_manual_event_without_date(client, pipeline_entry_id):
    resp = client.post(f"/api/pipeline/{pipeline_entry_id}/history", json={
        "description": "Sent thank-you email",
    })
    assert resp.status_code == 201
    assert resp.json()["event_date"] is None


def test_manual_event_requires_description(client, pipeline_entry_id):
    resp = client.post(f"/api/pipeline/{pipeline_entry_id}/history", json={})
    assert resp.status_code == 422


def test_stage_changes_have_event_type(client, pipeline_entry_id):
    client.put(f"/api/pipeline/{pipeline_entry_id}/move", json={"to_stage": "applying"})
    resp = client.get(f"/api/pipeline/{pipeline_entry_id}/history")
    for h in resp.json():
        assert h["event_type"] == "stage_change"


def test_history_includes_both_types(client, pipeline_entry_id):
    client.put(f"/api/pipeline/{pipeline_entry_id}/move", json={"to_stage": "applying"})
    client.post(f"/api/pipeline/{pipeline_entry_id}/history", json={
        "description": "Informal chat",
    })
    resp = client.get(f"/api/pipeline/{pipeline_entry_id}/history")
    types = [h["event_type"] for h in resp.json()]
    assert "stage_change" in types
    assert "manual" in types


def test_manual_event_404_for_missing_entry(client):
    resp = client.post("/api/pipeline/9999/history", json={"description": "test"})
    assert resp.status_code == 404
