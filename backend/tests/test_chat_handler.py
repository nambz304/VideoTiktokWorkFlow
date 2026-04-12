from unittest.mock import patch, MagicMock
from services.chat_handler import ChatHandler


def test_chat_returns_text():
    handler = ChatHandler(api_key="fake")
    mock_resp = MagicMock()
    mock_resp.text = "Tôi sẽ đổi ảnh cảnh 2 cho bạn."
    with patch.object(handler._model, "generate_content", return_value=mock_resp):
        result = handler.chat(
            message="đổi ảnh cảnh 2 sang milo_happy",
            step=3,
            session_context={"topic": "Ngủ ngon", "step": 3},
        )
        assert isinstance(result, str)
        assert len(result) > 0


def test_chat_includes_step_context():
    handler = ChatHandler(api_key="fake")
    captured_prompt = []
    mock_resp = MagicMock()
    mock_resp.text = "OK"

    def side_effect(p):
        captured_prompt.append(p)
        return mock_resp

    with patch.object(handler._model, "generate_content", side_effect=side_effect):
        handler.chat(message="help", step=3, session_context={})
        assert any("ước 3" in str(p) for p in captured_prompt)
