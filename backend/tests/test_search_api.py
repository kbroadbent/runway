from unittest.mock import patch
import pandas as pd


def test_create_search_profile(client):
    resp = client.post("/api/search-profiles", json={
        "name": "Remote SWE",
        "search_term": "software engineer",
        "location": "Remote",
        "remote_filter": "remote",
        "sources": ["linkedin", "indeed"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Remote SWE"
    assert data["sources"] == ["linkedin", "indeed"]


def test_list_search_profiles(client):
    client.post("/api/search-profiles", json={"name": "Profile 1", "search_term": "eng"})
    client.post("/api/search-profiles", json={"name": "Profile 2", "search_term": "data"})
    resp = client.get("/api/search-profiles")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_search_profile(client):
    create = client.post("/api/search-profiles", json={"name": "Test", "search_term": "eng"})
    pid = create.json()["id"]
    resp = client.put(f"/api/search-profiles/{pid}", json={"run_interval": 24, "is_auto_enabled": True})
    assert resp.status_code == 200
    assert resp.json()["run_interval"] == 24
    assert resp.json()["is_auto_enabled"] is True


def test_delete_search_profile(client):
    create = client.post("/api/search-profiles", json={"name": "Test", "search_term": "eng"})
    pid = create.json()["id"]
    resp = client.delete(f"/api/search-profiles/{pid}")
    assert resp.status_code == 204
    assert client.get("/api/search-profiles").json() == []


def test_run_search(client):
    create = client.post("/api/search-profiles", json={
        "name": "Test", "search_term": "software engineer", "sources": ["indeed"],
    })
    pid = create.json()["id"]
    mock_df = pd.DataFrame([{
        "title": "Software Engineer",
        "company": "Acme Corp",
        "location": "Remote, US",
        "job_url": "https://indeed.com/job/123",
        "description": "Build stuff",
        "date_posted": "2026-03-10",
        "is_remote": True,
        "min_amount": 150000,
        "max_amount": 200000,
        "site": "indeed",
    }])
    with patch("app.services.search_service.scrape_jobs", return_value=mock_df):
        resp = client.post(f"/api/search-profiles/{pid}/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data["new_count"] == 1


def test_mark_results_reviewed(client):
    create = client.post("/api/search-profiles", json={
        "name": "Test", "search_term": "eng", "sources": ["indeed"],
    })
    pid = create.json()["id"]
    mock_df = pd.DataFrame([{
        "title": "Eng", "company": "Co", "location": "Remote",
        "job_url": "https://indeed.com/1", "description": "desc",
        "date_posted": None, "is_remote": True,
        "min_amount": None, "max_amount": None, "site": "indeed",
    }])
    with patch("app.services.search_service.scrape_jobs", return_value=mock_df):
        client.post(f"/api/search-profiles/{pid}/run")
    resp = client.post(f"/api/search-results/{pid}/mark-reviewed")
    assert resp.status_code == 200
    profiles = client.get("/api/search-profiles").json()
    assert profiles[0]["new_result_count"] == 0
