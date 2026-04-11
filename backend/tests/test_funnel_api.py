from tests.conftest import *  # noqa: F401,F403


def _create_posting_and_entry(client, stage="interested"):
    """Helper: create a posting via API, return (posting_id, entry_id)."""
    resp = client.post("/api/postings", json={
        "title": "SWE", "company_name": "TestCo", "source": "manual",
    })
    posting_id = resp.json()["id"]
    data = client.get("/api/pipeline").json()
    for entries in data.values():
        for e in entries:
            if e["job_posting"]["id"] == posting_id:
                return posting_id, e["id"]
    raise AssertionError(f"No pipeline entry for posting {posting_id}")


def test_funnel_empty(client):
    resp = client.get("/api/dashboard/funnel")
    assert resp.status_code == 200
    data = resp.json()
    assert data["transitions"] == []
    assert data["stage_counts"] == {}


def test_funnel_with_transitions(client):
    _, eid1 = _create_posting_and_entry(client)
    _, eid2 = _create_posting_and_entry(client)

    for eid in [eid1, eid2]:
        client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applying"})
        client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applied"})

    client.put(f"/api/pipeline/{eid1}/move", json={"to_stage": "recruiter_screen_scheduled"})
    client.put(f"/api/pipeline/{eid2}/move", json={"to_stage": "rejected"})

    resp = client.get("/api/dashboard/funnel")
    assert resp.status_code == 200
    data = resp.json()

    transitions = {(t["from_stage"], t["to_stage"]): t["count"] for t in data["transitions"]}
    assert transitions[("Interested", "Applying")] == 2
    assert transitions[("Applying", "Applied")] == 2
    assert transitions[("Applied", "Recruiter Screen")] == 1
    assert transitions[("Applied", "Rejected")] == 1

    assert data["stage_counts"]["Recruiter Screen"] == 1
    assert data["stage_counts"]["Rejected"] == 1


def test_funnel_collapses_sublanes(client):
    _, eid = _create_posting_and_entry(client)
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applying"})
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applied"})
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "recruiter_screen_scheduled"})
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "recruiter_screen_completed"})

    resp = client.get("/api/dashboard/funnel")
    data = resp.json()
    transitions = {(t["from_stage"], t["to_stage"]): t["count"] for t in data["transitions"]}

    assert ("Recruiter Screen", "Recruiter Screen") not in transitions
    assert transitions[("Applied", "Recruiter Screen")] == 1


def test_funnel_date_filter(client):
    _, eid = _create_posting_and_entry(client)
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applying"})

    resp = client.get("/api/dashboard/funnel?start=2099-01-01T00:00:00")
    data = resp.json()
    assert data["transitions"] == []

    resp = client.get("/api/dashboard/funnel")
    data = resp.json()
    assert len(data["transitions"]) == 1
