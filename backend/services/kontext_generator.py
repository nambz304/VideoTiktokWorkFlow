import os
import logging
import requests
import fal_client
from typing import List

logger = logging.getLogger(__name__)

KONTEXT_MODEL = "fal-ai/flux-kontext/dev"


class KontextGenerator:
    def __init__(self, fal_key: str, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        if fal_key:
            os.environ["FAL_KEY"] = fal_key

    def upload_ref_image(self, local_path: str) -> str:
        """Upload ref image to fal.ai storage, return URL."""
        url = fal_client.upload_file(local_path)
        logger.info(f"Uploaded ref image: {local_path} → {url}")
        return url

    def generate(
        self,
        prompt: str,
        ref_image_urls: List[str],
        output_filename: str,
        seed: int = 42,
    ) -> str:
        """
        Call FLUX Kontext with ref images + prompt.
        Returns local path of downloaded image.
        """
        if not ref_image_urls:
            raise ValueError("Cần ít nhất 1 ref image URL")

        arguments = {
            "prompt": prompt,
            "image_url": ref_image_urls[0],   # Kontext takes the main ref image
            "image_size": {"width": 1080, "height": 1920},
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "seed": seed,
            "output_format": "png",
        }

        # If multiple ref images, add extras to prompt context
        if len(ref_image_urls) > 1:
            arguments["extra_image_urls"] = ref_image_urls[1:]

        logger.info(f"Calling Kontext: {KONTEXT_MODEL} | prompt: {prompt[:80]}...")

        result = fal_client.subscribe(
            KONTEXT_MODEL,
            arguments=arguments,
        )

        images = result.get("images", [])
        if not images:
            raise RuntimeError("Kontext trả về không có ảnh")

        image_url = images[0]["url"]
        output_path = os.path.join(self.output_dir, output_filename)
        self._download(image_url, output_path)

        logger.info(f"Kontext image saved: {output_path}")
        return output_path

    def _download(self, url: str, dest: str) -> None:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            f.write(resp.content)
