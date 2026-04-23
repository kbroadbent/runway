import pytest


@pytest.fixture
def pipeline_entry_id(client):
    resp = client.post("/api/postings", json={"title": "Eng", "company_name": "Acme", "source": "manual"})
    pid = resp.json()["id"]
    data = client.get("/api/pipeline").json()
    for entries in data.values():
        for e in entries:
            if e["job_posting"]["id"] == pid:
                return e["id"]


def _create_manual_event(client, pipeline_entry_id):
    resp = client.post(f"/api/pipeline/{pipeline_entry_id}/history", json={
        "description": "Coffee chat with hiring manager",
    })
    assert resp.status_code == 201
    return resp.json()["id"]


def test_delete_history_event_returns_204(client, pipeline_entry_id):
    history_id = _create_manual_event(client, pipeline_entry_id)
    resp = client.delete(f"/api/pipeline-history/{history_id}")
    assert resp.status_code == 204


def test_delete_history_event_removes_it_from_list(client, pipeline_entry_id):
    history_id = _create_manual_event(client, pipeline_entry_id)
    client.delete(f"/api/pipeline-history/{history_id}")
    resp = client.get(f"/api/pipeline/{pipeline_entry_id}/history")
    ids = [h["id"] for h in resp.json()]
    assert history_id not in ids


def test_delete_history_event_returns_404_for_nonexistent_id(client):
    resp = client.delete("/api/pipeline-history/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"] != "Not Found"
