from datetime import datetime, timedelta


def _create_posting_and_entry(client, stage="interested"):
    """Helper: create a posting via API and return (posting_id, entry_id)."""
    resp = client.post("/api/postings", json={"title": "SWE", "company_name": "TestCo", "source": "manual"})
    posting_id = resp.json()["id"]
    entry_id = _get_entry_id(client, posting_id)
    if stage != "interested":
        client.put(f"/api/pipeline/{entry_id}/move", json={"to_stage": stage})
    return posting_id, entry_id


def _get_entry_id(client, posting_id):
    data = client.get("/api/pipeline").json()
    for entries in data.values():
        for e in entries:
            if e["job_posting"]["id"] == posting_id:
                return e["id"]
    raise AssertionError(f"No pipeline entry found for posting {posting_id}")


def test_dashboard_action_items_include_upcoming_interviews(client):
    """Interviews with no outcome and recent scheduled_at should appear."""
    _, entry_id = _create_posting_and_entry(client, stage="tech_screen_scheduled")

    scheduled = (datetime.utcnow() + timedelta(days=2)).isoformat()
    resp = client.post(f"/api/pipeline/{entry_id}/interviews", json={
        "round": "Technical",
        "scheduled_at": scheduled,
    })
    assert resp.status_code == 201

    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    events = resp.json()["upcoming_events"]
    assert len(events) == 1
    assert events[0]["description"] == "Technical"
    assert events[0]["is_overdue"] is False


def test_dashboard_excludes_interviews_with_outcome(client):
    """Interviews with an outcome set should NOT appear in upcoming events."""
    _, entry_id = _create_posting_and_entry(client, stage="tech_screen_completed")

    scheduled = (datetime.utcnow() - timedelta(days=1)).isoformat()
    resp = client.post(f"/api/pipeline/{entry_id}/interviews", json={
        "round": "Technical",
        "scheduled_at": scheduled,
        "outcome": "passed",
    })
    assert resp.status_code == 201

    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    events = resp.json()["upcoming_events"]
    assert len(events) == 0


def test_dashboard_overdue_interview(client):
    """An interview scheduled in the past with no outcome should be marked overdue."""
    _, entry_id = _create_posting_and_entry(client, stage="onsite_scheduled")

    scheduled = (datetime.utcnow() - timedelta(days=2)).isoformat()
    resp = client.post(f"/api/pipeline/{entry_id}/interviews", json={
        "round": "Onsite",
        "scheduled_at": scheduled,
    })
    assert resp.status_code == 201

    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    events = resp.json()["upcoming_events"]
    assert len(events) == 1
    assert events[0]["is_overdue"] is True
