"""Test that step 4 uses dialogue for TTS, not script_text."""
import pytest
from unittest.mock import MagicMock, patch


def test_step4_uses_dialogue_not_script_text():
    """TTS must receive dialogue text, not script_text."""
    from routers.pipeline import step_4_scene_video

    # Mock scene with different dialogue and script_text
    mock_scene = MagicMock()
    mock_scene.id = 1
    mock_scene.session_id = 1
    mock_scene.script_text = "Milo nhảy vào màn hình hài hước: 'Xin chào!'  ← full script_text"
    mock_scene.dialogue = "Xin chào!"  # ← only the spoken words
    mock_scene.action = "Milo nhảy vào màn hình hài hước"
    mock_scene.image_path = "/tmp/test.png"
    mock_scene.emotion_tag = "happy"
    mock_scene.act = "hook"

    mock_session = MagicMock()
    mock_session.lang = "vi"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [mock_scene, mock_session]

    tts_calls = []

    with patch("routers.pipeline._get_tts") as mock_tts_factory, \
         patch("routers.pipeline._get_assembler") as mock_asm_factory, \
         patch("os.path.join", side_effect=lambda *a: "/".join(a)):

        mock_tts = MagicMock()
        mock_tts_factory.return_value = mock_tts
        mock_asm = MagicMock()
        mock_asm_factory.return_value = mock_asm

        def capture_tts(**kwargs):
            tts_calls.append(kwargs.get("text", ""))
        mock_tts.generate_sync.side_effect = capture_tts

        try:
            step_4_scene_video(session_id=1, scene_id=1, db=mock_db)
        except Exception:
            pass  # other side effects may fail, not important

    assert len(tts_calls) > 0, "TTS was not called"
    assert tts_calls[0] == "Xin chào!", \
        f"TTS received '{tts_calls[0]}' instead of dialogue 'Xin chào!'"


def test_step4_fallback_to_script_text_when_no_dialogue():
    """If dialogue is null, fallback to script_text."""
    from routers.pipeline import step_4_scene_video

    mock_scene = MagicMock()
    mock_scene.id = 1
    mock_scene.session_id = 1
    mock_scene.script_text = "Nội dung đầy đủ"
    mock_scene.dialogue = None  # no dialogue
    mock_scene.image_path = "/tmp/test.png"
    mock_scene.emotion_tag = "happy"
    mock_scene.act = "hook"

    mock_session = MagicMock()
    mock_session.lang = "vi"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [mock_scene, mock_session]

    tts_calls = []

    with patch("routers.pipeline._get_tts") as mock_tts_factory, \
         patch("routers.pipeline._get_assembler") as mock_asm_factory, \
         patch("os.path.join", side_effect=lambda *a: "/".join(a)):

        mock_tts = MagicMock()
        mock_tts_factory.return_value = mock_tts
        mock_asm = MagicMock()
        mock_asm_factory.return_value = mock_asm

        def capture_tts(**kwargs):
            tts_calls.append(kwargs.get("text", ""))
        mock_tts.generate_sync.side_effect = capture_tts

        try:
            step_4_scene_video(session_id=1, scene_id=1, db=mock_db)
        except Exception:
            pass

    assert len(tts_calls) > 0
    assert tts_calls[0] == "Nội dung đầy đủ"
