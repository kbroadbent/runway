from app.models import Company, JobPosting  # noqa: F401 — register models


def test_create_posting_with_new_company(client):
    resp = client.post("/api/postings", json={
        "title": "Software Engineer",
        "company_name": "Acme Corp",
        "location": "Remote",
        "source": "manual",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Software Engineer"
    # company_name is stored as text; no Company record is auto-created
    assert data["company"] is None
    assert data["company_name"] == "Acme Corp"


def test_create_posting_with_existing_company(client):
    co = client.post("/api/companies", json={"name": "Acme Corp"})
    cid = co.json()["id"]
    resp = client.post("/api/postings", json={
        "title": "Software Engineer",
        "company_id": cid,
        "source": "manual",
    })
    assert resp.status_code == 201
    assert resp.json()["company"]["id"] == cid


def test_list_postings(client):
    client.post("/api/postings", json={"title": "Eng 1", "company_name": "A", "source": "manual"})
    client.post("/api/postings", json={"title": "Eng 2", "company_name": "B", "source": "manual"})
    resp = client.get("/api/postings")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_posting(client):
    create = client.post("/api/postings", json={"title": "Eng", "company_name": "A", "source": "manual"})
    pid = create.json()["id"]
    resp = client.get(f"/api/postings/{pid}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Eng"


def test_update_posting(client):
    create = client.post("/api/postings", json={"title": "Eng", "company_name": "A", "source": "manual"})
    pid = create.json()["id"]
    resp = client.put(f"/api/postings/{pid}", json={"salary_min": 150000, "salary_max": 200000})
    assert resp.status_code == 200
    assert resp.json()["salary_min"] == 150000


def test_delete_posting(client):
    create = client.post("/api/postings", json={"title": "Eng", "company_name": "A", "source": "manual"})
    pid = create.json()["id"]
    resp = client.delete(f"/api/postings/{pid}")
    assert resp.status_code == 204
    assert client.get(f"/api/postings/{pid}").status_code == 404


def test_import_preview_text(client):
    resp = client.post("/api/postings/import", json={
        "text": "Software Engineer\nAcme Corp\nSan Francisco, CA (Remote)\n$150,000 - $200,000\n\nWe are looking for..."
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] is not None
    assert data["raw_content"] is not None


def test_import_confirm(client):
    resp = client.post("/api/postings/import/confirm", json={
        "title": "Software Engineer",
        "company_name": "Acme Corp",
        "location": "San Francisco",
        "salary_min": 150000,
        "salary_max": 200000,
    })
    assert resp.status_code == 201
    assert resp.json()["title"] == "Software Engineer"


def test_import_no_input(client):
    resp = client.post("/api/postings/import", json={})
    assert resp.status_code == 400


def test_import_confirm_saves_notes(client):
    resp = client.post("/api/postings/import/confirm", json={
        "title": "Staff Engineer",
        "company_name": "Acme",
        "notes": "Referral from Jane",
    })
    assert resp.status_code == 201
    assert resp.json()["notes"] == "Referral from Jane"


def test_update_posting_notes(client):
    create = client.post("/api/postings", json={"title": "Eng", "company_name": "A", "source": "manual"})
    pid = create.json()["id"]
    resp = client.put(f"/api/postings/{pid}", json={"notes": "Via recruiter"})
    assert resp.status_code == 200
    assert resp.json()["notes"] == "Via recruiter"
