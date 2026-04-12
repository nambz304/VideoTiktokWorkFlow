# tests/test_tiktok_client.py
import pytest
from unittest.mock import patch, MagicMock
from services.tiktok_client import TikTokClient

@pytest.fixture
def client():
    return TikTokClient(
        client_key="fake_key",
        client_secret="fake_secret",
        access_token="fake_token"
    )

def test_upload_video_returns_post_id(client, tmp_path):
    fake_video = tmp_path / "final.mp4"
    fake_video.write_bytes(b"fake_video_data")
    with patch("httpx.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"data": {"publish_id": "abc123", "upload_url": "https://fake.url"}, "error": {"code": "ok"}}
        )
        with patch("httpx.put") as mock_put:
            mock_put.return_value = MagicMock(status_code=200)
            result = client.upload(
                video_path=str(fake_video),
                caption="Test caption #health",
                schedule_time=None
            )
            assert result["publish_id"] == "abc123"

def test_upload_raises_on_api_error(client, tmp_path):
    fake_video = tmp_path / "final.mp4"
    fake_video.write_bytes(b"data")
    with patch("httpx.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"error": {"code": "access_token_invalid", "message": "Token invalid"}}
        )
        with pytest.raises(Exception, match="TikTok API error"):
            client.upload(video_path=str(fake_video), caption="test", schedule_time=None)
