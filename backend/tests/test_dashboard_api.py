import pytest
from datetime import datetime, timedelta
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


# --- Endpoint exists and returns correct shape ---


def test_dashboard_returns_200(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200


def test_dashboard_returns_lane_counts_and_action_items(client):
    resp = client.get("/api/dashboard")
    data = resp.json()
    assert "lane_counts" in data
    assert "action_items" in data
    assert isinstance(data["lane_counts"], dict)
    assert isinstance(data["action_items"], list)


# --- Lane counts ---


def test_dashboard_empty_pipeline_returns_zero_counts(client):
    resp = client.get("/api/dashboard")
    data = resp.json()
    for count in data["lane_counts"].values():
        assert count == 0


def test_dashboard_counts_postings_in_interested_lane(client, posting_id):
    resp = client.get("/api/dashboard")
    data = resp.json()
    assert data["lane_counts"]["Interested"] == 1


def test_dashboard_counts_postings_across_multiple_lanes(client):
    # Create two postings — both start in "interested"
    p1 = client.post("/api/postings", json={"title": "Eng A", "company_name": "Co A", "source": "manual"})
    p2 = client.post("/api/postings", json={"title": "Eng B", "company_name": "Co B", "source": "manual"})

    # Move second posting to "applied"
    eid = _get_entry_id(client, p2.json()["id"])
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applied"})

    resp = client.get("/api/dashboard")
    data = resp.json()
    assert data["lane_counts"]["Interested"] == 1
    assert data["lane_counts"]["Applied"] == 1


def test_dashboard_groups_stages_into_lanes(client):
    """recruiter_screen_scheduled and recruiter_screen_completed both map to 'Recruiter Screen' lane."""
    p1 = client.post("/api/postings", json={"title": "Eng A", "company_name": "Co A", "source": "manual"})
    p2 = client.post("/api/postings", json={"title": "Eng B", "company_name": "Co B", "source": "manual"})

    eid1 = _get_entry_id(client, p1.json()["id"])
    eid2 = _get_entry_id(client, p2.json()["id"])

    client.put(f"/api/pipeline/{eid1}/move", json={"to_stage": "recruiter_screen_scheduled"})
    client.put(f"/api/pipeline/{eid2}/move", json={"to_stage": "recruiter_screen_completed"})

    resp = client.get("/api/dashboard")
    data = resp.json()
    assert data["lane_counts"]["Recruiter Screen"] == 2


# --- Action items ---


def test_dashboard_no_action_items_when_pipeline_empty(client):
    resp = client.get("/api/dashboard")
    data = resp.json()
    assert data["action_items"] == []


def test_dashboard_action_item_for_next_action(client, posting_id, db_session):
    eid = _get_entry_id(client, posting_id)
    # Set a next_action on the pipeline entry
    entry = db_session.query(PipelineEntry).filter_by(id=eid).first()
    entry.next_action = "Send follow-up email"
    entry.next_action_date = datetime.now() + timedelta(days=1)
    db_session.commit()

    resp = client.get("/api/dashboard")
    data = resp.json()
    action_items = data["action_items"]
    assert len(action_items) >= 1
    item = next(a for a in action_items if a["pipeline_entry_id"] == eid)
    assert item["job_title"] == "Eng"
    assert item["description"] == "Send follow-up email"
    assert item["is_overdue"] is False


def test_dashboard_action_item_is_overdue_when_date_past(client, posting_id, db_session):
    eid = _get_entry_id(client, posting_id)
    entry = db_session.query(PipelineEntry).filter_by(id=eid).first()
    entry.next_action = "Follow up"
    entry.next_action_date = datetime.now() - timedelta(days=2)
    db_session.commit()

    resp = client.get("/api/dashboard")
    data = resp.json()
    item = next(a for a in data["action_items"] if a["pipeline_entry_id"] == eid)
    assert item["is_overdue"] is True


def test_dashboard_action_item_includes_company_name(client, posting_id, db_session):
    eid = _get_entry_id(client, posting_id)
    entry = db_session.query(PipelineEntry).filter_by(id=eid).first()
    entry.next_action = "Prep for interview"
    entry.next_action_date = datetime.now() + timedelta(days=1)
    db_session.commit()

    resp = client.get("/api/dashboard")
    data = resp.json()
    item = next(a for a in data["action_items"] if a["pipeline_entry_id"] == eid)
    assert item["company_name"] == "Acme"


def test_dashboard_action_item_without_date_is_not_overdue(client, posting_id, db_session):
    eid = _get_entry_id(client, posting_id)
    entry = db_session.query(PipelineEntry).filter_by(id=eid).first()
    entry.next_action = "Research company"
    entry.next_action_date = None
    db_session.commit()

    resp = client.get("/api/dashboard")
    data = resp.json()
    item = next(a for a in data["action_items"] if a["pipeline_entry_id"] == eid)
    assert item["date"] is None
    assert item["is_overdue"] is False
