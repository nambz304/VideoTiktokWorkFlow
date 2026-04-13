import subprocess
import os


class VideoMerger:
    def __init__(self, output_dir: str):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def _create_concat_file(self, clip_paths: list, concat_path: str) -> str:
        with open(concat_path, "w") as f:
            for path in clip_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")
        return concat_path

    def merge(
        self,
        clip_paths: list,
        bgm_path: str,
        output_path: str,
        bgm_volume: float = 0.15,
    ) -> str:
        concat_file = os.path.join(self.output_dir, "concat.txt")
        self._create_concat_file(clip_paths, concat_file)
        temp_out = os.path.join(self.output_dir, "_merged_no_bgm.mp4")

        # Step 1: concatenate clips
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                temp_out,
            ],
            check=True,
            capture_output=True,
        )

        # Step 2: mix background music (skip if no bgm)
        if bgm_path:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", temp_out,
                    "-stream_loop", "-1", "-i", bgm_path,
                    "-filter_complex",
                    f"[1:a]volume={bgm_volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first[aout]",
                    "-map", "0:v", "-map", "[aout]",
                    "-c:v", "copy", "-c:a", "aac", "-shortest",
                    output_path,
                ],
                check=True,
                capture_output=True,
            )
            os.remove(temp_out)
        else:
            os.rename(temp_out, output_path)
        return output_path
