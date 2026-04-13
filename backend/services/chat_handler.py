import anthropic
from services.base_handler import BaseChatHandler, BASE_SYSTEM, STEP_CONTEXTS


class ClaudeHandler(BaseChatHandler):
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        if not api_key:
            raise ValueError("missing_key:anthropic")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def chat(self, message: str, step: int, session_context: dict) -> str:
        step_ctx = STEP_CONTEXTS.get(step, "")
        context_str = f"Topic hiện tại: {session_context.get('topic', 'chưa có')}"
        prompt = f"{step_ctx}\n{context_str}\n\nUser: {message}"
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=BASE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
