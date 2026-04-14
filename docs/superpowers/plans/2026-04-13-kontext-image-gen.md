# Kontext Image Gen + Multi-Character System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mỗi user có thể tạo nhiều nhân vật (upload ảnh ref + mô tả tính cách), chọn nhân vật khi tạo video, và FLUX.1 Kontext gen ảnh Milo đúng hành động từng cảnh thay vì dùng sprite PNG cố định.

**Architecture:** Thêm `Character` model vào DB. `CharacterManager` lưu/load ref images và build Kontext prompt. `KontextGenerator` gọi fal.ai FLUX Kontext API (async polling). Pipeline step 3 thay AssetManager bằng KontextGenerator — gen 1 ảnh tích hợp Milo + BG per scene. Frontend thêm Character CRUD + dropdown chọn nhân vật khi tạo session.

**Tech Stack:** Python, FastAPI, SQLAlchemy, `fal-client`, FLUX.1 Kontext via fal.ai, React/Next.js (frontend)

**Requires:** Plan `2026-04-13-audio-scene-fix.md` đã complete (DB có `act`, `action`, `dialogue` columns).

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/models.py` | Modify | Thêm `Character` model, thêm `character_id` vào `SessionModel` |
| `backend/services/character_manager.py` | Create | CRUD character, upload ref images lên fal.ai, build Kontext prompt |
| `backend/services/kontext_generator.py` | Create | Gọi FLUX Kontext API, poll result, download + save image |
| `backend/routers/characters.py` | Create | REST endpoints: list/create/get/delete characters |
| `backend/routers/pipeline.py` | Modify | Step 3 dùng KontextGenerator; step 2 nhận `character_id` |
| `backend/main.py` | Modify | Register characters router; serve `assets/characters` static |
| `backend/tests/test_character_manager.py` | Create | Unit tests CharacterManager |
| `backend/tests/test_kontext_generator.py` | Create | Unit tests KontextGenerator (mock fal API) |
| `frontend/components/CharacterManager.tsx` | Create | UI tạo/chọn nhân vật |
| `frontend/components/steps/Step0Character.tsx` | Create | Step chọn nhân vật trước khi tạo video |
| `frontend/lib/types.ts` | Modify | Thêm `Character` type |

---

## Task 1: Character model trong DB

**Files:**
- Modify: `backend/models.py`

- [ ] **Step 1: Thêm Character model**

Mở `backend/models.py`, thêm sau `SessionModel`:

```python
class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    personality = Column(Text, nullable=True)       # mô tả tính cách
    ref_image_paths = Column(Text, nullable=True)   # JSON list paths local
    fal_image_urls = Column(Text, nullable=True)    # JSON list URLs đã upload lên fal.ai
    char_description = Column(Text, nullable=True)  # auto-gen từ personality + tên
    created_at = Column(DateTime, default=datetime.utcnow)
```

Thêm import ở đầu file nếu chưa có:
```python
from datetime import datetime
from sqlalchemy import DateTime
```

- [ ] **Step 2: Thêm `character_id` vào SessionModel**

Trong `SessionModel`, thêm:
```python
character_id = Column(Integer, nullable=True)  # FK tới characters.id (soft ref)
```

- [ ] **Step 3: Recreate DB**

```bash
cd backend
python -c "
from database import Base, engine
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
print('DB recreated OK')
"
```

Expected: `DB recreated OK`

- [ ] **Step 4: Verify**

```bash
cd backend
python -c "
from database import engine
from sqlalchemy import inspect
i = inspect(engine)
print('characters cols:', [c['name'] for c in i.get_columns('characters')])
print('sessions cols:', [c['name'] for c in i.get_columns('sessions')])
assert 'character_id' in [c['name'] for c in i.get_columns('sessions')]
print('OK')
"
```

Expected: in ra columns và `OK`.

- [ ] **Step 5: Commit**

```bash
git add backend/models.py
git commit -m "feat: add Character model and character_id to sessions"
```

---

## Task 2: CharacterManager service

**Files:**
- Create: `backend/services/character_manager.py`
- Create: `backend/tests/test_character_manager.py`

- [ ] **Step 1: Viết tests trước**

Tạo `backend/tests/test_character_manager.py`:

```python
import json
import os
import pytest
from unittest.mock import patch, MagicMock
from services.character_manager import CharacterManager


@pytest.fixture
def mgr(tmp_path):
    return CharacterManager(assets_dir=str(tmp_path))


