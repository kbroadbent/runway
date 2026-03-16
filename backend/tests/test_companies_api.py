import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models import Company  # noqa: F401 — register models with Base.metadata
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


def test_create_company(client):
    resp = client.post("/api/companies", json={"name": "Acme Corp", "website": "https://acme.com"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Acme Corp"
    assert data["id"] is not None


def test_list_companies(client):
    client.post("/api/companies", json={"name": "Acme"})
    client.post("/api/companies", json={"name": "Beta"})
    resp = client.get("/api/companies")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_company(client):
    create = client.post("/api/companies", json={"name": "Acme"})
    cid = create.json()["id"]
    resp = client.get(f"/api/companies/{cid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Acme"


def test_update_company(client):
    create = client.post("/api/companies", json={"name": "Acme"})
    cid = create.json()["id"]
    resp = client.put(f"/api/companies/{cid}", json={"notes": "Great culture"})
    assert resp.status_code == 200
    assert resp.json()["notes"] == "Great culture"


def test_get_nonexistent_company(client):
    resp = client.get("/api/companies/999")
    assert resp.status_code == 404
