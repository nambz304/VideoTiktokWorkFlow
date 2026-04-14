# Chatbox Model Switcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add model-switching to the Milo AI chatbox — pill buttons above textarea, all Gemini/Claude/OpenAI models always shown, missing keys trigger inline key-save flow.

**Architecture:** Separate handler class per provider (`GeminiHandler`, `ClaudeHandler`, `OpenAIHandler`) all extending `BaseChatHandler`. A factory `get_handler(model)` routes by model prefix. Backend exposes `/chat/models` and `/chat/keys`. Frontend fetches models on mount, renders pill buttons, handles missing-key 401 inline.

**Tech Stack:** FastAPI, google-generativeai, anthropic SDK, openai SDK, python-dotenv `set_key`, Next.js 16, React, TypeScript

---

## File Map

**Create:**
- `backend/services/base_handler.py` — `BaseChatHandler` ABC + `BASE_SYSTEM` + `STEP_CONTEXTS`
- `backend/services/claude_handler.py` — `ClaudeHandler(BaseChatHandler)`
- `backend/services/openai_handler.py` — `OpenAIHandler(BaseChatHandler)`
- `backend/services/chat_factory.py` — `get_handler()` + `SUPPORTED_MODELS`
- `backend/tests/test_claude_handler.py`
- `backend/tests/test_openai_handler.py`
- `backend/tests/test_chat_factory.py`

**Modify:**
- `backend/requirements.txt` — add `anthropic`, `openai`
- `backend/services/chat_handler.py` — rename `ChatHandler` → `GeminiHandler`, extend `BaseChatHandler`, add `model` param, raise on empty key
- `backend/tests/test_chat_handler.py` — update import/class name
- `backend/routers/chat.py` — add `GET /chat/models`, `POST /chat/keys`, update `POST /chat`
- `frontend/lib/api.ts` — add `getAvailableModels`, `saveApiKey`, update `sendChat`
- `frontend/components/ChatSidebar.tsx` — model pills, key-input flow

---

## Task 1: Add backend dependencies

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add packages**

Edit `backend/requirements.txt` — append these two lines:
```
anthropic>=0.40.0
openai>=1.50.0
```

- [ ] **Step 2: Install**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/backend
/Users/catcomputer/ai-env/bin/pip install anthropic openai
```

Expected: both packages install successfully, no errors.

- [ ] **Step 3: Verify**

```bash
/Users/catcomputer/ai-env/bin/python -c "import anthropic; import openai; print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add anthropic and openai dependencies"
```

---

## Task 2: Create `base_handler.py`

**Files:**
- Create: `backend/services/base_handler.py`

- [ ] **Step 1: Write the file**

Create `backend/services/base_handler.py`:

```python
from abc import ABC, abstractmethod

BASE_SYSTEM = """Bạn là Milo — AI assistant cho kênh TikTok "Sống khoẻ cùng AI".
Trả lời ngắn gọn, thân thiện. Nếu user yêu cầu thay đổi, mô tả rõ action cần thực hiện.
Không tự thực hiện thay đổi — chỉ hướng dẫn hoặc confirm."""

STEP_CONTEXTS = {
    1: "User đang ở Bước 1: Trend research và tạo kịch bản. Hỗ trợ chọn topic, chỉnh sửa kịch bản.",
    2: "User đang ở Bước 2: Phân cảnh. Hỗ trợ split/merge/reorder/edit scenes.",
    3: "User đang ở Bước 3: Chọn ảnh Milo. Hỗ trợ swap ảnh, giải thích tại sao chọn ảnh đó.",
    4: "User đang ở Bước 4: Tạo video từng cảnh. Hỗ trợ redo scene, điều chỉnh TTS.",
    5: "User đang ở Bước 5: Ghép video + caption. Hỗ trợ edit caption, hashtag, BGM.",
    6: "User đang ở Bước 6: Lên lịch đăng. Hỗ trợ set giờ đăng, cuối cùng trước khi publish.",
}


class BaseChatHandler(ABC):
    @abstractmethod
    def chat(self, message: str, step: int, session_context: dict) -> str: ...
```

- [ ] **Step 2: Commit**

```bash
git add backend/services/base_handler.py
git commit -m "feat: add BaseChatHandler ABC with shared prompts"
```

---

## Task 3: Refactor `GeminiHandler`

**Files:**
- Modify: `backend/services/chat_handler.py`
- Modify: `backend/tests/test_chat_handler.py`

- [ ] **Step 1: Write failing test**

Replace `backend/tests/test_chat_handler.py` with:

```python
from unittest.mock import patch, MagicMock
from services.chat_handler import GeminiHandler