def test_build_kontext_prompt_basic(mgr):
    char = MagicMock()
    char.name = "Milo"
    char.personality = "Robot vui vẻ, hài hước, thích nhảy nhót"
    char.char_description = "Blue chibi robot, round eyes, antenna, white gloves"

    scene_action = "Milo cầm viên vitamin to, mắt mở to ngạc nhiên"
    act = "main"

    prompt = mgr.build_kontext_prompt(char, scene_action, act)

    assert "Milo" in prompt
    assert "vitamin" in prompt.lower() or "cầm" in prompt.lower()
    assert "9:16" in prompt or "vertical" in prompt.lower()
    assert "no text" in prompt.lower() or "no words" in prompt.lower()


def test_build_kontext_prompt_includes_act_context(mgr):
    char = MagicMock()
    char.name = "Milo"
    char.personality = "Robot năng động"
    char.char_description = "Blue robot"

    hook_prompt = mgr.build_kontext_prompt(char, "Milo nhảy vào màn hình", "hook")
    cta_prompt = mgr.build_kontext_prompt(char, "Milo vẫy tay", "cta")

    # Hook và CTA phải có context khác nhau
    assert hook_prompt != cta_prompt


def test_save_ref_images_creates_dir(mgr, tmp_path):
    char_id = 1
    # Tạo fake image files
    img1 = tmp_path / "ref1.png"
    img1.write_bytes(b"fake png data")

    saved = mgr.save_ref_images(char_id, [str(img1)])
    assert len(saved) == 1
    assert os.path.exists(saved[0])


def test_get_fal_urls_returns_list(mgr):
    char = MagicMock()
    char.fal_image_urls = json.dumps(["https://fal.ai/img1.png", "https://fal.ai/img2.png"])

    urls = mgr.get_fal_urls(char)
    assert urls == ["https://fal.ai/img1.png", "https://fal.ai/img2.png"]


def test_get_fal_urls_empty_when_none(mgr):
    char = MagicMock()
    char.fal_image_urls = None

    urls = mgr.get_fal_urls(char)
    assert urls == []
```

- [ ] **Step 2: Chạy tests — xác nhận FAIL**

```bash
cd backend
python -m pytest tests/test_character_manager.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'services.character_manager'`

- [ ] **Step 3: Tạo CharacterManager**

Tạo `backend/services/character_manager.py`:

```python
import json
import os
import shutil
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

ACT_CONTEXT = {
    "hook": "energetic and eye-catching scene, dynamic background, bright colors",
    "main": "clean informative setting, health and wellness environment, soft lighting",
    "cta":  "warm inviting atmosphere, product spotlight, encouraging mood",
}


class CharacterManager:
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir
        os.makedirs(assets_dir, exist_ok=True)

    def save_ref_images(self, char_id: int, source_paths: List[str]) -> List[str]:
        """Copy uploaded ref images vào assets/characters/{char_id}/"""
        char_dir = os.path.join(self.assets_dir, "characters", str(char_id))
        os.makedirs(char_dir, exist_ok=True)
        saved = []
        for i, src in enumerate(source_paths):
            ext = os.path.splitext(src)[1] or ".png"
            dest = os.path.join(char_dir, f"ref_{i}{ext}")
            shutil.copy2(src, dest)
            saved.append(dest)
        return saved

    def get_fal_urls(self, character) -> List[str]:
        """Parse JSON list of fal.ai URLs từ character.fal_image_urls"""
        if not character.fal_image_urls:
            return []
        try:
            return json.loads(character.fal_image_urls)
        except (json.JSONDecodeError, TypeError):
            return []

    def build_kontext_prompt(self, character, scene_action: str, act: str) -> str:
        """Build prompt cho FLUX Kontext từ character + scene action + act."""
        act_ctx = ACT_CONTEXT.get(act, ACT_CONTEXT["main"])
        char_desc = character.char_description or f"{character.name}, {character.personality or 'friendly mascot character'}"

        prompt = (
            f"Character: {char_desc}. "
            f"Scene: {scene_action}. "
            f"Setting: {act_ctx}. "
            f"Style: TikTok vertical video frame, 9:16 aspect ratio, "
            f"clean composition, character in foreground, "
            f"no text overlay, no watermark, no UI elements. "
            f"The character must match the reference images exactly."
        )
        return prompt

    def build_char_description(self, name: str, personality: str) -> str:
        """Tạo char_description ngắn gọn từ name + personality cho prompt."""
        return f"{name} — {personality}" if personality else name
