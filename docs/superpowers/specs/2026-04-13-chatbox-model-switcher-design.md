# Chatbox Model Switcher

**Date:** 2026-04-13  
**Status:** Approved

## Overview

Add model-switching to the Milo AI chatbox. Users can select from Gemini, Claude, or OpenAI models via pill buttons above the textarea. Missing API keys trigger an inline key-input flow that writes the key to `.env` for long-term use.

---

## Backend

### New endpoint: `GET /chat/models`

Returns all supported models regardless of whether API keys are configured.

```json
["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash",
 "claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001",
 "gpt-4o", "gpt-4o-mini"]
```

### New endpoint: `POST /chat/keys`

Saves an API key to `.env` and updates `os.environ` in-memory (no restart needed).

**Request:**
```json
{ "provider": "anthropic", "key": "sk-ant-..." }
```

**Response:** `{ "ok": true }`

Provider values: `"google"`, `"anthropic"`, `"openai"`  
Env var mapping: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`

### Modified: `POST /chat`

Added `model` field (default: `"gemini-2.0-flash"`):

```json
{ "session_id": 1, "message": "hi", "step": 1, "model": "gemini-2.0-flash" }
```

**Error cases:**
- Missing key for provider → HTTP 401 `{ "detail": "missing_key:anthropic" }`
- Invalid model string → HTTP 400
- Quota exhausted → HTTP 429 with model name in message
- Invalid key → HTTP 401 `{ "detail": "invalid_key:openai" }`

### Handler architecture

```
backend/services/
  chat_handler.py      ← rename class to GeminiHandler, keep existing logic
  claude_handler.py    ← new, uses anthropic SDK
  openai_handler.py    ← new, uses openai SDK
  chat_factory.py      ← new, factory function
```

All handlers implement the same interface:

```python
class BaseChatHandler:
    def chat(self, message: str, step: int, session_context: dict) -> str: ...
```

**`chat_factory.py`:**

```python
def get_handler(model: str) -> BaseChatHandler:
    if model.startswith("gemini"):   return GeminiHandler(os.getenv("GEMINI_API_KEY", ""), model)
    elif model.startswith("claude"): return ClaudeHandler(os.getenv("ANTHROPIC_API_KEY", ""), model)
    else:                            return OpenAIHandler(os.getenv("OPENAI_API_KEY", ""), model)
```

If the key is empty string → raise `ValueError("missing_key:<provider>")` → router catches → HTTP 401.

---

## Frontend

### Model selector UI

Pill buttons rendered above the textarea, fetched from `GET /chat/models` on mount.

```
┌──────────────────────────────────────┐
│ [Flash 2.0] [Opus 4.6] [GPT-4o] ... │  ← selected pill highlighted blue
├──────────────────────────────────────┤
│ textarea...                    [→]   │
└──────────────────────────────────────┘
```

Display label mapping (shorten for compact UI):

| Model ID | Label |
|---|---|
| gemini-2.0-flash | Gemini Flash 2.0 |
| gemini-1.5-pro | Gemini Pro 1.5 |
| gemini-1.5-flash | Gemini Flash 1.5 |
| claude-opus-4-6 | Opus 4.6 |
| claude-sonnet-4-6 | Sonnet 4.6 |
| claude-haiku-4-5-20251001 | Haiku 4.5 |
| gpt-4o | GPT-4o |
| gpt-4o-mini | GPT-4o-mini |

### Missing key inline flow

When backend returns `401` with `missing_key:<provider>`, the chat area shows:

> "Model này chưa có API key. Config trong `.env` hoặc dán key vào đây:"
> `[input _______________] [Lưu]`

- User pastes key → `POST /chat/keys` → on success → auto-retry the failed message
- After save, input disappears, chat resumes normally

### `api.ts` changes

```ts
export const getAvailableModels = () =>
  req<string[]>("/chat/models");

export const saveApiKey = (provider: string, key: string) =>
  req<{ ok: boolean }>("/chat/keys", {
    method: "POST",
    body: JSON.stringify({ provider, key }),
  });

export const sendChat = (
  sessionId: number, message: string, step: number, model: string
) =>
  req<{ reply: string }>("/chat", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, message, step, model }),
  });
```

---

## Data flow

```
User selects model pill
  → selectedModel state update

User sends message
  → POST /chat { ..., model }
  → factory picks handler by model prefix
  → if key missing → 401 missing_key:<provider>
    → frontend shows inline key input
    → user pastes key → POST /chat/keys
    → backend writes .env + os.environ
    → frontend auto-retries POST /chat
  → if ok → reply shown in chat

App reload
  → key already in .env → works immediately
```

---

## Out of scope

- Persisting selected model across sessions
- Per-session model history
- Streaming responses
