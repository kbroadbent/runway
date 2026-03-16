import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models import Company, JobPosting  # noqa: F401 — register models
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


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
    assert data["company"]["name"] == "Acme Corp"


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