```

- [ ] **Step 4: Chạy tests — xác nhận PASS**

```bash
cd backend
python -m pytest tests/test_character_manager.py -v
```

Expected: tất cả PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/services/character_manager.py backend/tests/test_character_manager.py
git commit -m "feat: add CharacterManager service with Kontext prompt builder"
```

---

## Task 3: KontextGenerator service

**Files:**
- Create: `backend/services/kontext_generator.py`
- Create: `backend/tests/test_kontext_generator.py`

- [ ] **Step 1: Install fal-client**

```bash
cd backend
pip install fal-client
echo "fal-client>=0.5.0" >> requirements.txt
```

- [ ] **Step 2: Viết tests (mock fal API)**

Tạo `backend/tests/test_kontext_generator.py`:

```python
import os
import json
import pytest
from unittest.mock import patch, MagicMock
from services.kontext_generator import KontextGenerator


@pytest.fixture
def gen(tmp_path):
    return KontextGenerator(
        fal_key="test-key",
        output_dir=str(tmp_path)
    )


def test_generate_returns_image_path(gen, tmp_path):
    fake_img_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # fake PNG header

    with patch("fal_client.subscribe") as mock_sub, \
         patch("requests.get") as mock_get:

        mock_sub.return_value = {
            "images": [{"url": "https://fal.ai/output/test.png"}]
        }
        mock_get.return_value = MagicMock(content=fake_img_bytes, status_code=200)

        result = gen.generate(
            prompt="Milo robot holding vitamin",
            ref_image_urls=["https://fal.ai/ref/milo.png"],
            output_filename="scene_1.png",
            seed=42,
        )

    assert result.endswith(".png")
    assert os.path.exists(result)


def test_generate_raises_on_empty_images(gen):
    with patch("fal_client.subscribe") as mock_sub:
        mock_sub.return_value = {"images": []}

        with pytest.raises(RuntimeError, match="Kontext trả về không có ảnh"):
            gen.generate(
                prompt="test prompt",
                ref_image_urls=["https://example.com/ref.png"],
                output_filename="scene_fail.png",
                seed=1,
            )


def test_generate_uses_correct_model(gen):
    called_with = {}

    def capture(model, arguments, **kw):
        called_with["model"] = model
        called_with["args"] = arguments
        return {"images": [{"url": "https://fal.ai/out.png"}]}

    fake_img = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    with patch("fal_client.subscribe", side_effect=capture), \
         patch("requests.get", return_value=MagicMock(content=fake_img)):
        gen.generate("prompt", ["https://ref.png"], "out.png", seed=99)

    assert called_with["model"] == "fal-ai/flux-kontext/dev"
    assert called_with["args"]["seed"] == 99
    assert called_with["args"]["image_size"]["width"] == 1080
    assert called_with["args"]["image_size"]["height"] == 1920


def test_upload_image_returns_url(gen, tmp_path):
    fake_file = tmp_path / "milo.png"
    fake_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

    with patch("fal_client.upload_file", return_value="https://fal.ai/uploads/milo.png"):
        url = gen.upload_ref_image(str(fake_file))

    assert url == "https://fal.ai/uploads/milo.png"
```

- [ ] **Step 3: Chạy tests — xác nhận FAIL**

```bash
cd backend
python -m pytest tests/test_kontext_generator.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'services.kontext_generator'`

- [ ] **Step 4: Tạo KontextGenerator**

Tạo `backend/services/kontext_generator.py`:

```python
import os
import logging
import requests
import fal_client
from typing import List, Optional

logger = logging.getLogger(__name__)

KONTEXT_MODEL = "fal-ai/flux-kontext/dev"


class KontextGenerator:
    def __init__(self, fal_key: str, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        os.environ["FAL_KEY"] = fal_key

    def upload_ref_image(self, local_path: str) -> str:
        """Upload ảnh ref lên fal.ai storage, trả về URL."""
        url = fal_client.upload_file(local_path)
        logger.info(f"Uploaded ref image: {local_path} → {url}")
        return url

    def generate(
        self,
        prompt: str,
        ref_image_urls: List[str],
        output_filename: str,
        seed: int = 42,
    ) -> str:
        """
        Gọi FLUX Kontext với ref images + prompt.
        Trả về local path của ảnh đã download.
        """
        if not ref_image_urls:
            raise ValueError("Cần ít nhất 1 ref image URL")

        arguments = {
            "prompt": prompt,
            "image_url": ref_image_urls[0],   # Kontext nhận ảnh ref chính
            "image_size": {"width": 1080, "height": 1920},
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "seed": seed,
            "output_format": "png",
        }

        # Nếu có nhiều ref images, thêm vào prompt context
        if len(ref_image_urls) > 1:
            arguments["extra_image_urls"] = ref_image_urls[1:]

        logger.info(f"Calling Kontext: {KONTEXT_MODEL} | prompt: {prompt[:80]}...")

        result = fal_client.subscribe(
            KONTEXT_MODEL,
            arguments=arguments,
        )

        images = result.get("images", [])
        if not images:
            raise RuntimeError("Kontext trả về không có ảnh")

        image_url = images[0]["url"]
        output_path = os.path.join(self.output_dir, output_filename)
        self._download(image_url, output_path)

        logger.info(f"Kontext image saved: {output_path}")
        return output_path

    def _download(self, url: str, dest: str) -> None:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            f.write(resp.content)
```

