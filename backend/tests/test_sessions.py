import pytest
from fastapi.testclient import TestClient

def test_create_session(client):
    res = client.post("/sessions", json={"title": "Test Video", "lang": "vi"})
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Test Video"
    assert data["step"] == 1
    assert data["status"] == "draft"

def test_list_sessions(client):
    client.post("/sessions", json={"title": "Video A", "lang": "vi"})
    client.post("/sessions", json={"title": "Video B", "lang": "en"})
    res = client.get("/sessions")
    assert res.status_code == 200
    assert len(res.json()) >= 2

def test_get_session(client):
    created = client.post("/sessions", json={"title": "My Video", "lang": "vi"}).json()
    res = client.get(f"/sessions/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]

def test_get_session_not_found(client):
    res = client.get("/sessions/99999")
    assert res.status_code == 404

def test_update_session_step(client):
    created = client.post("/sessions", json={"title": "Video", "lang": "vi"}).json()
    res = client.patch(f"/sessions/{created['id']}", json={"step": 2, "topic": "Ngủ đủ giấc"})
    assert res.status_code == 200
    assert res.json()["step"] == 2
    assert res.json()["topic"] == "Ngủ đủ giấc"

def test_delete_session(client):
    created = client.post("/sessions", json={"title": "To Delete", "lang": "vi"}).json()
    res = client.delete(f"/sessions/{created['id']}")
    assert res.status_code == 200
    assert client.get(f"/sessions/{created['id']}").status_code == 404

def test_get_scenes_not_found(client):
    res = client.get("/sessions/99999/scenes")
    assert res.status_code == 404