def test_chat_returns_text():
    handler = GeminiHandler(api_key="fake")
    mock_resp = MagicMock()
    mock_resp.text = "Tôi sẽ đổi ảnh cảnh 2 cho bạn."
    with patch.object(handler._model, "generate_content", return_value=mock_resp):
        result = handler.chat(
            message="đổi ảnh cảnh 2 sang milo_happy",
            step=3,
            session_context={"topic": "Ngủ ngon", "step": 3},
        )
        assert isinstance(result, str)
        assert len(result) > 0


def test_chat_includes_step_context():
    handler = GeminiHandler(api_key="fake")
    captured_prompt = []
    mock_resp = MagicMock()
    mock_resp.text = "OK"

    def side_effect(p):
        captured_prompt.append(p)
        return mock_resp

    with patch.object(handler._model, "generate_content", side_effect=side_effect):
        handler.chat(message="help", step=3, session_context={})
        assert any("ước 3" in str(p) for p in captured_prompt)


def test_missing_key_raises():
    import pytest
    with pytest.raises(ValueError, match="missing_key:google"):
        GeminiHandler(api_key="")


def test_custom_model():
    handler = GeminiHandler(api_key="fake", model="gemini-1.5-pro")
    assert "1.5-pro" in handler._model.model_name
```

- [ ] **Step 2: Run to verify fails**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/backend
/Users/catcomputer/ai-env/bin/pytest tests/test_chat_handler.py -v
```

Expected: FAIL — `ImportError: cannot import name 'GeminiHandler'`

- [ ] **Step 3: Rewrite `chat_handler.py`**

Replace `backend/services/chat_handler.py` with:

```python
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
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/backend
/Users/catcomputer/ai-env/bin/pytest tests/test_chat_handler.py -v
```

Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/chat_handler.py backend/tests/test_chat_handler.py
git commit -m "refactor: rename ChatHandler to GeminiHandler, extend BaseChatHandler"
```

---

## Task 4: Create `ClaudeHandler`

**Files:**
- Create: `backend/services/claude_handler.py`
- Create: `backend/tests/test_claude_handler.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_claude_handler.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from services.claude_handler import ClaudeHandler


def test_missing_key_raises():
    with pytest.raises(ValueError, match="missing_key:anthropic"):
        ClaudeHandler(api_key="")


def test_chat_returns_text():
    handler = ClaudeHandler(api_key="fake")
    mock_content = MagicMock()
    mock_content.text = "Xin chào!"
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    with patch.object(handler._client.messages, "create", return_value=mock_response):
        result = handler.chat(
            message="hi",
            step=1,
            session_context={"topic": "test"},
        )
        assert result == "Xin chào!"


def test_chat_passes_system_prompt():
    handler = ClaudeHandler(api_key="fake")
    calls = []
    mock_content = MagicMock()
    mock_content.text = "OK"
    mock_response = MagicMock()
    mock_response.content = [mock_content]

    def capture(**kwargs):
        calls.append(kwargs)
        return mock_response

    with patch.object(handler._client.messages, "create", side_effect=capture):
        handler.chat(message="test", step=2, session_context={})
        assert calls[0]["system"] is not None
        assert "Milo" in calls[0]["system"]
```

- [ ] **Step 2: Run to verify fails**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/backend
/Users/catcomputer/ai-env/bin/pytest tests/test_claude_handler.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'services.claude_handler'`

- [ ] **Step 3: Implement `claude_handler.py`**

Create `backend/services/claude_handler.py`:

```python
import anthropic
from services.base_handler import BaseChatHandler, BASE_SYSTEM, STEP_CONTEXTS


class ClaudeHandler(BaseChatHandler):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
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
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/backend
/Users/catcomputer/ai-env/bin/pytest tests/test_claude_handler.py -v
```

Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/claude_handler.py backend/tests/test_claude_handler.py
git commit -m "feat: add ClaudeHandler"
```

---

## Task 5: Create `OpenAIHandler`

**Files:**
- Create: `backend/services/openai_handler.py`
- Create: `backend/tests/test_openai_handler.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_openai_handler.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from services.openai_handler import OpenAIHandler


def test_missing_key_raises():
    with pytest.raises(ValueError, match="missing_key:openai"):
        OpenAIHandler(api_key="")


