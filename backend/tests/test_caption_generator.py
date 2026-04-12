from unittest.mock import patch, MagicMock
from services.caption_generator import CaptionGenerator

def test_generate_returns_caption_and_hashtags():
    gen = CaptionGenerator(api_key="fake")
    mock_resp = MagicMock()
    mock_resp.text = "CAPTION:\nMilo chia sẻ bí quyết ngủ ngon 💤\n\nHASHTAGS:\n#suckhoe #milo #tiktok #AI"
    with patch.object(gen._model, 'generate_content', return_value=mock_resp):
        result = gen.generate(script="Test script", topic="Ngủ ngon", lang="vi")
        assert "caption" in result
        assert "hashtags" in result
        assert isinstance(result["hashtags"], list)
