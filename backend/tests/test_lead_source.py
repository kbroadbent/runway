from app.models import Company, JobPosting  # noqa: F401 — register models


def test_create_posting_defaults_lead_source(client):
    resp = client.post("/api/postings", json={
        "title": "Engineer", "company_name": "Acme", "source": "manual",
    })
    assert resp.status_code == 201
    assert resp.json()["lead_source"] == "cold_apply"


def test_create_posting_with_explicit_lead_source(client):
    resp = client.post("/api/postings", json={
        "title": "Engineer", "company_name": "Acme", "source": "manual",
        "lead_source": "referral",
    })
    assert resp.status_code == 201
    assert resp.json()["lead_source"] == "referral"


def test_create_posting_rejects_invalid_lead_source(client):
    resp = client.post("/api/postings", json={
        "title": "Engineer", "company_name": "Acme", "source": "manual",
        "lead_source": "magic",
    })
    assert resp.status_code == 422


def test_update_posting_lead_source(client):
    create = client.post("/api/postings", json={
        "title": "Engineer", "company_name": "Acme", "source": "manual",
    })
    pid = create.json()["id"]
    resp = client.put(f"/api/postings/{pid}", json={"lead_source": "recruiter_inbound"})
    assert resp.status_code == 200
    assert resp.json()["lead_source"] == "recruiter_inbound"


def test_update_posting_rejects_invalid_lead_source(client):
    create = client.post("/api/postings", json={
        "title": "Engineer", "company_name": "Acme", "source": "manual",
    })
    pid = create.json()["id"]
    resp = client.put(f"/api/postings/{pid}", json={"lead_source": "magic"})
    assert resp.status_code == 422


def test_import_confirm_with_lead_source(client):
    resp = client.post("/api/postings/import/confirm", json={
        "title": "Imported Role",
        "company_name": "BigCo",
        "lead_source": "recruiter_outbound",
    })
    assert resp.status_code == 201
    assert resp.json()["lead_source"] == "recruiter_outbound"


def test_import_confirm_defaults_lead_source(client):
    resp = client.post("/api/postings/import/confirm", json={
        "title": "Imported Role 2",
        "company_name": "BigCo2",
    })
    assert resp.status_code == 201
    assert resp.json()["lead_source"] == "cold_apply"


def test_pipeline_filter_by_lead_source(client):
    """Create postings with different lead_sources, filter pipeline."""
    for title, ls in [("Eng A", "referral"), ("Eng B", "recruiter_inbound"), ("Eng C", "cold_apply")]:
        client.post("/api/postings", json={
            "title": title, "company_name": "Co", "source": "manual",
            "lead_source": ls,
        })
    resp = client.get("/api/pipeline?lead_source=referral")
    entries = [e for entries in resp.json().values() for e in entries]
    assert len(entries) == 1
    assert entries[0]["job_posting"]["lead_source"] == "referral"


def test_pipeline_filter_invalid_lead_source(client):
    resp = client.get("/api/pipeline?lead_source=invalid")
    assert resp.status_code == 422


def test_pipeline_no_lead_source_filter_returns_all(client):
    for title, ls in [("Eng X", "referral"), ("Eng Y", "cold_apply")]:
        client.post("/api/postings", json={
            "title": title, "company_name": "Co2", "source": "manual",
            "lead_source": ls,
        })
    resp = client.get("/api/pipeline")
    entries = [e for entries in resp.json().values() for e in entries]
    assert len(entries) == 2
