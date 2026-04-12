from unittest.mock import patch, MagicMock
from services.video_merger import VideoMerger

def test_create_concat_file(tmp_path):
    merger = VideoMerger(output_dir=str(tmp_path))
    clips = ["/a/clip1.mp4", "/a/clip2.mp4"]
    concat_path = merger._create_concat_file(clips, str(tmp_path / "concat.txt"))
    content = open(concat_path).read()
    assert "clip1.mp4" in content
    assert "clip2.mp4" in content
    assert "file" in content

def test_merge_calls_ffmpeg(tmp_path):
    merger = VideoMerger(output_dir=str(tmp_path))
    with patch("subprocess.run") as mock_run, \
         patch("os.remove") as mock_remove:
        mock_run.return_value = MagicMock(returncode=0)
        result = merger.merge(
            clip_paths=["/a/s1.mp4", "/a/s2.mp4"],
            bgm_path="/music/bg.mp3",
            output_path=str(tmp_path / "final.mp4"),
            bgm_volume=0.15
        )
        assert mock_run.called
        assert result == str(tmp_path / "final.mp4")
