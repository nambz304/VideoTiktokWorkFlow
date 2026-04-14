# Audio + SceneSplitter Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix audio quality (TTS chỉ đọc lời thoại Milo) và nâng cấp SceneSplitter output schema để chuẩn bị cho Kontext image gen.

**Architecture:** Upgrade SceneSplitter từ Haiku→Sonnet với prompt mới trả về `{act, action, dialogue, emotion}`. Pipeline step 4 dùng `scene.dialogue` cho TTS thay vì `scene.script_text`. DB thêm 3 columns mới vào `scenes`.

**Tech Stack:** Python, SQLAlchemy, FastAPI, `anthropic` SDK (`claude-sonnet-4-6`), `edge_tts`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/models.py` | Modify | Thêm `act`, `action`, `dialogue` vào `SceneModel` |
| `backend/services/scene_splitter.py` | Modify | Sonnet model + prompt mới + parse schema mới |
| `backend/routers/pipeline.py` | Modify | Step 2 lưu fields mới, Step 4 TTS dùng `dialogue` |
| `backend/tests/test_scene_splitter.py` | Modify | Update tests cho schema mới |

---

## Task 1: Thêm columns mới vào SceneModel

**Files:**
- Modify: `backend/models.py`

- [ ] **Step 1: Đọc models.py hiện tại**

Mở `backend/models.py`, tìm `SceneModel`. Hiện tại có các fields: `id`, `session_id`, `order`, `script_text`, `emotion_tag`, `image_path`, `audio_path`, `video_path`.

- [ ] **Step 2: Thêm 3 columns mới**

Thêm sau field `emotion_tag`:

```python
act = Column(String, nullable=True)        # "hook" | "main" | "cta"
action = Column(Text, nullable=True)       # mô tả hành động Milo
dialogue = Column(Text, nullable=True)     # lời thoại Milo → dùng cho TTS
```

- [ ] **Step 3: Recreate DB**

```bash
cd backend
python -c "from database import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"
```

Expected output: không có error. File `milo_studio.db` được recreate.

- [ ] **Step 4: Verify schema**

```bash
python -c "
from database import engine
from sqlalchemy import inspect
cols = [c['name'] for c in inspect(engine).get_columns('scenes')]
print(cols)
assert 'act' in cols
assert 'action' in cols
assert 'dialogue' in cols
print('OK')
"
```

Expected: `['id', 'session_id', 'order', 'script_text', 'emotion_tag', 'image_path', 'audio_path', 'video_path', 'act', 'action', 'dialogue']` và `OK`.

- [ ] **Step 5: Commit**

```bash
git add backend/models.py
git commit -m "feat: add act/action/dialogue columns to SceneModel"
```

---

## Task 2: Upgrade SceneSplitter — Sonnet + schema mới

**Files:**
- Modify: `backend/services/scene_splitter.py`
- Modify: `backend/tests/test_scene_splitter.py`

- [ ] **Step 1: Viết failing tests trước**

Thay toàn bộ nội dung `backend/tests/test_scene_splitter.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from services.scene_splitter import SceneSplitter

SAMPLE_SCRIPT = """
Milo vào màn hình với điệu nhảy hài hước, làm mặt hoảng sợ và vuốt tay: 'Ê! Bạn đã Follow chưa? Không? Thì Milo cho bạn lý do để Follow ngay đây!'
Milo cầm một viên vitamin to xác: 'Hàng ngày mình ăn cơm, bạn ăn gì để sống khoẻ?'
Milo chỉ vào chiếc vòng đo nhịp tim: 'Này, máy đo nhịp tim này biết bạn sống còn hay không!'
Milo cười ha hả, nhảy nhót: 'Follow Milo ngay để không bỏ lỡ bí kíp sống khoẻ nhé!'
"""

