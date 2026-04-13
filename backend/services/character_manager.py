import json
import os
import shutil
import logging
from typing import List

logger = logging.getLogger(__name__)

ACT_CONTEXT = {
    "hook": "energetic and eye-catching scene, dynamic background, bright colors",
    "main": "clean informative setting, health and wellness environment, soft lighting",
    "cta":  "warm inviting atmosphere, product spotlight, encouraging mood",
}


class CharacterManager:
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir
        os.makedirs(assets_dir, exist_ok=True)

    def save_ref_images(self, char_id: int, source_paths: List[str]) -> List[str]:
        """Copy uploaded ref images into assets/characters/{char_id}/"""
        char_dir = os.path.join(self.assets_dir, "characters", str(char_id))
        os.makedirs(char_dir, exist_ok=True)
        saved = []
        for i, src in enumerate(source_paths):
            ext = os.path.splitext(src)[1] or ".png"
            dest = os.path.join(char_dir, f"ref_{i}{ext}")
            shutil.copy2(src, dest)
            saved.append(dest)
        return saved

    def get_fal_urls(self, character) -> List[str]:
        """Parse JSON list of fal.ai URLs from character.fal_image_urls"""
        if not character.fal_image_urls:
            return []
        try:
            return json.loads(character.fal_image_urls)
        except (json.JSONDecodeError, TypeError):
            return []

    def build_kontext_prompt(self, character, scene_action: str, act: str) -> str:
        """Build FLUX Kontext prompt from character + scene action + act."""
        act_ctx = ACT_CONTEXT.get(act, ACT_CONTEXT["main"])
        char_desc = character.char_description or f"{character.name}, {character.personality or 'friendly mascot character'}"

        prompt = (
            f"Character: {char_desc}. "
            f"Scene: {scene_action}. "
            f"Setting: {act_ctx}. "
            f"Style: TikTok vertical video frame, 9:16 aspect ratio, "
            f"clean composition, character in foreground, "
            f"no text overlay, no watermark, no UI elements. "
            f"The character must match the reference images exactly."
        )
        return prompt

    def build_char_description(self, name: str, personality: str) -> str:
        """Generate short char_description from name + personality for prompt."""
        return f"{name} — {personality}" if personality else name
