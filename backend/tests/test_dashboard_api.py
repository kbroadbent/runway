from datetime import date, datetime, timedelta

from app.models import PipelineEntry


def _create_posting_and_entry(client, stage="interested", title="SWE", company="TestCo"):
    """Helper: create a posting via API and return (posting_id, entry_id)."""
    resp = client.post("/api/postings", json={"title": title, "company_name": company, "source": "manual"})
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


def test_dashboard_upcoming_events_include_future_stage_dates(client):
    """Entries with a future interview stage date should appear in upcoming_events."""
    _, entry_id = _create_posting_and_entry(client, stage="tech_screen_scheduled")
    future = (date.today() + timedelta(days=2)).isoformat()
    client.put(f"/api/pipeline/{entry_id}", json={"tech_screen_date": future})

    events = client.get("/api/dashboard").json()["upcoming_events"]
    assert len(events) == 1
    assert events[0]["description"] == "Tech Screen"
    assert events[0]["is_overdue"] is False


def test_dashboard_excludes_past_stage_dates(client):
    """Entries whose interview stage date is in the past should not appear."""
    _, entry_id = _create_posting_and_entry(client, stage="tech_screen_completed")
    past = (date.today() - timedelta(days=1)).isoformat()
    client.put(f"/api/pipeline/{entry_id}", json={"tech_screen_date": past})

    events = client.get("/api/dashboard").json()["upcoming_events"]
    assert len(events) == 0


# --- Completed interviews awaiting next step ---


def test_completed_interviews_includes_recruiter_screen_completed(client):
    """An entry in recruiter_screen_completed with a date should appear."""
    _, entry_id = _create_posting_and_entry(client, stage="recruiter_screen_completed")
    interview_day = (date.today() - timedelta(days=3)).isoformat()
    client.put(f"/api/pipeline/{entry_id}", json={"recruiter_screen_date": interview_day})

    items = client.get("/api/dashboard").json()["completed_interviews"]
    assert len(items) == 1
    assert items[0]["stage_label"] == "Recruiter Screen"
    assert items[0]["interview_date"] == interview_day
    assert items[0]["days_since"] == 3
    assert items[0]["pipeline_entry_id"] == entry_id


def test_completed_interviews_excludes_offer(client):
    """Entries in 'offer' should not appear as completed interviews."""
    _create_posting_and_entry(client, stage="offer")
    items = client.get("/api/dashboard").json()["completed_interviews"]
    assert items == []


def test_completed_interviews_excludes_terminal_stages(client):
    """Entries in rejected/withdrawn/archived should not appear."""
    for stage in ("rejected", "withdrawn", "archived"):
        _create_posting_and_entry(client, stage=stage, title=f"Eng-{stage}")
    items = client.get("/api/dashboard").json()["completed_interviews"]
    assert items == []


def test_completed_interviews_excludes_non_interview_stages(client):
    """Entries in applied or *_scheduled should not appear."""
    _create_posting_and_entry(client, stage="applied", title="A")
    _create_posting_and_entry(client, stage="recruiter_screen_scheduled", title="B")
    items = client.get("/api/dashboard").json()["completed_interviews"]
    assert items == []


def test_completed_interviews_sorted_ascending_by_date(client):
    """Oldest interview date (longest wait) should come first."""
    _, e1 = _create_posting_and_entry(client, stage="recruiter_screen_completed", title="Recent")
    _, e2 = _create_posting_and_entry(client, stage="onsite_completed", title="Older")
    _, e3 = _create_posting_and_entry(client, stage="tech_screen_completed", title="Middle")

    client.put(f"/api/pipeline/{e1}", json={"recruiter_screen_date": (date.today() - timedelta(days=2)).isoformat()})
    client.put(f"/api/pipeline/{e2}", json={"onsite_date": (date.today() - timedelta(days=10)).isoformat()})
    client.put(f"/api/pipeline/{e3}", json={"tech_screen_date": (date.today() - timedelta(days=5)).isoformat()})

    items = client.get("/api/dashboard").json()["completed_interviews"]
    assert [i["job_title"] for i in items] == ["Older", "Middle", "Recent"]


def test_completed_interviews_null_date_still_appears(client):
    """If the stage date is null, the entry still appears with null interview_date."""
    _, entry_id = _create_posting_and_entry(client, stage="manager_screen_completed")
    items = client.get("/api/dashboard").json()["completed_interviews"]
    assert len(items) == 1
    assert items[0]["stage_label"] == "Manager Screen"
    assert items[0]["interview_date"] is None
    # days_since falls back to (now - updated_at); value depends on env timezone
    # so we just verify it's a small integer (just-created entry).
    assert isinstance(items[0]["days_since"], int)
    assert abs(items[0]["days_since"]) <= 1


def test_stale_entries_excludes_ghosted_stage(client, db_session):
    """Entries in ghosted stage should not appear as stale entries."""
    _, entry_id = _create_posting_and_entry(client, stage="ghosted")
    entry = db_session.get(PipelineEntry, entry_id)
    entry.updated_at = datetime.now() - timedelta(days=10)
    db_session.commit()

    items = client.get("/api/dashboard").json()["stale_entries"]
    assert items == []
