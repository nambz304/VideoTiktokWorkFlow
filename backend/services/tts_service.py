import edge_tts
import asyncio
import os
import time
import logging

logger = logging.getLogger(__name__)

VOICES = {
    "vi": "vi-VN-NamMinhNeural",
    "en": "en-US-GuyNeural",
}

FALLBACK_VOICES = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-JennyNeural",
}


class TTSService:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def get_voice(self, lang: str) -> str:
        return VOICES.get(lang, VOICES["vi"])

    async def _try_generate(self, text: str, voice: str, output_path: str) -> bool:
        """Attempt TTS with given voice. Returns True if non-empty audio produced."""
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        return size > 0

    async def generate(self, text: str, lang: str, output_path: str) -> str:
        voice = self.get_voice(lang)
        fallback_voice = FALLBACK_VOICES.get(lang, voice)

        # First attempt
        try:
            success = await self._try_generate(text, voice, output_path)
            if success:
                return output_path
        except Exception as e:
            logger.warning(f"TTS attempt 1 failed ({voice}): {e}")

        # Small delay before retry
        await asyncio.sleep(1)

        # Retry with same voice
        try:
            success = await self._try_generate(text, voice, output_path)
            if success:
                logger.info(f"TTS succeeded on retry 2 ({voice})")
                return output_path
        except Exception as e:
            logger.warning(f"TTS attempt 2 failed ({voice}): {e}")

        # Fallback voice
        await asyncio.sleep(1)
        try:
            success = await self._try_generate(text, fallback_voice, output_path)
            if success:
                logger.info(f"TTS succeeded with fallback voice ({fallback_voice})")
                return output_path
        except Exception as e:
            logger.warning(f"TTS fallback failed ({fallback_voice}): {e}")

        raise RuntimeError(f"TTS failed for all voices. Text: {text[:80]}")

    def generate_sync(self, text: str, lang: str, output_path: str) -> str:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.generate(text, lang, output_path))
        finally:
            loop.close()
