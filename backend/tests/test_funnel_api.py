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
    # Pre-funnel stages (Interested, Applying) are remapped to Applied
    assert ("Interested", "Applying") not in transitions
    assert ("Applying", "Applied") not in transitions
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
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applied"})
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "recruiter_screen_scheduled"})

    resp = client.get("/api/dashboard/funnel?start=2099-01-01T00:00:00")
    data = resp.json()
    # Only "Still Active" transition remains (from stage_counts, not history)
    history_transitions = [t for t in data["transitions"] if t["to_stage"] != "Still Active"]
    assert history_transitions == []

    resp = client.get("/api/dashboard/funnel")
    data = resp.json()
    transitions = {(t["from_stage"], t["to_stage"]): t["count"] for t in data["transitions"]}
    assert transitions[("Applied", "Recruiter Screen")] == 1


def test_funnel_deduplicates_bounced_transitions(client):
    """A posting that bounces (Applied→Withdrawn→Recruiter Screen→Withdrawn)
    should only show Applied→Recruiter Screen→Withdrawn, not double-count."""
    _, eid = _create_posting_and_entry(client)
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applying"})
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applied"})
    # Move to withdrawn, then back to recruiter screen, then withdrawn again
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "withdrawn"})
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "recruiter_screen_scheduled"})
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "withdrawn"})

    resp = client.get("/api/dashboard/funnel")
    data = resp.json()
    transitions = {(t["from_stage"], t["to_stage"]): t["count"] for t in data["transitions"]}

    # Should show the effective path: Applied → Recruiter Screen → Withdrawn
    assert transitions.get(("Applied", "Recruiter Screen")) == 1
    assert transitions.get(("Recruiter Screen", "Withdrawn")) == 1
    # Should NOT have Applied → Withdrawn (that transition was "undone")
    assert ("Applied", "Withdrawn") not in transitions


def test_funnel_ghosted_stage_not_shown_as_still_active(client):
    """Entries in ghosted stage should not produce a 'Still Active' transition in the funnel."""
    _, eid = _create_posting_and_entry(client)
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "ghosted"})

    resp = client.get("/api/dashboard/funnel")
    data = resp.json()
    still_active = [t for t in data["transitions"] if t["to_stage"] == "Still Active"]
    assert still_active == []