def test_chat_returns_text():
    handler = OpenAIHandler(api_key="fake")
    mock_message = MagicMock()
    mock_message.content = "Xin chào!"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    with patch.object(handler._client.chat.completions, "create", return_value=mock_response):
        result = handler.chat(
            message="hi",
            step=1,
            session_context={"topic": "test"},
        )
        assert result == "Xin chào!"


def test_chat_passes_system_message():
    handler = OpenAIHandler(api_key="fake")
    calls = []
    mock_message = MagicMock()
    mock_message.content = "OK"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    def capture(**kwargs):
        calls.append(kwargs)
        return mock_response

    with patch.object(handler._client.chat.completions, "create", side_effect=capture):
        handler.chat(message="test", step=2, session_context={})
        system_msgs = [m for m in calls[0]["messages"] if m["role"] == "system"]
        assert len(system_msgs) == 1
        assert "Milo" in system_msgs[0]["content"]
```

- [ ] **Step 2: Run to verify fails**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/backend
/Users/catcomputer/ai-env/bin/pytest tests/test_openai_handler.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'services.openai_handler'`

- [ ] **Step 3: Implement `openai_handler.py`**

Create `backend/services/openai_handler.py`:

```python
from openai import OpenAI
from services.base_handler import BaseChatHandler, BASE_SYSTEM, STEP_CONTEXTS


class OpenAIHandler(BaseChatHandler):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        if not api_key:
            raise ValueError("missing_key:openai")
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def chat(self, message: str, step: int, session_context: dict) -> str:
        step_ctx = STEP_CONTEXTS.get(step, "")
        context_str = f"Topic hiện tại: {session_context.get('topic', 'chưa có')}"
        prompt = f"{step_ctx}\n{context_str}\n\nUser: {message}"
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": BASE_SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/backend
/Users/catcomputer/ai-env/bin/pytest tests/test_openai_handler.py -v
```

Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/openai_handler.py backend/tests/test_openai_handler.py
git commit -m "feat: add OpenAIHandler"
```

---

## Task 6: Create `chat_factory.py`

**Files:**
- Create: `backend/services/chat_factory.py`
- Create: `backend/tests/test_chat_factory.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_chat_factory.py`:

```python
import pytest
from unittest.mock import patch
from services.chat_factory import get_handler, SUPPORTED_MODELS
from services.chat_handler import GeminiHandler
from services.claude_handler import ClaudeHandler
from services.openai_handler import OpenAIHandler


def test_supported_models_list():
    assert "gemini-2.0-flash" in SUPPORTED_MODELS
    assert "claude-opus-4-6" in SUPPORTED_MODELS
    assert "gpt-4o" in SUPPORTED_MODELS
    assert len(SUPPORTED_MODELS) == 8


def test_get_handler_gemini():
    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake"}):
        handler = get_handler("gemini-2.0-flash")
        assert isinstance(handler, GeminiHandler)


def test_get_handler_claude():
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "fake"}):
        handler = get_handler("claude-opus-4-6")
        assert isinstance(handler, ClaudeHandler)


def test_get_handler_openai():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "fake"}):
        handler = get_handler("gpt-4o")
        assert isinstance(handler, OpenAIHandler)


def test_unsupported_model_raises():
    with pytest.raises(ValueError, match="unsupported_model"):
        get_handler("unknown-model-xyz")


def test_missing_gemini_key_raises():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="missing_key:google"):
            get_handler("gemini-2.0-flash")


def test_missing_anthropic_key_raises():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="missing_key:anthropic"):
            get_handler("claude-sonnet-4-6")


def test_missing_openai_key_raises():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="missing_key:openai"):
            get_handler("gpt-4o-mini")
```

- [ ] **Step 2: Run to verify fails**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/backend
/Users/catcomputer/ai-env/bin/pytest tests/test_chat_factory.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'services.chat_factory'`

- [ ] **Step 3: Implement `chat_factory.py`**

Create `backend/services/chat_factory.py`:

```python
import os
from services.base_handler import BaseChatHandler
from services.chat_handler import GeminiHandler
from services.claude_handler import ClaudeHandler
from services.openai_handler import OpenAIHandler

SUPPORTED_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
    "gpt-4o",
    "gpt-4o-mini",
]


def get_handler(model: str) -> BaseChatHandler:
    if model not in SUPPORTED_MODELS:
        raise ValueError(f"unsupported_model:{model}")
    if model.startswith("gemini"):
        return GeminiHandler(api_key=os.getenv("GEMINI_API_KEY", ""), model=model)
    elif model.startswith("claude"):
        return ClaudeHandler(api_key=os.getenv("ANTHROPIC_API_KEY", ""), model=model)
    else:
        return OpenAIHandler(api_key=os.getenv("OPENAI_API_KEY", ""), model=model)
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/backend
/Users/catcomputer/ai-env/bin/pytest tests/test_chat_factory.py -v
```