MOCK_RESPONSE = """
[
  {"order": 1, "act": "hook", "action": "Milo nhảy vào màn hình, làm mặt hoảng sợ", "dialogue": "Ê! Bạn đã Follow chưa? Thì Milo cho bạn lý do ngay đây!", "emotion": "surprise"},
  {"order": 2, "act": "main", "action": "Milo cầm viên vitamin to xác", "dialogue": "Hàng ngày mình ăn cơm, bạn ăn gì để sống khoẻ?", "emotion": "recommend"},
  {"order": 3, "act": "main", "action": "Milo chỉ vào vòng đo nhịp tim", "dialogue": "Máy đo nhịp tim này biết bạn sống còn hay không!", "emotion": "point"},
  {"order": 4, "act": "cta", "action": "Milo cười nhảy nhót", "dialogue": "Follow Milo ngay để không bỏ lỡ bí kíp sống khoẻ nhé!", "emotion": "cta"}
]
"""


def make_splitter():
    return SceneSplitter(api_key="test-key")


def mock_response(text):
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


# --- Schema tests ---

def test_split_returns_list(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    assert isinstance(scenes, list)
    assert len(scenes) == 4


def test_scene_has_required_fields(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    for scene in scenes:
        assert "order" in scene
        assert "act" in scene
        assert "action" in scene
        assert "dialogue" in scene
        assert "emotion" in scene


def test_act_values_valid(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    valid_acts = {"hook", "main", "cta"}
    for scene in scenes:
        assert scene["act"] in valid_acts, f"Invalid act: {scene['act']}"


def test_first_scene_is_hook(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    assert scenes[0]["act"] == "hook"


def test_last_scene_is_cta(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    assert scenes[-1]["act"] == "cta"


def test_dialogue_not_empty(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    for scene in scenes:
        assert scene["dialogue"] and len(scene["dialogue"]) > 0


def test_emotion_valid(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(MOCK_RESPONSE))
    scenes = splitter.split(SAMPLE_SCRIPT)
    valid = {"happy","wave","question","explain","recommend","cta","sleep","eat","exercise","surprise","think","point"}
    for scene in scenes:
        assert scene["emotion"] in valid


def test_uses_sonnet_model(monkeypatch):
    splitter = make_splitter()
    captured = {}
    def capture(**kw):
        captured["model"] = kw.get("model")
        return mock_response(MOCK_RESPONSE)
    monkeypatch.setattr(splitter._client.messages, "create", capture)
    splitter.split(SAMPLE_SCRIPT)
    assert captured["model"] == "claude-sonnet-4-6"


# --- Fallback tests ---

def test_fallback_on_bad_json(monkeypatch):
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response("not json at all"))
    scenes = splitter.split(SAMPLE_SCRIPT)
    assert len(scenes) == 1
    assert scenes[0]["act"] == "hook"
    assert scenes[0]["emotion"] == "explain"


def test_fallback_dialogue_uses_action(monkeypatch):
    """Nếu dialogue null/missing, fallback về action text"""
    bad_response = '[{"order":1,"act":"hook","action":"Milo nhảy","dialogue":null,"emotion":"happy"}]'
    splitter = make_splitter()
    monkeypatch.setattr(splitter._client.messages, "create", lambda **kw: mock_response(bad_response))
    scenes = splitter.split(SAMPLE_SCRIPT)
    assert scenes[0]["dialogue"] == "Milo nhảy"
```

- [ ] **Step 2: Chạy tests để xác nhận chúng FAIL**

```bash
cd backend
python -m pytest tests/test_scene_splitter.py -v 2>&1 | head -40
```

Expected: nhiều FAILED — `test_uses_sonnet_model`, `test_scene_has_required_fields`, etc.

- [ ] **Step 3: Rewrite scene_splitter.py**

Thay toàn bộ `backend/services/scene_splitter.py`:

```python
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
        # Fallback: dialogue → action nếu null/empty
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
```

- [ ] **Step 4: Chạy tests để xác nhận PASS**

```bash
cd backend
python -m pytest tests/test_scene_splitter.py -v
```

Expected: tất cả PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/services/scene_splitter.py backend/tests/test_scene_splitter.py
git commit -m "feat: upgrade SceneSplitter to Sonnet with act/action/dialogue schema"
```

---

## Task 3: Pipeline Step 2 — lưu fields mới

**Files:**
- Modify: `backend/routers/pipeline.py` (step 2 endpoint)

- [ ] **Step 1: Tìm step 2 handler trong pipeline.py**

Mở `backend/routers/pipeline.py`, tìm `@router.post("/{session_id}/step/2")`.

Hiện tại nó lưu: `order`, `script_text`, `emotion_tag`.

- [ ] **Step 2: Update step 2 để lưu fields mới**

Thay đoạn tạo `SceneModel` trong step 2:

```python
# Trước:
scene = SceneModel(
    session_id=session_id,
    order=s["order"],
    script_text=s["text"],
    emotion_tag=s["emotion"],
)

# Sau:
scene = SceneModel(
    session_id=session_id,
    order=s["order"],
    script_text=s.get("action", s.get("text", "")),  # backward compat
    emotion_tag=s.get("emotion", "explain"),
    act=s.get("act"),
    action=s.get("action"),
    dialogue=s.get("dialogue"),
)
```

- [ ] **Step 3: Update response dict trong step 2**

Thay đoạn build response scenes list:

```python
return {
    "scenes": [
        {
            "id": s.id,
            "order": s.order,
            "act": s.act,
            "action": s.action,
            "dialogue": s.dialogue,
            "script_text": s.script_text,
            "emotion_tag": s.emotion_tag,
        }
        for s in scene_objs
    ]
}
```

- [ ] **Step 4: Test thủ công step 2**

```bash
cd backend && uvicorn main:app --reload &
sleep 2

# Tạo session trước
curl -s -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"lang": "vi"}' | python -m json.tool

# Nhớ session_id từ response (ví dụ: 1)
SESSION_ID=1

# Set topic
curl -s -X PATCH http://localhost:8000/sessions/$SESSION_ID \
  -H "Content-Type: application/json" \
  -d '{"topic": "Vitamin D3"}' | python -m json.tool

# Run step 2
curl -s -X POST http://localhost:8000/pipeline/$SESSION_ID/step/2 \
  -H "Content-Type: application/json" \
  -d '{"script": "Milo làm mặt hoảng sợ: '\''Bạn có biết 70% người Việt thiếu Vitamin D3 không?'\'' Milo chỉ vào bảng số liệu: '\''Đây là những dấu hiệu thiếu D3.'\'' Milo cầm hộp vitamin: '\''Follow để biết cách bổ sung đúng cách!'\''"}' \
  | python -m json.tool
```

Expected: response có `act`, `action`, `dialogue` trong mỗi scene.

- [ ] **Step 5: Kill server và commit**

```bash
kill %1 2>/dev/null; true
git add backend/routers/pipeline.py
git commit -m "feat: pipeline step 2 saves act/action/dialogue fields"
```

---

## Task 4: Pipeline Step 4 — TTS dùng dialogue

**Files:**
- Modify: `backend/routers/pipeline.py` (step 4 endpoint)

- [ ] **Step 1: Viết failing test**

Tạo file `backend/tests/test_pipeline_tts.py`:

```python
"""Test rằng step 4 dùng dialogue cho TTS, không phải script_text."""
import pytest
from unittest.mock import MagicMock, patch, call


def test_step4_uses_dialogue_not_script_text():
    """TTS phải nhận dialogue text, không phải script_text."""
    from routers.pipeline import step_4_scene_video
    from unittest.mock import MagicMock

    # Mock scene với cả dialogue và script_text khác nhau
    mock_scene = MagicMock()
    mock_scene.id = 1
    mock_scene.session_id = 1
    mock_scene.script_text = "Milo nhảy vào màn hình hài hước: 'Xin chào!'  ← đây là script_text đầy đủ"
    mock_scene.dialogue = "Xin chào!"  # ← chỉ lời thoại
    mock_scene.action = "Milo nhảy vào màn hình hài hước"
    mock_scene.image_path = "/tmp/test.png"
    mock_scene.emotion_tag = "happy"
    mock_scene.act = "hook"

    mock_session = MagicMock()
    mock_session.lang = "vi"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [mock_scene, mock_session]

    tts_calls = []

    with patch("routers.pipeline._get_tts") as mock_tts_factory, \
         patch("routers.pipeline._get_assembler") as mock_asm_factory, \
         patch("os.path.join", side_effect=lambda *a: "/".join(a)):

        mock_tts = MagicMock()
        mock_tts_factory.return_value = mock_tts
        mock_asm = MagicMock()
        mock_asm_factory.return_value = mock_asm

        def capture_tts(**kwargs):
            tts_calls.append(kwargs.get("text", ""))
        mock_tts.generate_sync.side_effect = capture_tts

        try:
            step_4_scene_video(session_id=1, scene_id=1, db=mock_db)
        except Exception:
            pass  # các side effects khác có thể fail, không quan trọng

    assert len(tts_calls) > 0, "TTS không được gọi"
    assert tts_calls[0] == "Xin chào!", \
        f"TTS nhận '{tts_calls[0]}' thay vì dialogue 'Xin chào!'"


def test_step4_fallback_to_script_text_when_no_dialogue():
    """Nếu dialogue null, fallback về script_text."""
    from routers.pipeline import step_4_scene_video

    mock_scene = MagicMock()
    mock_scene.id = 1
    mock_scene.session_id = 1
    mock_scene.script_text = "Nội dung đầy đủ"
    mock_scene.dialogue = None  # không có dialogue
    mock_scene.image_path = "/tmp/test.png"
    mock_scene.emotion_tag = "happy"
    mock_scene.act = "hook"

    mock_session = MagicMock()
    mock_session.lang = "vi"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [mock_scene, mock_session]

    tts_calls = []

    with patch("routers.pipeline._get_tts") as mock_tts_factory, \
         patch("routers.pipeline._get_assembler") as mock_asm_factory, \
         patch("os.path.join", side_effect=lambda *a: "/".join(a)):

        mock_tts = MagicMock()
        mock_tts_factory.return_value = mock_tts
        mock_asm = MagicMock()
        mock_asm_factory.return_value = mock_asm

        def capture_tts(**kwargs):
            tts_calls.append(kwargs.get("text", ""))
        mock_tts.generate_sync.side_effect = capture_tts

        try:
            step_4_scene_video(session_id=1, scene_id=1, db=mock_db)
        except Exception:
            pass

    assert len(tts_calls) > 0
    assert tts_calls[0] == "Nội dung đầy đủ"
```

- [ ] **Step 2: Chạy tests để xác nhận FAIL**

```bash
cd backend
python -m pytest tests/test_pipeline_tts.py -v
```

Expected: `test_step4_uses_dialogue_not_script_text` FAIL — vì hiện tại step 4 dùng `scene.script_text`.

- [ ] **Step 3: Fix step 4 trong pipeline.py**

Tìm `step_4_scene_video` trong `backend/routers/pipeline.py`.

Thay dòng TTS call:

```python
# Trước:
tts.generate_sync(text=scene.script_text, lang=session.lang, output_path=audio_path)

# Sau:
tts_text = scene.dialogue or scene.script_text
tts.generate_sync(text=tts_text, lang=session.lang, output_path=audio_path)
```

- [ ] **Step 4: Chạy tests để xác nhận PASS**

```bash
cd backend
python -m pytest tests/test_pipeline_tts.py -v
```

Expected: cả 2 tests PASSED.

- [ ] **Step 5: Chạy toàn bộ test suite**

```bash
cd backend
python -m pytest tests/ -v --tb=short
```

Expected: tất cả tests PASS (hoặc chỉ fail những test không liên quan đến task này).

- [ ] **Step 6: Commit**

```bash
git add backend/routers/pipeline.py backend/tests/test_pipeline_tts.py
git commit -m "fix: TTS uses scene.dialogue instead of script_text, fallback to script_text"
```

---

## Task 5: End-to-end verification

- [ ] **Step 1: Chạy full pipeline test**

```bash
cd backend && uvicorn main:app --reload &
sleep 2

# Tạo session
SESSION=$(curl -s -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"lang": "vi"}' | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Session ID: $SESSION"

# Set topic
curl -s -X PATCH http://localhost:8000/sessions/$SESSION \
  -H "Content-Type: application/json" \
  -d '{"topic": "Vitamin D3 và sức khoẻ"}' > /dev/null

# Step 2: SceneSplitter
echo "=== Step 2: SceneSplitter ==="
SCENES=$(curl -s -X POST http://localhost:8000/pipeline/$SESSION/step/2 \
  -H "Content-Type: application/json" \
  -d '{"script": "Milo làm mặt hoảng sợ: '\''Ê! 70% người Việt thiếu Vitamin D3 mà không biết!'\''\nMilo chỉ vào bảng: '\''Mệt mỏi, đau xương, dễ ốm... đây là dấu hiệu thiếu D3.'\''\nMilo cầm hộp vitamin cười: '\''Follow Milo để biết cách bổ sung đúng cách nhé!'\''"  }')

echo $SCENES | python -m json.tool | grep -E '"act"|"dialogue"|"action"'
```

Expected output:
```
"act": "hook",
"dialogue": "Ê! 70% người Việt thiếu Vitamin D3 mà không biết!",
"action": "Milo làm mặt hoảng sợ",
"act": "main",
"dialogue": "Mệt mỏi, đau xương, dễ ốm... đây là dấu hiệu thiếu D3.",
"act": "cta",
"dialogue": "Follow Milo để biết cách bổ sung đúng cách nhé!",
```

- [ ] **Step 2: Verify audio file ngắn hơn**

Lấy scene_id đầu tiên, chạy step 3 (images) rồi step 4:

```bash
# Lấy scene_id từ DB
SCENE_ID=$(python -c "
from database import SessionLocal
from models import SceneModel
db = SessionLocal()
s = db.query(SceneModel).filter(SceneModel.session_id==$SESSION).order_by(SceneModel.order).first()
print(s.id)
db.close()
")

echo "Scene ID: $SCENE_ID"

# Step 3 (images)
curl -s -X POST http://localhost:8000/pipeline/$SESSION/step/3 | python -m json.tool

# Step 4 (TTS + video)
curl -s -X POST http://localhost:8000/pipeline/$SESSION/step/4/$SCENE_ID | python -m json.tool
```

- [ ] **Step 3: Kiểm tra audio chỉ đọc dialogue**

```bash
# Nghe file audio (macOS)
AUDIO_PATH=$(python -c "
from database import SessionLocal
from models import SceneModel
db = SessionLocal()
s = db.query(SceneModel).filter(SceneModel.id==$SCENE_ID).first()
print(s.audio_path or '')
db.close()
")

echo "Audio path: $AUDIO_PATH"
[ -f "$AUDIO_PATH" ] && afplay "$AUDIO_PATH" || echo "File không tồn tại: $AUDIO_PATH"
```

Expected: audio ngắn, chỉ đọc lời thoại Milo — không đọc phần mô tả hành động.

- [ ] **Step 4: Kill server + final commit**

```bash
kill %1 2>/dev/null; true
git add -A
git commit -m "test: add end-to-end verification for audio dialogue fix"
```

---

## Summary

Sau plan này:
- ✅ SceneSplitter dùng `claude-sonnet-4-6`, trả về `{act, action, dialogue, emotion}`
- ✅ TTS chỉ đọc `dialogue` — không đọc mô tả hành động
- ✅ DB có đủ columns cho Plan 2 (Kontext image gen)
- ✅ Backward compatible — `script_text` vẫn được lưu, TTS có fallback

**Plan 2** (tiếp theo): `2026-04-13-kontext-image-gen.md` — CharacterManager + KontextGenerator + pipeline step 3 overhaul.
