import anthropic
from typing import List
import re
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là AI writer cho kênh TikTok "Sống khoẻ cùng AI" với robot mascot tên Milo.
Viết kịch bản ngắn 30-60 giây, phong cách vui nhộn + thông tin.
Cấu trúc: Hook mạnh (3-5 giây) → Nội dung chính → CTA affiliate tự nhiên.
"""

class ScriptGenerator:
    def __init__(self, api_key: str):
        self._client = anthropic.Anthropic(api_key=api_key)

    def generate_scripts(
        self,
        topic: str,
        lang: str,
        channel_context: str,
        affiliate_category: str,
        count: int = 2
    ) -> List[str]:
        lang_instruction = "Viết bằng tiếng Việt." if lang == "vi" else "Write in English."
        prompt = f"""
{lang_instruction}
Chủ đề: {topic}
Context kênh: {channel_context}
Sản phẩm affiliate liên quan: {affiliate_category}

Tạo {count} kịch bản TikTok khác nhau về tone (vui nhộn vs thông tin), hook style, và cách đề xuất sản phẩm.
Format output:
SCRIPT_1:
[kịch bản 1]
SCRIPT_2:
[kịch bản 2]
"""
        try:
            response = self._client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_scripts(response.content[0].text)
        except Exception as e:
            logger.error(f"Claude script generation failed: {e}")
            raise

    def _parse_scripts(self, raw: str) -> List[str]:
        # Drop text before first SCRIPT_N: marker, then split on remaining markers
        match = re.search(r'SCRIPT_\d+:', raw)
        if not match:
            return [raw.strip()] if raw.strip() else []
        parts = re.split(r'SCRIPT_\d+:', raw[match.start():])
        return [p.strip() for p in parts if p.strip()]