Expected: 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/chat_factory.py backend/tests/test_chat_factory.py
git commit -m "feat: add chat_factory with multi-provider routing"
```

---

## Task 7: Update `routers/chat.py`

**Files:**
- Modify: `backend/routers/chat.py`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_pipeline_router.py` — actually create a new file `backend/tests/test_chat_router.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_models():
    resp = client.get("/chat/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "gemini-2.0-flash" in data
    assert "claude-opus-4-6" in data
    assert "gpt-4o" in data
    assert len(data) == 8


def test_save_key_unknown_provider():
    resp = client.post("/chat/keys", json={"provider": "unknown", "key": "abc"})
    assert resp.status_code == 400


def test_save_key_empty_key():
    resp = client.post("/chat/keys", json={"provider": "anthropic", "key": ""})
    assert resp.status_code == 400


def test_chat_missing_key_returns_401():
    with patch("routers.chat.get_handler", side_effect=ValueError("missing_key:anthropic")):
        resp = client.post("/chat", json={
            "session_id": None, "message": "hi", "step": 1, "model": "claude-sonnet-4-6"
        })
        assert resp.status_code == 401
        assert "missing_key:anthropic" in resp.json()["detail"]


def test_chat_unsupported_model_returns_400():
    with patch("routers.chat.get_handler", side_effect=ValueError("unsupported_model:xyz")):
        resp = client.post("/chat", json={
            "session_id": None, "message": "hi", "step": 1, "model": "xyz"
        })
        assert resp.status_code == 400


def test_chat_returns_reply():
    mock_handler = MagicMock()
    mock_handler.chat.return_value = "Xin chào!"
    with patch("routers.chat.get_handler", return_value=mock_handler):
        resp = client.post("/chat", json={
            "session_id": None, "message": "hi", "step": 1, "model": "gemini-2.0-flash"
        })
        assert resp.status_code == 200
        assert resp.json()["reply"] == "Xin chào!"
```

- [ ] **Step 2: Run to verify fails**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/backend
/Users/catcomputer/ai-env/bin/pytest tests/test_chat_router.py -v
```

Expected: FAIL — `404` on `/chat/models`, `AttributeError` on `get_handler` import

- [ ] **Step 3: Rewrite `routers/chat.py`**

Replace `backend/routers/chat.py` with:

```python
import os
import pathlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from dotenv import set_key
from google.api_core.exceptions import ResourceExhausted
from database import get_db
from models import SessionModel
from services.chat_factory import get_handler, SUPPORTED_MODELS

router = APIRouter()

_ENV_PATH = str(pathlib.Path(__file__).parent.parent / ".env")

_PROVIDER_ENV_MAP = {
    "google": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}


@router.get("/models")
def list_models():
    return SUPPORTED_MODELS


@router.post("/keys")
def save_key(body: dict):
    provider = body.get("provider", "")
    key = body.get("key", "").strip()
    if provider not in _PROVIDER_ENV_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    if not key:
        raise HTTPException(status_code=400, detail="Key cannot be empty")
    env_var = _PROVIDER_ENV_MAP[provider]
    set_key(_ENV_PATH, env_var, key)
    os.environ[env_var] = key
    return {"ok": True}


@router.post("")
def chat(body: dict, db: DBSession = Depends(get_db)):
    session_id = body.get("session_id")
    message = body.get("message", "")
    step = body.get("step", 1)
    model = body.get("model", "gemini-2.0-flash")
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    session_context = {"topic": session.topic if session else None, "step": step}
    try:
        handler = get_handler(model)
        reply = handler.chat(message=message, step=step, session_context=session_context)
    except ValueError as e:
        err = str(e)
        if err.startswith("missing_key:"):
            raise HTTPException(status_code=401, detail=err)
        if err.startswith("unsupported_model:"):
            raise HTTPException(status_code=400, detail=err)
        raise HTTPException(status_code=500, detail=err)
    except ResourceExhausted:
        raise HTTPException(status_code=429, detail=f"{model}: Gemini API quota exhausted. Upgrade plan or wait.")
    except Exception as e:
        err_str = str(e).lower()
        if "authentication" in err_str or "api_key" in err_str or "unauthorized" in err_str or "incorrect api key" in err_str:
            provider = "anthropic" if model.startswith("claude") else "openai"
            raise HTTPException(status_code=401, detail=f"invalid_key:{provider}")
        raise
    return {"reply": reply}
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/backend
/Users/catcomputer/ai-env/bin/pytest tests/test_chat_router.py -v
```

Expected: 6 tests PASS

- [ ] **Step 5: Run all backend tests**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/backend
/Users/catcomputer/ai-env/bin/pytest --tb=short -q
```

