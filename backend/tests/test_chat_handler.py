from unittest.mock import patch, MagicMock
from services.chat_handler import ClaudeHandler


def _make_handler():
    with patch("anthropic.Anthropic"):
        return ClaudeHandler(api_key="fake")


def test_chat_returns_text():
    handler = _make_handler()
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text="Tôi sẽ đổi ảnh cảnh 2 cho bạn.")]
    with patch.object(handler._client.messages, "create", return_value=mock_resp):
        result = handler.chat(
            message="đổi ảnh cảnh 2 sang milo_happy",
            step=3,
            session_context={"topic": "Ngủ ngon", "step": 3},
        )
        assert isinstance(result, str)
        assert len(result) > 0


def test_chat_includes_step_context():
    handler = _make_handler()
    captured_prompt = []
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text="OK")]

    def side_effect(**kwargs):
        captured_prompt.append(kwargs.get("messages", []))
        return mock_resp

    with patch.object(handler._client.messages, "create", side_effect=side_effect):
        handler.chat(message="help", step=3, session_context={})
        assert any("ước 3" in str(p) for p in captured_prompt)


def test_missing_key_raises():
    import pytest
    with pytest.raises(ValueError, match="missing_key:anthropic"):
        ClaudeHandler(api_key="")


def test_custom_model():
    with patch("anthropic.Anthropic"):
        handler = ClaudeHandler(api_key="fake", model="claude-sonnet-4-6")
    assert handler._model == "claude-sonnet-4-6"
