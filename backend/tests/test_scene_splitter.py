import pytest
from unittest.mock import MagicMock, patch
from services.scene_splitter import SceneSplitter

SAMPLE_SCRIPT = """
Milo vào màn hình với điệu nhảy hài hước, làm mặt hoảng sợ và vuốt tay: 'Ê! Bạn đã Follow chưa? Không? Thì Milo cho bạn lý do để Follow ngay đây!'
Milo cầm một viên vitamin to xác: 'Hàng ngày mình ăn cơm, bạn ăn gì để sống khoẻ?'
Milo chỉ vào chiếc vòng đo nhịp tim: 'Này, máy đo nhịp tim này biết bạn sống còn hay không!'
Milo cười ha hả, nhảy nhót: 'Follow Milo ngay để không bỏ lỡ bí kíp sống khoẻ nhé!'
"""

MOCK_RESPONSE = """
[
  {"order": 1, "act": "hook", "action": "Milo nhảy vào màn hình, làm mặt hoảng sợ", "dialogue": "Ê! Bạn đã Follow chưa? Thì Milo cho bạn lý do ngay đây!", "emotion": "surprise"},
  {"order": 2, "act": "main", "action": "Milo cầm viên vitamin to xác", "dialogue": "Hàng ngày mình ăn cơm, bạn ăn gì để sống khoẻ?", "emotion": "recommend"},
  {"order": 3, "act": "main", "action": "Milo chỉ vào vòng đo nhịp tim", "dialogue": "Máy đo nhịp tim này biết bạn sống còn hay không!", "emotion": "point"},
  {"order": 4, "act": "cta", "action": "Milo cười nhảy nhót", "dialogue": "Follow Milo ngay để không bỏ lỡ bí kíp sống khoẻ nhé!", "emotion": "cta"}
]
"""


def make_splitter():
    return SceneSplitter(api_key="test-key")


def mock_response(text):
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


# --- Schema tests ---

def test_split_returns_list(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    assert isinstance(scenes, list)
    assert len(scenes) == 4


def test_scene_has_required_fields(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    for scene in scenes:
        assert "order" in scene
        assert "act" in scene
        assert "action" in scene
        assert "dialogue" in scene
        assert "emotion" in scene


def test_act_values_valid(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    valid_acts = {"hook", "main", "cta"}
    for scene in scenes:
        assert scene["act"] in valid_acts, f"Invalid act: {scene['act']}"


def test_first_scene_is_hook(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    assert scenes[0]["act"] == "hook"


def test_last_scene_is_cta(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    assert scenes[-1]["act"] == "cta"


def test_dialogue_not_empty(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    for scene in scenes:
        assert scene["dialogue"] and len(scene["dialogue"]) > 0


def test_emotion_valid(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    valid = {"happy","wave","question","explain","recommend","cta","sleep","eat","exercise","surprise","think","point"}
    for scene in scenes:
        assert scene["emotion"] in valid


def test_uses_sonnet_model(monkeypatch):
    splitter = make_splitter()
    captured = {}
    def capture(**kw):
        captured["model"] = kw.get("model")
        return mock_response(MOCK_RESPONSE)
    monkeypatch.setattr(splitter._client.messages, "create", capture)
    splitter.split(SAMPLE_SCRIPT)
    assert captured["model"] == "claude-sonnet-4-6"


# --- Fallback tests ---

def test_fallback_on_bad_json(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response("not json at all"))
    scenes = splitter.split(SAMPLE_SCRIPT)
    assert len(scenes) == 1
    assert scenes[0]["act"] == "hook"
    assert scenes[0]["emotion"] == "explain"


def test_fallback_dialogue_uses_action(monkeypatch):
    """Nếu dialogue null/missing, fallback về action text"""
    bad_response = '[{"order":1,"act":"hook","action":"Milo nhảy","dialogue":null,"emotion":"happy"}]'
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(bad_response))
    scenes = splitter.split(SAMPLE_SCRIPT)
    assert scenes[0]["dialogue"] == "Milo nhảy"


def test_first_scene_forced_to_hook_even_if_wrong(monkeypatch):
    """LLM returns wrong act for first scene → code corrects to hook"""
    wrong_response = '[{"order":1,"act":"main","action":"Milo nhảy","dialogue":"Xin chào!","emotion":"happy"},' \
                     '{"order":2,"act":"cta","action":"Milo vẫy","dialogue":"Bye!","emotion":"wave"}]'
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(wrong_response))
    scenes = splitter.split(SAMPLE_SCRIPT)
    assert scenes[0]["act"] == "hook"


def test_last_scene_forced_to_cta_even_if_wrong(monkeypatch):
    """LLM returns wrong act for last scene → code corrects to cta"""
    wrong_response = '[{"order":1,"act":"hook","action":"Milo nhảy","dialogue":"Xin chào!","emotion":"surprise"},' \
                     '{"order":2,"act":"main","action":"Milo vẫy","dialogue":"Bye!","emotion":"wave"}]'
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(wrong_response))
    scenes = splitter.split(SAMPLE_SCRIPT)
    assert scenes[-1]["act"] == "cta"