Expected: all existing tests still pass

- [ ] **Step 6: Commit**

```bash
git add backend/routers/chat.py backend/tests/test_chat_router.py
git commit -m "feat: add /chat/models and /chat/keys endpoints, multi-model support in /chat"
```

---

## Task 8: Update `frontend/lib/api.ts`

**Files:**
- Modify: `frontend/lib/api.ts`

- [ ] **Step 1: Update `api.ts`**

Replace the `// Chat` section at the bottom of `frontend/lib/api.ts`:

```ts
// Chat
export const getAvailableModels = () =>
  req<string[]>("/chat/models");

export const saveApiKey = (provider: string, key: string) =>
  req<{ ok: boolean }>("/chat/keys", {
    method: "POST",
    body: JSON.stringify({ provider, key }),
  });

export const sendChat = (
  sessionId: number,
  message: string,
  step: number,
  model: string,
) =>
  req<{ reply: string }>("/chat", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, message, step, model }),
  });
```

- [ ] **Step 2: Commit**

```bash
git add frontend/lib/api.ts
git commit -m "feat: add getAvailableModels, saveApiKey; update sendChat signature"
```

---

## Task 9: Update `ChatSidebar.tsx`

**Files:**
- Modify: `frontend/components/ChatSidebar.tsx`

- [ ] **Step 1: Replace `ChatSidebar.tsx`**

Replace `frontend/components/ChatSidebar.tsx` with:

```tsx
"use client";
import { useState, useRef, useEffect } from "react";
import { sendChat, getAvailableModels, saveApiKey } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

interface ChatSidebarProps {
  sessionId: number;
  step: number;
}

const MODEL_LABELS: Record<string, string> = {
  "gemini-2.0-flash": "Gemini Flash 2.0",
  "gemini-1.5-pro": "Gemini Pro 1.5",
  "gemini-1.5-flash": "Gemini Flash 1.5",
  "claude-opus-4-6": "Opus 4.6",
  "claude-sonnet-4-6": "Sonnet 4.6",
  "claude-haiku-4-5-20251001": "Haiku 4.5",
  "gpt-4o": "GPT-4o",
  "gpt-4o-mini": "GPT-4o-mini",
};

function providerFromModel(model: string): string {
  if (model.startsWith("gemini")) return "google";
  if (model.startsWith("claude")) return "anthropic";
  return "openai";
}

export default function ChatSidebar({ sessionId, step }: ChatSidebarProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "ai", text: "Xin chào! Tôi là Milo. Bạn cần hỗ trợ gì không?", timestamp: Date.now() },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState("gemini-2.0-flash");
  const [missingKeyProvider, setMissingKeyProvider] = useState<string | null>(null);
  const [keyInput, setKeyInput] = useState("");
  const [pendingMessage, setPendingMessage] = useState<{ text: string; model: string } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getAvailableModels().then((list) => {
      setModels(list);
      if (list.length > 0) setSelectedModel(list[0]);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, missingKeyProvider]);

  async function doSend(text: string, model: string) {
    setMessages((prev) => [...prev, { role: "user", text, timestamp: Date.now() }]);
    setLoading(true);
    try {
      const { reply } = await sendChat(sessionId, text, step, model);
      setMessages((prev) => [...prev, { role: "ai", text: reply, timestamp: Date.now() }]);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "";
      if (errMsg.includes("401")) {
        const match = errMsg.match(/missing_key:(\w+)/);
        if (match) {
          setPendingMessage({ text, model });
          setMissingKeyProvider(match[1]);
          return;
        }
        setMessages((prev) => [...prev, { role: "ai", text: "API key không hợp lệ.", timestamp: Date.now() }]);
      } else if (errMsg.includes("429")) {
        setMessages((prev) => [...prev, { role: "ai", text: `${model}: hết quota. Nâng cấp plan hoặc thử lại sau.`, timestamp: Date.now() }]);
      } else {
        setMessages((prev) => [...prev, { role: "ai", text: "Lỗi kết nối, thử lại nhé.", timestamp: Date.now() }]);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    await doSend(text, selectedModel);
  }

  async function handleSaveKey() {
    if (!missingKeyProvider || !keyInput.trim()) return;
    try {
      await saveApiKey(missingKeyProvider, keyInput.trim());
      setMissingKeyProvider(null);
      setKeyInput("");
      if (pendingMessage) {
        const { text, model } = pendingMessage;
        setPendingMessage(null);
        await doSend(text, model);
      }
    } catch {
      setMessages((prev) => [...prev, { role: "ai", text: "Lưu key thất bại, thử lại.", timestamp: Date.now() }]);
    }
  }

  return (
    <div className="w-72 bg-gray-950 border-l border-gray-800 flex flex-col flex-shrink-0">
      <div className="px-4 py-3 border-b border-gray-800 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-sm font-semibold text-emerald-400">Milo AI</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[90%] px-3 py-2 rounded-xl text-xs leading-relaxed
                ${msg.role === "user"
                  ? "bg-blue-700 text-blue-100 rounded-br-sm"
                  : "bg-gray-800 text-gray-300 rounded-bl-sm"
                }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 px-3 py-2 rounded-xl text-xs text-gray-400">...</div>
          </div>
        )}
        {missingKeyProvider && (
          <div className="bg-yellow-900/40 border border-yellow-700/50 rounded-xl px-3 py-2 text-xs text-yellow-200">
            <p className="mb-2">Model này chưa có API key. Config trong <code className="text-yellow-400">.env</code> hoặc dán key vào đây:</p>
            <div className="flex gap-1">
              <input
                type="password"
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") handleSaveKey(); }}
                placeholder="Dán API key..."
                className="flex-1 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-xs text-gray-200 outline-none focus:border-yellow-500"
              />
              <button
                onClick={handleSaveKey}
                disabled={!keyInput.trim()}
                className="px-2 py-1 bg-yellow-600 hover:bg-yellow-500 disabled:opacity-30 rounded text-xs text-white"
              >
                Lưu
              </button>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="p-3 border-t border-gray-800">
        {models.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {models.map((m) => (
              <button
                key={m}
                onClick={() => setSelectedModel(m)}
                className={`px-2 py-0.5 rounded-full text-[10px] border transition-colors
                  ${selectedModel === m
                    ? "bg-blue-700 border-blue-600 text-white"
                    : "bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500"
                  }`}
              >
                {MODEL_LABELS[m] ?? m}
              </button>
            ))}
          </div>
        )}
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="Ra lệnh hoặc hỏi Milo..."
            rows={2}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-200
              placeholder-gray-500 outline-none focus:border-blue-500 resize-none"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="w-8 h-8 bg-blue-700 rounded-lg flex items-center justify-center flex-shrink-0
              hover:bg-blue-600 disabled:opacity-30 transition-all self-end"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        <p className="text-xs text-gray-600 mt-1.5">VD: &quot;làm lại cảnh 2&quot; · &quot;đổi hashtag&quot;</p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify frontend compiles**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/frontend
npm run build 2>&1 | tail -20
```

Expected: build completes with no TypeScript errors

- [ ] **Step 3: Commit**

```bash
git add frontend/components/ChatSidebar.tsx
git commit -m "feat: add model selector pills and inline API key flow to ChatSidebar"
```

---

## Task 10: Smoke test

- [ ] **Step 1: Run all backend tests**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam/backend
/Users/catcomputer/ai-env/bin/pytest --tb=short -q
```

Expected: all tests pass

- [ ] **Step 2: Start app**

```bash
cd /Users/catcomputer/Documents/Programs/AI/big_project/tiktokTeam
make dev
```

- [ ] **Step 3: Verify `/chat/models`**

```bash
curl http://localhost:8000/chat/models
```

Expected: `["gemini-2.0-flash","gemini-1.5-pro","gemini-1.5-flash","claude-opus-4-6","claude-sonnet-4-6","claude-haiku-4-5-20251001","gpt-4o","gpt-4o-mini"]`

- [ ] **Step 4: Manual UI check**

Open `http://localhost:3000`, open a session → verify:
1. 8 model pill buttons appear above textarea
2. Click a pill → it highlights blue
3. Send a message with Gemini Flash 2.0 → reply appears (or quota error with model name)
4. Click a model without a key (e.g., Opus 4.6 if no `ANTHROPIC_API_KEY`) → yellow key-input box appears
5. Paste a valid key → "Lưu" → key saved, message auto-retries
