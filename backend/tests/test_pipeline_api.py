import pytest
from app.models import Company, JobPosting, PipelineEntry, PipelineHistory, InterviewNote  # noqa: F401 — register models


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


def test_add_to_pipeline(client, posting_id):
    # Posting is auto-added to pipeline when created
    resp = client.get("/api/pipeline")
    assert resp.status_code == 200
    entries = [e for es in resp.json().values() for e in es]
    assert any(e["job_posting"]["id"] == posting_id for e in entries)


def test_list_pipeline(client, posting_id):
    resp = client.get("/api/pipeline")
    assert resp.status_code == 200
    data = resp.json()
    assert "interested" in data


def test_move_stage(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applying", "note": "Applied online"})
    assert resp.status_code == 200
    assert resp.json()["stage"] == "applying"


def test_stage_history(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applying"})
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applied"})
    resp = client.get(f"/api/pipeline/{eid}/history")
    assert resp.status_code == 200
    assert len(resp.json()) == 3  # initial entry + 2 moves


def test_add_interview_note(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    resp = client.post(f"/api/pipeline/{eid}/interviews", json={"round": "Phone Screen", "outcome": "passed"})
    assert resp.status_code == 201
    assert resp.json()["round"] == "Phone Screen"


def test_list_interview_notes(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    client.post(f"/api/pipeline/{eid}/interviews", json={"round": "Phone Screen"})
    client.post(f"/api/pipeline/{eid}/interviews", json={"round": "Technical"})
    resp = client.get(f"/api/pipeline/{eid}/interviews")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_interview_note(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    note = client.post(f"/api/pipeline/{eid}/interviews", json={"round": "Phone Screen"})
    nid = note.json()["id"]
    resp = client.put(f"/api/interviews/{nid}", json={"outcome": "passed", "notes": "Went well"})
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "passed"


def test_delete_interview_note(client, posting_id):
    eid = _get_entry_id(client, posting_id)
    note = client.post(f"/api/pipeline/{eid}/interviews", json={"round": "Phone Screen"})
    nid = note.json()["id"]
    resp = client.delete(f"/api/interviews/{nid}")
    assert resp.status_code == 204


def test_update_entry_cannot_change_stage(client, posting_id):
    """Stage changes must go through the /move endpoint."""
    eid = _get_entry_id(client, posting_id)
    resp = client.put(f"/api/pipeline/{eid}", json={"stage": "applied"})
    assert resp.status_code == 200
    # stage should NOT have changed — the field is ignored
    assert resp.json()["stage"] == "interested"
