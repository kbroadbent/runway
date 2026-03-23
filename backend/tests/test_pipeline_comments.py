import pytest


@pytest.fixture
def pipeline_entry_id(client):
    resp = client.post("/api/postings", json={"title": "Eng", "company_name": "Acme", "source": "manual"})
    pid = resp.json()["id"]
    resp = client.post("/api/pipeline", json={"job_posting_id": pid, "stage": "interested"})
    return resp.json()["id"]


def test_add_comment(client, pipeline_entry_id):
    resp = client.post(f"/api/pipeline/{pipeline_entry_id}/comments", json={
        "content": "Looks like a great opportunity",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "Looks like a great opportunity"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_list_comments(client, pipeline_entry_id):
    client.post(f"/api/pipeline/{pipeline_entry_id}/comments", json={"content": "First"})
    client.post(f"/api/pipeline/{pipeline_entry_id}/comments", json={"content": "Second"})
    resp = client.get(f"/api/pipeline/{pipeline_entry_id}/comments")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    assert resp.json()[0]["content"] == "First"
    assert resp.json()[1]["content"] == "Second"


def test_update_comment(client, pipeline_entry_id):
    create = client.post(f"/api/pipeline/{pipeline_entry_id}/comments", json={"content": "Draft"})
    cid = create.json()["id"]
    resp = client.put(f"/api/pipeline-comments/{cid}", json={"content": "Updated thought"})
    assert resp.status_code == 200
    assert resp.json()["content"] == "Updated thought"


def test_delete_comment(client, pipeline_entry_id):
    create = client.post(f"/api/pipeline/{pipeline_entry_id}/comments", json={"content": "Temp"})
    cid = create.json()["id"]
    resp = client.delete(f"/api/pipeline-comments/{cid}")
    assert resp.status_code == 204
    resp = client.get(f"/api/pipeline/{pipeline_entry_id}/comments")
    assert len(resp.json()) == 0


def test_comment_requires_content(client, pipeline_entry_id):
    resp = client.post(f"/api/pipeline/{pipeline_entry_id}/comments", json={})
    assert resp.status_code == 422


def test_comment_404_for_missing_entry(client):
    resp = client.post("/api/pipeline/9999/comments", json={"content": "test"})
    assert resp.status_code == 404


def test_update_nonexistent_comment(client):
    resp = client.put("/api/pipeline-comments/9999", json={"content": "test"})
    assert resp.status_code == 404


def test_delete_nonexistent_comment(client):
    resp = client.delete("/api/pipeline-comments/9999")
    assert resp.status_code == 404
