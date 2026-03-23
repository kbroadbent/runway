import pytest


@pytest.fixture
def seeded_pipeline(client):
    """Create 3 postings with different titles and tiers, add all to pipeline."""
    ids = []
    for title, tier in [("Senior Engineer", 1), ("Staff Designer", 2), ("Junior Engineer", 3)]:
        resp = client.post("/api/postings", json={"title": title, "company_name": "Co", "source": "manual"})
        pid = resp.json()["id"]
        client.put(f"/api/postings/{pid}", json={"tier": tier})
        ids.append(pid)
    return ids


def test_filter_by_title(client, seeded_pipeline):
    resp = client.get("/api/pipeline?title=engineer")
    data = resp.json()
    titles = [e["job_posting"]["title"] for entries in data.values() for e in entries]
    assert "Senior Engineer" in titles
    assert "Junior Engineer" in titles
    assert "Staff Designer" not in titles


def test_filter_by_tier(client, seeded_pipeline):
    resp = client.get("/api/pipeline?tier=1")
    data = resp.json()
    entries = [e for entries in data.values() for e in entries]
    assert len(entries) == 1
    assert entries[0]["job_posting"]["tier"] == 1


def test_filter_by_title_and_tier(client, seeded_pipeline):
    resp = client.get("/api/pipeline?title=engineer&tier=1")
    data = resp.json()
    entries = [e for entries in data.values() for e in entries]
    assert len(entries) == 1
    assert entries[0]["job_posting"]["title"] == "Senior Engineer"


def test_filter_no_results(client, seeded_pipeline):
    resp = client.get("/api/pipeline?title=nonexistent")
    data = resp.json()
    entries = [e for entries in data.values() for e in entries]
    assert len(entries) == 0


def test_no_filter_returns_all(client, seeded_pipeline):
    resp = client.get("/api/pipeline")
    data = resp.json()
    entries = [e for entries in data.values() for e in entries]
    assert len(entries) == 3


def test_filter_case_insensitive(client, seeded_pipeline):
    resp = client.get("/api/pipeline?title=ENGINEER")
    data = resp.json()
    entries = [e for entries in data.values() for e in entries]
    assert len(entries) == 2


def test_invalid_tier_rejected(client, seeded_pipeline):
    resp = client.get("/api/pipeline?tier=5")
    assert resp.status_code == 422
