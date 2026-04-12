from unittest.mock import patch, MagicMock
from services.scene_splitter import SceneSplitter

def test_split_returns_scenes():
    splitter = SceneSplitter(api_key="fake")
    mock_resp = MagicMock()
    mock_resp.text = """
    [{"order":1,"text":"Chào mọi người! Hôm nay Milo sẽ chia sẻ về giấc ngủ.","emotion":"wave"},
     {"order":2,"text":"Bạn có biết thiếu ngủ làm tăng cân không?","emotion":"question"},
     {"order":3,"text":"Ngủ đủ 8 tiếng giúp giảm hormone gây thèm ăn.","emotion":"explain"}]
    """
    with patch.object(splitter._model, 'generate_content', return_value=mock_resp):
        scenes = splitter.split(script="some script text", lang="vi")
        assert len(scenes) == 3
        assert scenes[0]["order"] == 1
        assert scenes[0]["emotion"] in {"wave","happy","question","explain","recommend","cta","sleep","eat","exercise","surprise","think","point"}
        assert "text" in scenes[0]

def test_split_validates_emotion_tags():
    splitter = SceneSplitter(api_key="fake")
    mock_resp = MagicMock()
    mock_resp.text = '[{"order":1,"text":"hello","emotion":"INVALID_TAG"}]'
    with patch.object(splitter._model, 'generate_content', return_value=mock_resp):
        scenes = splitter.split(script="text", lang="vi")
        assert scenes[0]["emotion"] == "explain"
