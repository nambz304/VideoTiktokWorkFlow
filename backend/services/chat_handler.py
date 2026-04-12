import google.generativeai as genai
from services.base_handler import BaseChatHandler, BASE_SYSTEM, STEP_CONTEXTS


class GeminiHandler(BaseChatHandler):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        if not api_key:
            raise ValueError("missing_key:google")
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model, system_instruction=BASE_SYSTEM)

    def chat(self, message: str, step: int, session_context: dict) -> str:
        step_ctx = STEP_CONTEXTS.get(step, "")
        context_str = f"Topic hiện tại: {session_context.get('topic', 'chưa có')}"
        prompt = f"{step_ctx}\n{context_str}\n\nUser: {message}"
        response = self._model.generate_content(prompt)
        return response.text
