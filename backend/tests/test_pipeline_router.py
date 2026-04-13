import pytest
from unittest.mock import patch


def test_step1a_trends(client):
    with patch("services.trend_fetcher.TrendFetcher.fetch", return_value=[
        {"topic": "Ngủ đủ giấc", "score": 90, "source": "google_trends"}
    ]):
        session = client.post("/sessions", json={"title": "Test", "lang": "vi"}).json()
        res = client.post(f"/sessions/{session['id']}/step/1a")
        assert res.status_code == 200
        assert isinstance(res.json(), list)


def test_step1c_scripts(client):
    with patch("services.script_generator.ScriptGenerator.generate_scripts", return_value=[
        "Script A: Hook...", "Script B: Hook..."
    ]):
        session = client.post("/sessions", json={"title": "Test", "lang": "vi"}).json()
        client.patch(f"/sessions/{session['id']}", json={"topic": "Ngủ ngon"})
        res = client.post(f"/sessions/{session['id']}/step/1c")
        assert res.status_code == 200
        assert len(res.json()["scripts"]) == 2


def test_step2_scenes(client):
    with patch("services.scene_splitter.SceneSplitter.split", return_value=[
        {"order": 1, "text": "Chào mọi người", "emotion": "wave"},
        {"order": 2, "text": "Hôm nay Milo chia sẻ", "emotion": "explain"},
    ]):
        session = client.post("/sessions", json={"title": "Test", "lang": "vi"}).json()
        client.patch(f"/sessions/{session['id']}", json={"topic": "Test"})
        res = client.post(f"/sessions/{session['id']}/step/2", json={"script": "Test script"})
        assert res.status_code == 200
        scenes = res.json()["scenes"]
        assert len(scenes) == 2
        assert scenes[0]["emotion_tag"] == "wave"


def test_chat_endpoint(client):
    with patch("routers.chat.ClaudeHandler") as MockHandler:
        MockHandler.return_value.chat.return_value = "OK tôi hiểu rồi!"
        session = client.post("/sessions", json={"title": "Test", "lang": "vi"}).json()
        res = client.post("/chat", json={
            "session_id": session["id"],
            "message": "help",
            "step": 3
        })
        assert res.status_code == 200
        assert res.json()["reply"] == "OK tôi hiểu rồi!"
