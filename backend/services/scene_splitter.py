import anthropic
import json
import re
import logging
from typing import List

logger = logging.getLogger(__name__)

VALID_EMOTIONS = {
    "happy", "wave", "question", "explain", "recommend",
    "cta", "sleep", "eat", "exercise", "surprise", "think", "point"
}

VALID_ACTS = {"hook", "main", "cta"}


class SceneSplitter:
    def __init__(self, api_key: str):
        self._client = anthropic.Anthropic(api_key=api_key)

    def split(self, script: str, lang: str = "vi") -> List[dict]:
        prompt = f"""Bạn là chuyên gia phân tích kịch bản TikTok. Phân tích kịch bản sau thành 3-6 phân cảnh.

Quy tắc phân act:
- Cảnh đầu tiên: act = "hook" (gây chú ý, mở đầu)
- Các cảnh giữa: act = "main" (nội dung chính)
- Cảnh cuối (1-2 cảnh): act = "cta" (kêu gọi hành động, follow)

Với mỗi cảnh, extract:
- action: mô tả hành động, cử chỉ, biểu cảm của nhân vật (dùng làm prompt gen ảnh)
- dialogue: CHÍNH XÁC lời nhân vật nói (text trong ngoặc kép hoặc sau dấu ':') — dùng cho TTS đọc
- emotion: 1 trong {', '.join(sorted(VALID_EMOTIONS))}

Nếu không có lời thoại rõ ràng, dialogue = action text.

Trả về CHỈ JSON array, không giải thích:
[{{"order": 1, "act": "hook", "action": "...", "dialogue": "...", "emotion": "..."}}]

Kịch bản:
{script}"""

        try:
            response = self._client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_scenes(response.content[0].text, script)
        except Exception as e:
            logger.error(f"SceneSplitter failed: {e}")
            raise

    def _parse_scenes(self, raw: str, original_script: str) -> List[dict]:
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            return [self._fallback_scene(original_script)]
        try:
            scenes = json.loads(match.group())
            return [self._validate_scene(s) for s in scenes]
        except json.JSONDecodeError:
            return [self._fallback_scene(original_script)]

    def _validate_scene(self, scene: dict) -> dict:
        if scene.get("emotion") not in VALID_EMOTIONS:
            scene["emotion"] = "explain"
        if scene.get("act") not in VALID_ACTS:
            scene["act"] = "main"
        # Fallback: dialogue → action if null/empty
        if not scene.get("dialogue"):
            scene["dialogue"] = scene.get("action", "")
        return scene

    def _fallback_scene(self, script: str) -> dict:
        return {
            "order": 1,
            "act": "hook",
            "action": script.strip()[:200],
            "dialogue": script.strip()[:200],
            "emotion": "explain",
        }
