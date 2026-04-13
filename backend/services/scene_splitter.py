import anthropic
import json, re
from typing import List
import logging

logger = logging.getLogger(__name__)

VALID_EMOTIONS = {"happy","wave","question","explain","recommend","cta","sleep","eat","exercise","surprise","think","point"}

class SceneSplitter:
    def __init__(self, api_key: str):
        self._client = anthropic.Anthropic(api_key=api_key)

    def split(self, script: str, lang: str = "vi") -> List[dict]:
        prompt = f"""Split this TikTok script into 3-8 scenes. Each scene is one visual moment.
For each scene, assign ONE emotion tag from: {', '.join(sorted(VALID_EMOTIONS))}

Return ONLY a JSON array, no explanation:
[{{"order": 1, "text": "scene text", "emotion": "tag"}}, ...]

Script:
{script}"""
        try:
            response = self._client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_scenes(response.content[0].text)
        except Exception as e:
            logger.error(f"Claude scene split failed: {e}")
            raise

    def _parse_scenes(self, raw: str) -> List[dict]:
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            return [{"order": 1, "text": raw.strip(), "emotion": "explain"}]
        try:
            scenes = json.loads(match.group())
            for scene in scenes:
                if scene.get("emotion") not in VALID_EMOTIONS:
                    scene["emotion"] = "explain"
            return scenes
        except json.JSONDecodeError:
            return [{"order": 1, "text": raw.strip(), "emotion": "explain"}]
