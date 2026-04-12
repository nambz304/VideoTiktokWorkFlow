# services/video_assembler.py
import subprocess, os
from typing import Optional

class VideoAssembler:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _get_audio_duration(self, audio_path: str) -> float:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())

    def _build_ffmpeg_cmd(
        self, image_path: str, audio_path: str, output_path: str, duration: float
    ) -> list:
        fps = 25
        total_frames = int(duration * fps)
        zoom_filter = (
            f"zoompan=z='min(zoom+0.0005,1.1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={total_frames}:s=1080x1920:fps={fps}"
        )
        return [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-vf", zoom_filter,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-pix_fmt", "yuv420p",
            output_path
        ]

    def assemble(
        self, image_path: str, audio_path: str, caption: str, output_path: str
    ) -> str:
        duration = self._get_audio_duration(audio_path)
        cmd = self._build_ffmpeg_cmd(image_path, audio_path, output_path, duration)
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