- [ ] **Step 5: Chạy tests — xác nhận PASS**

```bash
cd backend
python -m pytest tests/test_kontext_generator.py -v
```

Expected: tất cả PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/services/kontext_generator.py backend/tests/test_kontext_generator.py backend/requirements.txt
git commit -m "feat: add KontextGenerator service for FLUX Kontext image gen"
```

---

## Task 4: Characters REST API

**Files:**
- Create: `backend/routers/characters.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Tạo characters router**

Tạo `backend/routers/characters.py`:

```python
import json
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session as DBSession
from typing import List, Optional
from database import get_db
from models import Character
from services.character_manager import CharacterManager
from services.kontext_generator import KontextGenerator

router = APIRouter()

ASSETS_DIR = os.getenv("ASSETS_DIR", "../assets")
FAL_KEY = os.getenv("FAL_KEY", "")


def _get_char_manager():
    return CharacterManager(assets_dir=ASSETS_DIR)


def _get_kontext_gen():
    return KontextGenerator(
        fal_key=FAL_KEY,
        output_dir=os.path.join(os.getenv("OUTPUT_DIR", "../output"), "images"),
    )


@router.get("/")
def list_characters(db: DBSession = Depends(get_db)):
    chars = db.query(Character).order_by(Character.created_at.desc()).all()
    return {"characters": [_serialize(c) for c in chars]}


@router.post("/")
async def create_character(
    name: str = Form(...),
    personality: str = Form(""),
    files: List[UploadFile] = File(default=[]),
    db: DBSession = Depends(get_db),
):
    mgr = _get_char_manager()
    gen = _get_kontext_gen()

    char = Character(
        name=name,
        personality=personality,
        char_description=mgr.build_char_description(name, personality),
    )
    db.add(char)
    db.commit()
    db.refresh(char)

    # Lưu ref images
    saved_paths = []
    for upload in files[:3]:   # max 3 ảnh
        tmp_path = f"/tmp/char_{char.id}_{upload.filename}"
        with open(tmp_path, "wb") as f:
            content = await upload.read()
            f.write(content)
        saved_paths.append(tmp_path)

    if saved_paths:
        local_paths = mgr.save_ref_images(char.id, saved_paths)
        char.ref_image_paths = json.dumps(local_paths)

        # Upload lên fal.ai để dùng cho Kontext
        try:
            fal_urls = [gen.upload_ref_image(p) for p in local_paths]
            char.fal_image_urls = json.dumps(fal_urls)
        except Exception as e:
            # Không fail nếu upload fal lỗi — sẽ retry khi gen
            char.fal_image_urls = json.dumps([])

        db.commit()

    return _serialize(char)


@router.get("/{char_id}")
def get_character(char_id: int, db: DBSession = Depends(get_db)):
    char = db.query(Character).filter(Character.id == char_id).first()
    if not char:
        raise HTTPException(404, "Character not found")
    return _serialize(char)


@router.delete("/{char_id}")
def delete_character(char_id: int, db: DBSession = Depends(get_db)):
    char = db.query(Character).filter(Character.id == char_id).first()
    if not char:
        raise HTTPException(404, "Character not found")
    db.delete(char)
    db.commit()
    return {"deleted": char_id}


def _serialize(c: Character) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "personality": c.personality,
        "char_description": c.char_description,
        "ref_image_count": len(json.loads(c.ref_image_paths or "[]")),
        "fal_ready": bool(json.loads(c.fal_image_urls or "[]")),
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
```

- [ ] **Step 2: Register router trong main.py**

Mở `backend/main.py`, thêm:

```python
from routers import characters as characters_router

# Trong phần đăng ký routers:
app.include_router(characters_router.router, prefix="/characters", tags=["characters"])
```

