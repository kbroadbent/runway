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
