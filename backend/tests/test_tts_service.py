import pytest, os
from unittest.mock import patch, AsyncMock
from services.tts_service import TTSService

@pytest.fixture
def tts(tmp_path):
    return TTSService(output_dir=str(tmp_path))

def test_voice_selection_vi(tts):
    assert tts.get_voice("vi") == "vi-VN-NamMinhNeural"

def test_voice_selection_en(tts):
    assert tts.get_voice("en") == "en-US-GuyNeural"

def test_generate_creates_file(tts, tmp_path):
    output_path = str(tmp_path / "scene_1.mp3")
    with patch("edge_tts.Communicate") as mock_comm:
        mock_instance = AsyncMock()
        mock_comm.return_value = mock_instance
        mock_instance.save = AsyncMock()
        import asyncio
        result = asyncio.run(tts.generate(text="Xin chào", lang="vi", output_path=output_path))
        mock_instance.save.assert_called_once_with(output_path)
        assert result == output_path