Thêm static files serve cho character assets:
```python
from fastapi.staticfiles import StaticFiles
import os

assets_dir = os.getenv("ASSETS_DIR", "../assets")
app.mount("/static/characters", StaticFiles(directory=os.path.join(assets_dir, "characters")), name="characters")
```

- [ ] **Step 3: Test API thủ công**

```bash
cd backend && uvicorn main:app --reload &
sleep 2

# List characters (empty)
curl -s http://localhost:8000/characters/ | python -m json.tool

# Tạo character Milo với ảnh ref
curl -s -X POST http://localhost:8000/characters/ \
  -F "name=Milo" \
  -F "personality=Robot vui vẻ hài hước, thích nhảy nhót và làm mặt ngộ nghĩnh, luôn nhiệt tình về sức khoẻ" \
  -F "files=@../assets/milo/milo_happy.png" \
  -F "files=@../assets/milo/milo_wave.png" \
  | python -m json.tool

# List lại để verify
curl -s http://localhost:8000/characters/ | python -m json.tool
```

Expected: character Milo được tạo với `ref_image_count: 2`.

- [ ] **Step 4: Kill server + commit**

```bash
kill %1 2>/dev/null; true
git add backend/routers/characters.py backend/main.py
git commit -m "feat: add characters REST API with ref image upload"
```

---

## Task 5: Pipeline Step 2 — nhận character_id; Step 3 — KontextGenerator

**Files:**
- Modify: `backend/routers/pipeline.py`

- [ ] **Step 1: Update step 2 để nhận character_id**

Trong `backend/routers/pipeline.py`, tìm `step_2_scenes`. Thêm lưu `character_id` vào session:

```python
@router.post("/{session_id}/step/2")
def step_2_scenes(session_id: int, body: dict, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")

    script = body.get("script", "")

    # Lưu character_id nếu được truyền vào
    character_id = body.get("character_id")
    if character_id:
        session.character_id = character_id

    splitter = _get_scene_splitter()
    raw_scenes = splitter.split(script=script, lang=session.lang)
    db.query(SceneModel).filter(SceneModel.session_id == session_id).delete()

    scene_objs = []
    for s in raw_scenes:
        scene = SceneModel(
            session_id=session_id,
            order=s["order"],
            script_text=s.get("action", s.get("text", "")),
            emotion_tag=s.get("emotion", "explain"),
            act=s.get("act"),
            action=s.get("action"),
            dialogue=s.get("dialogue"),
        )
        db.add(scene)
        scene_objs.append(scene)

    session.step = 2
    db.commit()
    for s in scene_objs:
        db.refresh(s)

    return {
        "character_id": session.character_id,
        "scenes": [
            {
                "id": s.id,
                "order": s.order,
                "act": s.act,
                "action": s.action,
                "dialogue": s.dialogue,
                "emotion_tag": s.emotion_tag,
            }
            for s in scene_objs
        ]
    }
```

- [ ] **Step 2: Thêm factory functions vào pipeline.py**

Thêm sau các factory functions hiện tại:

```python
def _get_char_manager():
    return CharacterManager(assets_dir=os.getenv("ASSETS_DIR", "../assets"))


def _get_kontext_gen():
    return KontextGenerator(
        fal_key=os.getenv("FAL_KEY", ""),
        output_dir=os.path.join(os.getenv("OUTPUT_DIR", "../output"), "images"),
    )
```

Thêm imports ở đầu file:
```python
from models import SessionModel, SceneModel, Character
from services.character_manager import CharacterManager
from services.kontext_generator import KontextGenerator
```

- [ ] **Step 3: Rewrite step 3 — KontextGenerator thay AssetManager**

Thay toàn bộ `step_3_images`:

```python
@router.post("/{session_id}/step/3")
def step_3_images(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")

    scenes = (
        db.query(SceneModel)
        .filter(SceneModel.session_id == session_id)
        .order_by(SceneModel.order)
        .all()
    )

    # Lấy character — nếu không có thì dùng fallback AssetManager
    character = None
    if session.character_id:
        character = db.query(Character).filter(Character.id == session.character_id).first()

    mgr = _get_char_manager()
    kontext = _get_kontext_gen()

    # Seed cố định per session để consistency
    seed = session.id * 1000 % 1000000

    updated = []
    for scene in scenes:
        if character:
            # FLUX Kontext path
            fal_urls = mgr.get_fal_urls(character)
            if not fal_urls:
                # Upload ref images nếu chưa có
                ref_paths = json.loads(character.ref_image_paths or "[]")
                if ref_paths:
                    fal_urls = [kontext.upload_ref_image(p) for p in ref_paths]
                    character.fal_image_urls = json.dumps(fal_urls)
                    db.commit()

            if fal_urls:
                prompt = mgr.build_kontext_prompt(
                    character,
                    scene.action or scene.script_text,
                    scene.act or "main",
                )
                filename = f"session_{session_id}_scene_{scene.id}.png"
                try:
                    image_path = kontext.generate(
                        prompt=prompt,
                        ref_image_urls=fal_urls,
                        output_filename=filename,
                        seed=seed + scene.order,
                    )
                    scene.image_path = image_path
                except Exception as e:
                    # Fallback về AssetManager nếu Kontext fail
                    _fallback_asset(scene, db)
            else:
                _fallback_asset(scene, db)
        else:
            # Không có character → dùng sprite PNG cũ
            _fallback_asset(scene, db)

        updated.append({
            "id": scene.id,
            "image_path": scene.image_path,
            "act": scene.act,
            "emotion_tag": scene.emotion_tag,
        })

    session.step = 3
    db.commit()
    return {"scenes": updated}


def _fallback_asset(scene: SceneModel, db):
    """Fallback: dùng Milo sprite PNG cũ."""
    from services.asset_manager import AssetManager
    mgr = AssetManager(os.getenv("ASSETS_DIR", "../assets"))
    match = mgr.find_best_match(scene.emotion_tag or "explain")
    scene.image_path = match["path"] if match else None
```

Thêm import json ở đầu file nếu chưa có:
```python
import json
```

- [ ] **Step 4: Commit**

```bash
git add backend/routers/pipeline.py
git commit -m "feat: pipeline step 2 accepts character_id, step 3 uses KontextGenerator"
```

---

## Task 6: Frontend — Character Manager UI

**Files:**
- Create: `frontend/components/CharacterManager.tsx`
- Modify: `frontend/lib/types.ts`

- [ ] **Step 1: Thêm Character type**

Mở `frontend/lib/types.ts`, thêm:

```typescript
export interface Character {
  id: number
  name: string
  personality: string | null
  char_description: string | null
  ref_image_count: number
  fal_ready: boolean
  created_at: string | null
}
```

- [ ] **Step 2: Tạo CharacterManager component**

Tạo `frontend/components/CharacterManager.tsx`:

