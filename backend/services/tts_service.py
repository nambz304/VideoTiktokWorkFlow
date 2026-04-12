import edge_tts
import asyncio
import os

VOICES = {
    "vi": "vi-VN-NamMinhNeural",
    "en": "en-US-GuyNeural",
}

class TTSService:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def get_voice(self, lang: str) -> str:
        return VOICES.get(lang, VOICES["vi"])

    async def generate(self, text: str, lang: str, output_path: str) -> str:
        voice = self.get_voice(lang)
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return output_path

    def generate_sync(self, text: str, lang: str, output_path: str) -> str:
        return asyncio.run(self.generate(text, lang, output_path))
