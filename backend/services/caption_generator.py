import google.generativeai as genai
import re
import logging

logger = logging.getLogger(__name__)


class CaptionGenerator:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("gemini-2.0-flash")

    def generate(self, script: str, topic: str, lang: str) -> dict:
        lang_note = "Tiếng Việt" if lang == "vi" else "English"
        prompt = f"""Create a TikTok caption and hashtags for this video.
Language: {lang_note}
Topic: {topic}

Script summary:
{script[:500]}

Output format (exact):
CAPTION:
[1-2 sentences, engaging, emoji OK]

HASHTAGS:
#tag1 #tag2 #tag3 ... (10-15 hashtags, mix trending + niche)
"""
        try:
            response = self._model.generate_content(prompt)
            return self._parse(response.text)
        except Exception as e:
            logger.error(f"Gemini caption generation failed: {e}")
            raise

    def _parse(self, raw: str) -> dict:
        caption_match = re.search(r"CAPTION:\n(.*?)(?:\n\nHASHTAGS:|\Z)", raw, re.DOTALL)
        hashtag_match = re.search(r"HASHTAGS:\n(.*)", raw, re.DOTALL)
        caption = caption_match.group(1).strip() if caption_match else raw.strip()
        hashtag_str = hashtag_match.group(1).strip() if hashtag_match else ""
        hashtags = re.findall(r"#\w+", hashtag_str)
        return {"caption": caption, "hashtags": hashtags}