```typescript
'use client'

import { useState, useEffect, useRef } from 'react'
import { Character } from '@/lib/types'

interface Props {
  selectedId: number | null
  onSelect: (char: Character) => void
}

export default function CharacterManager({ selectedId, onSelect }: Props) {
  const [characters, setCharacters] = useState<Character[]>([])
  const [creating, setCreating] = useState(false)
  const [loading, setLoading] = useState(false)
  const [name, setName] = useState('')
  const [personality, setPersonality] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const fileRef = useRef<HTMLInputElement>(null)

  const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetch(`${API}/characters/`)
      .then(r => r.json())
      .then(d => setCharacters(d.characters || []))
  }, [])

  async function createCharacter() {
    if (!name.trim()) return
    setLoading(true)
    const form = new FormData()
    form.append('name', name)
    form.append('personality', personality)
    files.forEach(f => form.append('files', f))

    const res = await fetch(`${API}/characters/`, { method: 'POST', body: form })
    const char: Character = await res.json()
    setCharacters(prev => [char, ...prev])
    setCreating(false)
    setName('')
    setPersonality('')
    setFiles([])
    setLoading(false)
    onSelect(char)
  }

  async function deleteCharacter(id: number) {
    await fetch(`${API}/characters/${id}`, { method: 'DELETE' })
    setCharacters(prev => prev.filter(c => c.id !== id))
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-300">Nhân vật</h3>
        <button
          onClick={() => setCreating(true)}
          className="text-xs bg-indigo-600 hover:bg-indigo-500 px-3 py-1 rounded-full text-white"
        >
          + Thêm nhân vật
        </button>
      </div>

      {/* Character list */}
      <div className="space-y-2">
        {characters.map(char => (
          <div
            key={char.id}
            onClick={() => onSelect(char)}
            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
              selectedId === char.id
                ? 'border-indigo-500 bg-indigo-900/30'
                : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
            }`}
          >
            <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-lg">
              🤖
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-200 truncate">{char.name}</div>
              <div className="text-xs text-gray-500 truncate">
                {char.ref_image_count} ảnh ref
                {char.fal_ready ? ' · ✓ sẵn sàng' : ' · ⏳ chưa upload'}
              </div>
            </div>
            {selectedId === char.id && (
              <span className="text-xs text-indigo-400 font-semibold">✓ Đang dùng</span>
            )}
            <button
              onClick={e => { e.stopPropagation(); deleteCharacter(char.id) }}
              className="text-gray-600 hover:text-red-400 text-xs px-1"
            >
              ✕
            </button>
          </div>
        ))}

        {characters.length === 0 && !creating && (
          <p className="text-xs text-gray-600 text-center py-4">
            Chưa có nhân vật nào. Thêm nhân vật để bắt đầu.
          </p>
        )}
      </div>

      {/* Create form */}
      {creating && (
        <div className="border border-indigo-500/40 bg-indigo-900/20 rounded-lg p-4 space-y-3">
          <div className="text-xs font-semibold text-indigo-300">Tạo nhân vật mới</div>

          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Tên nhân vật (vd: Milo)"
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 placeholder-gray-600"
          />

          <textarea
            value={personality}
            onChange={e => setPersonality(e.target.value)}
            placeholder="Mô tả tính cách: Robot vui vẻ, hài hước, thích nhảy nhót..."
            rows={2}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 placeholder-gray-600 resize-none"
          />

          <div>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={e => setFiles(Array.from(e.target.files || []).slice(0, 3))}
            />
            <button
              onClick={() => fileRef.current?.click()}
              className="w-full border border-dashed border-gray-600 rounded py-3 text-xs text-gray-500 hover:border-gray-400 hover:text-gray-400"
            >
              {files.length > 0
                ? `✓ ${files.length} ảnh đã chọn`
                : '📸 Upload 1-3 ảnh reference'}
            </button>
          </div>

          <div className="flex gap-2">
            <button
              onClick={createCharacter}
              disabled={loading || !name.trim()}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 py-2 rounded text-sm font-semibold text-white"
            >
              {loading ? 'Đang tạo...' : 'Tạo nhân vật'}
            </button>
            <button
              onClick={() => setCreating(false)}
              className="px-4 py-2 rounded text-sm text-gray-400 hover:text-gray-200 border border-gray-700"
            >
              Huỷ
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/components/CharacterManager.tsx frontend/lib/types.ts
git commit -m "feat: add CharacterManager UI component for multi-character support"
```

---

## Task 7: Frontend — Tích hợp chọn nhân vật vào Step 2

**Files:**
- Modify: `frontend/components/steps/Step3Images.tsx` (hoặc file Step2 tương ứng trong codebase)

- [ ] **Step 1: Xác định file cần sửa**

```bash
ls frontend/components/steps/
```

Tìm file step tương ứng với "chọn kịch bản + tạo scenes" (Step 2 trong pipeline). Thường là file có gọi `/step/2` endpoint.

- [ ] **Step 2: Thêm CharacterManager vào step này**

Mở file step đó, thêm vào đầu:

```typescript
import CharacterManager from '@/components/CharacterManager'
import { Character } from '@/lib/types'
```

Thêm state:
```typescript
const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null)
```

Thêm `<CharacterManager>` component vào JSX (trước phần script):
```tsx
<div className="mb-6">
  <CharacterManager
    selectedId={selectedCharacter?.id ?? null}
    onSelect={setSelectedCharacter}
  />
</div>
```

Khi gọi step 2 API, thêm `character_id`:
```typescript
const body: Record<string, unknown> = { script: selectedScript }
if (selectedCharacter) {
  body.character_id = selectedCharacter.id
}

const res = await fetch(`${API}/pipeline/${sessionId}/step/2`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})
```

- [ ] **Step 3: Test UI**

```bash
cd frontend && npm run dev &
sleep 3
open http://localhost:3000
```

Verify:
1. CharacterManager hiển thị (có nút "+ Thêm nhân vật")
2. Tạo nhân vật Milo với ảnh từ `assets/milo/milo_happy.png`
3. Character xuất hiện trong list, có thể chọn
4. Chạy step 2 với character đã chọn → response có `character_id`
5. Chạy step 3 → kiểm tra `image_path` trong DB là ảnh AI gen (không phải sprite PNG cũ)

- [ ] **Step 4: Kill servers + commit**

```bash
kill %1 %2 2>/dev/null; true
git add frontend/components/steps/
git commit -m "feat: integrate character selection into video creation flow"
```

---

## Task 8: End-to-end test với FAL_KEY thật

**Yêu cầu:** Có `FAL_KEY` thật từ fal.ai (đăng ký tại fal.ai, free tier có ~$1 credit)

- [ ] **Step 1: Set env vars**

```bash
export FAL_KEY="your-fal-key-here"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

