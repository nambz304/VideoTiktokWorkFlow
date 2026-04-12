# tests/test_video_assembler.py
import pytest
from unittest.mock import patch, MagicMock
from services.video_assembler import VideoAssembler

@pytest.fixture
def assembler(tmp_path):
    return VideoAssembler(output_dir=str(tmp_path))

def test_build_command_includes_ken_burns(assembler):
    cmd = assembler._build_ffmpeg_cmd(
        image_path="/img/milo.png",
        audio_path="/audio/scene1.mp3",
        output_path="/out/scene1.mp4",
        duration=5.0
    )
    cmd_str = " ".join(cmd)
    assert "zoompan" in cmd_str
    assert "/img/milo.png" in cmd_str
    assert "/audio/scene1.mp3" in cmd_str
    assert "/out/scene1.mp4" in cmd_str

def test_assemble_calls_ffmpeg(assembler):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch.object(assembler, '_get_audio_duration', return_value=4.5):
            result = assembler.assemble(
                image_path="/img/milo.png",
                audio_path="/audio/s1.mp3",
                caption="Xin chào mọi người",
                output_path="/out/scene1.mp4"
            )
            assert mock_run.called
            assert result == "/out/scene1.mp4"
