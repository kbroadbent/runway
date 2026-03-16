import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models import Company, JobPosting, PipelineEntry, PipelineHistory, InterviewNote  # noqa: F401 — register models
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


@pytest.fixture
def posting_id(client):
    resp = client.post("/api/postings", json={"title": "Eng", "company_name": "Acme", "source": "manual"})
    return resp.json()["id"]


def test_add_to_pipeline(client, posting_id):
    resp = client.post("/api/pipeline", json={"job_posting_id": posting_id, "stage": "interested"})
    assert resp.status_code == 201
    assert resp.json()["stage"] == "interested"


def test_list_pipeline(client, posting_id):
    client.post("/api/pipeline", json={"job_posting_id": posting_id})
    resp = client.get("/api/pipeline")
    assert resp.status_code == 200
    data = resp.json()
    assert "interested" in data


def test_move_stage(client, posting_id):
    create = client.post("/api/pipeline", json={"job_posting_id": posting_id})
    eid = create.json()["id"]
    resp = client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applying", "note": "Applied online"})
    assert resp.status_code == 200
    assert resp.json()["stage"] == "applying"


def test_stage_history(client, posting_id):
    create = client.post("/api/pipeline", json={"job_posting_id": posting_id})
    eid = create.json()["id"]
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applying"})
    client.put(f"/api/pipeline/{eid}/move", json={"to_stage": "applied"})
    resp = client.get(f"/api/pipeline/{eid}/history")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_add_interview_note(client, posting_id):
    create = client.post("/api/pipeline", json={"job_posting_id": posting_id, "stage": "recruiter_screen"})
    eid = create.json()["id"]
    resp = client.post(f"/api/pipeline/{eid}/interviews", json={"round": "Phone Screen", "outcome": "passed"})
    assert resp.status_code == 201
    assert resp.json()["round"] == "Phone Screen"


def test_list_interview_notes(client, posting_id):
    create = client.post("/api/pipeline", json={"job_posting_id": posting_id, "stage": "recruiter_screen"})
    eid = create.json()["id"]
    client.post(f"/api/pipeline/{eid}/interviews", json={"round": "Phone Screen"})
    client.post(f"/api/pipeline/{eid}/interviews", json={"round": "Technical"})
    resp = client.get(f"/api/pipeline/{eid}/interviews")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_update_interview_note(client, posting_id):
    create = client.post("/api/pipeline", json={"job_posting_id": posting_id, "stage": "recruiter_screen"})
    eid = create.json()["id"]
    note = client.post(f"/api/pipeline/{eid}/interviews", json={"round": "Phone Screen"})
    nid = note.json()["id"]
    resp = client.put(f"/api/interviews/{nid}", json={"outcome": "passed", "notes": "Went well"})
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "passed"


def test_delete_interview_note(client, posting_id):
    create = client.post("/api/pipeline", json={"job_posting_id": posting_id, "stage": "recruiter_screen"})
    eid = create.json()["id"]
    note = client.post(f"/api/pipeline/{eid}/interviews", json={"round": "Phone Screen"})
    nid = note.json()["id"]
    resp = client.delete(f"/api/interviews/{nid}")
    assert resp.status_code == 204