- [ ] **Step 2: Chạy full pipeline**

```bash
cd backend && uvicorn main:app --reload &
sleep 2

# Tạo character
CHAR=$(curl -s -X POST http://localhost:8000/characters/ \
  -F "name=Milo" \
  -F "personality=Robot hoạt hình xanh dương, vui vẻ hài hước, mắt tròn to, ăng ten trên đầu" \
  -F "files=@../assets/milo/milo_happy.png" \
  -F "files=@../assets/milo/milo_wave.png")
CHAR_ID=$(echo $CHAR | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Character ID: $CHAR_ID"

# Tạo session
SESSION=$(curl -s -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"lang":"vi"}' | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Session ID: $SESSION"

# Set topic
curl -s -X PATCH http://localhost:8000/sessions/$SESSION \
  -H "Content-Type: application/json" \
  -d '{"topic":"Vitamin D3"}' > /dev/null

# Step 2 với character_id
SCENES=$(curl -s -X POST http://localhost:8000/pipeline/$SESSION/step/2 \
  -H "Content-Type: application/json" \
  -d "{\"script\":\"Milo làm mặt hoảng sợ: 'Ê! 70% người Việt thiếu D3!'\nMilo chỉ tay vào biểu đồ: 'Đây là triệu chứng thiếu D3.'\nMilo cầm hộp vitamin cười: 'Follow để biết cách bổ sung!'\", \"character_id\": $CHAR_ID}")

echo "=== Scenes ==="
echo $SCENES | python -m json.tool | grep -E '"act"|"dialogue"|"action"'

# Step 3 — FLUX Kontext gen images (~45s cho 3 cảnh)
echo "=== Step 3: Kontext gen images (chờ ~45s) ==="
IMAGES=$(curl -s -X POST http://localhost:8000/pipeline/$SESSION/step/3)
echo $IMAGES | python -m json.tool
```

- [ ] **Step 3: Verify ảnh gen ra**

```bash
# Xem ảnh cảnh đầu tiên
SCENE1_IMG=$(echo $IMAGES | python -c "
import sys, json
data = json.load(sys.stdin)
print(data['scenes'][0]['image_path'] or '')
")
echo "Scene 1 image: $SCENE1_IMG"
[ -f "$SCENE1_IMG" ] && open "$SCENE1_IMG" || echo "File not found"
```

Expected: mở ảnh Milo đúng hành động + background tích hợp.

- [ ] **Step 4: Chạy full video**

```bash
# Step 4 cho từng scene
SCENE_IDS=$(python -c "
from database import SessionLocal
from models import SceneModel
db = SessionLocal()
ids = [s.id for s in db.query(SceneModel).filter(SceneModel.session_id==$SESSION).order_by(SceneModel.order).all()]
print(' '.join(map(str, ids)))
db.close()
")

for SCENE_ID in $SCENE_IDS; do
  echo "Step 4 scene $SCENE_ID..."
  curl -s -X POST http://localhost:8000/pipeline/$SESSION/step/4/$SCENE_ID > /dev/null
done

# Step 5 — merge
FINAL=$(curl -s -X POST http://localhost:8000/pipeline/$SESSION/step/5 \
  -H "Content-Type: application/json" \
  -d '{"bgm_path":"","bgm_volume":0.15}')

FINAL_PATH=$(echo $FINAL | python -c "import sys,json; print(json.load(sys.stdin)['final_video_path'])")
echo "Final video: $FINAL_PATH"
[ -f "$FINAL_PATH" ] && open "$FINAL_PATH"
```

Expected: video mở ra với Milo đúng hành động từng cảnh, audio chỉ đọc lời thoại.

- [ ] **Step 5: Kill server + final commit**

```bash
kill %1 2>/dev/null; true
git add -A
git commit -m "feat: complete Kontext image gen pipeline with multi-character support"
```

---

## Summary

Sau plan này (cùng với Plan 1):
- ✅ Multi-character: user tạo nhiều nhân vật, upload ảnh ref, chọn khi tạo video
- ✅ FLUX Kontext gen ảnh Milo đúng hành động từng cảnh + BG tích hợp
- ✅ Fallback về sprite PNG nếu không có character hoặc Kontext fail
- ✅ Audio chỉ đọc lời thoại (từ Plan 1)
- ✅ SceneSplitter Sonnet với schema đầy đủ (từ Plan 1)
- ✅ Frontend có CharacterManager UI với create/select/delete

**Env vars cần thiết:**
```
FAL_KEY=...
ANTHROPIC_API_KEY=...
```
