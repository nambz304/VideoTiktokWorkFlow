import google.generativeai as genai
from typing import List
import re

SYSTEM_PROMPT = """Bạn là AI writer cho kênh TikTok "Sống khoẻ cùng AI" với robot mascot tên Milo.
Viết kịch bản ngắn 30-60 giây, phong cách vui nhộn + thông tin.
Cấu trúc: Hook mạnh (3-5 giây) → Nội dung chính → CTA affiliate tự nhiên.
"""

class ScriptGenerator:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(
            "gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT
        )

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
        response = self._model.generate_content(prompt)
        return self._parse_scripts(response.text)

    def _parse_scripts(self, raw: str) -> List[str]:
        parts = re.split(r'SCRIPT_\d+:', raw)
        return [p.strip() for p in parts if p.strip()]
