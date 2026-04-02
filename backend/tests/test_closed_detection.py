from app.models import JobPosting, PipelineEntry


def _create_saved_posting(client, title="SWE", url="https://example.com/job"):
    """Helper: create a saved posting with a URL and return its id."""
    resp = client.post("/api/postings", json={
        "title": title,
        "company_name": "TestCo",
        "source": "manual",
        "url": url,
    })
    assert resp.status_code == 201
    return resp.json()["id"]


def test_dismiss_closed_sets_flag(client, db_session):
    posting_id = _create_saved_posting(client)
    # Manually set is_closed_detected so we can dismiss it
    posting = db_session.get(JobPosting, posting_id)
    posting.is_closed_detected = True
    db_session.commit()

    resp = client.post(f"/api/postings/{posting_id}/dismiss-closed")
    assert resp.status_code == 200
    data = resp.json()
    assert data["closed_check_dismissed"] is True
    assert data["is_closed_detected"] is True


def test_dismiss_closed_404_for_missing_posting(client):
    resp = client.post("/api/postings/99999/dismiss-closed")
    assert resp.status_code == 404


def _create_posting_and_entry(client, title="SWE", url="https://example.com/job"):
    """Helper: create a posting and return (posting_id, entry_id)."""
    posting_id = _create_saved_posting(client, title=title, url=url)
    data = client.get("/api/pipeline").json()
    for entries in data.values():
        for e in entries:
            if e["job_posting"]["id"] == posting_id:
                return posting_id, e["id"]
    raise AssertionError(f"No pipeline entry found for posting {posting_id}")


def test_dashboard_includes_closed_postings(client, db_session):
    posting_id, _ = _create_posting_and_entry(client, url="https://example.com/job1")
    posting = db_session.get(JobPosting, posting_id)
    posting.is_closed_detected = True
    db_session.commit()

    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    closed = resp.json()["closed_postings"]
    assert len(closed) == 1
    assert closed[0]["id"] == posting_id
    assert closed[0]["title"] == "SWE"
    assert closed[0]["company_name"] == "TestCo"
    assert closed[0]["url"] == "https://example.com/job1"


def test_dashboard_excludes_dismissed_closed_postings(client, db_session):
    posting_id, _ = _create_posting_and_entry(client, url="https://example.com/job2")
    posting = db_session.get(JobPosting, posting_id)
    posting.is_closed_detected = True
    posting.closed_check_dismissed = True
    db_session.commit()

    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    closed = resp.json()["closed_postings"]
    assert len(closed) == 0


def test_dashboard_excludes_closed_in_terminal_stages(client, db_session):
    posting_id, entry_id = _create_posting_and_entry(client, url="https://example.com/job3")
    # Move to terminal stage
    client.put(f"/api/pipeline/{entry_id}/move", json={"to_stage": "rejected"})
    posting = db_session.get(JobPosting, posting_id)
    posting.is_closed_detected = True
    db_session.commit()

    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    closed = resp.json()["closed_postings"]
    assert len(closed) == 0
