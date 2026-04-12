# Milo Studio — Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build FastAPI backend with SQLite persistence, Asset Manager, and all 6 pipeline step services for the Milo Studio TikTok video creation system.

**Architecture:** FastAPI app, SQLAlchemy + SQLite for session/scene/schedule state. Each pipeline step is a stateless service module. REST endpoints expose each step. Session state is persisted after every user action so work can be paused and resumed.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, edge-tts, ffmpeg-python, google-generativeai (Gemini 2.0 Flash), pytrends, praw, pytest, httpx

---

## File Structure

```
backend/
├── main.py                    # FastAPI app, router registration, CORS
├── database.py                # SQLAlchemy engine, Base, get_db dependency
├── models.py                  # SQLAlchemy ORM models (Session, Scene, Schedule)
├── schemas.py                 # Pydantic request/response schemas
├── routers/
│   ├── sessions.py            # GET/POST/PATCH /sessions, GET /sessions/{id}
│   ├── pipeline.py            # POST /sessions/{id}/step/{n} — run each step
│   ├── schedule.py            # GET/POST/PATCH /schedule
│   ├── assets.py              # GET /assets/milo — list images by tag
│   └── chat.py                # POST /chat — contextual AI chat
├── services/
│   ├── asset_manager.py       # Index Milo image library from assets/milo/
│   ├── trend_fetcher.py       # Google Trends + Reddit top posts
│   ├── script_generator.py    # Gemini: topic discuss + script gen
│   ├── scene_splitter.py      # Gemini: split script → scenes with emotion tags
│   ├── tts_service.py         # edge-tts async wrapper, VI + EN voices
│   ├── video_assembler.py     # FFmpeg: image + audio → ken-burns scene clip
│   ├── video_merger.py        # FFmpeg: concat scenes + BGM + transitions
│   ├── caption_generator.py   # Gemini: gen caption + hashtags from script
│   ├── tiktok_client.py       # TikTok Content Posting API: upload + schedule
│   └── chat_handler.py        # Gemini chat with per-step system prompt
├── tests/
│   ├── conftest.py            # test DB, test client, fixtures
│   ├── test_sessions.py
│   ├── test_asset_manager.py
│   ├── test_trend_fetcher.py
│   ├── test_script_generator.py
│   ├── test_scene_splitter.py
│   ├── test_tts_service.py
│   ├── test_video_assembler.py
│   ├── test_video_merger.py
│   ├── test_caption_generator.py
│   └── test_pipeline_router.py
├── requirements.txt
└── .env.example

assets/
└── milo/
    ├── index.json             # {"milo_wave.png": ["happy","wave"], ...}
    └── *.png                  # Milo pose images

output/                        # generated audio/video files (gitignored)
```

---

## Task 1: Project Setup

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/main.py`
- Create: `assets/milo/index.json`
- Create: `.gitignore`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.30
pydantic==2.7.0
python-dotenv==1.0.1
httpx==0.27.0
pytest==8.2.0
pytest-asyncio==0.23.6
google-generativeai==0.7.2
edge-tts==6.1.9
ffmpeg-python==0.2.0
pytrends==4.9.2
praw==7.7.1
python-multipart==0.0.9
```

- [ ] **Step 2: Create .env.example**

```
GEMINI_API_KEY=your_gemini_api_key_here
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
TIKTOK_ACCESS_TOKEN=your_tiktok_access_token
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=MiloStudio/1.0
ASSETS_DIR=../assets
OUTPUT_DIR=../output
```

- [ ] **Step 3: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import engine, Base
from routers import sessions, pipeline, schedule, assets, chat

load_dotenv()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Milo Studio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(pipeline.router, prefix="/sessions", tags=["pipeline"])
app.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
app.include_router(assets.router, prefix="/assets", tags=["assets"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Create placeholder assets/milo/index.json**

```json
{
  "milo_wave.png": ["happy", "wave", "greeting"],
  "milo_think.png": ["think", "question", "curious"],
  "milo_point.png": ["explain", "point", "teach"],
  "milo_happy.png": ["happy", "excited", "positive"],
  "milo_sleep.png": ["sleep", "tired", "rest"],
  "milo_eat.png": ["eat", "food", "nutrition"],
  "milo_exercise.png": ["exercise", "workout", "health"],
  "milo_hold_product.png": ["recommend", "product", "affiliate"],
  "milo_cta.png": ["cta", "follow", "subscribe"]
}
```

- [ ] **Step 5: Create .gitignore**

```
output/
__pycache__/
*.pyc
.env
*.db
.pytest_cache/
node_modules/
.next/
```

- [ ] **Step 6: Install dependencies and verify**

```bash
cd backend
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 7: Commit**

```bash
git init
git add backend/ assets/ .gitignore
git commit -m "feat: project scaffold — FastAPI backend + asset structure"
```

---

## Task 2: Database Models + Session CRUD

**Files:**
- Create: `backend/database.py`
- Create: `backend/models.py`
- Create: `backend/schemas.py`
- Create: `backend/routers/sessions.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_sessions.py`

- [ ] **Step 1: Create database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./milo_studio.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: Create models.py**

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base

class SessionModel(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    topic = Column(Text, nullable=True)
    lang = Column(String(10), default="vi")
    step = Column(Integer, default=1)
    status = Column(String(20), default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SceneModel(Base):
    __tablename__ = "scenes"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, index=True, nullable=False)
    order = Column(Integer, nullable=False)
    script_text = Column(Text, nullable=False)
    emotion_tag = Column(String(50), nullable=True)
    image_path = Column(String(500), nullable=True)
    audio_path = Column(String(500), nullable=True)
    video_path = Column(String(500), nullable=True)
    approved = Column(Boolean, default=False)

class ScheduleModel(Base):
    __tablename__ = "schedule"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, index=True, nullable=False)
    post_time = Column(DateTime(timezone=True), nullable=False)
    caption = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)
    tiktok_post_id = Column(String(200), nullable=True)
    status = Column(String(20), default="pending")
```

- [ ] **Step 3: Create schemas.py**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SessionCreate(BaseModel):
    title: str
    lang: str = "vi"

class SessionUpdate(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None
    step: Optional[int] = None
    status: Optional[str] = None

class SessionOut(BaseModel):
    id: int
    title: str
    topic: Optional[str]
    lang: str
    step: int
    status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    model_config = {"from_attributes": True}

class SceneOut(BaseModel):
    id: int
    session_id: int
    order: int
    script_text: str
    emotion_tag: Optional[str]
    image_path: Optional[str]
    audio_path: Optional[str]
    video_path: Optional[str]
    approved: bool
    model_config = {"from_attributes": True}

class ScheduleCreate(BaseModel):
    session_id: int
    post_time: datetime
    caption: Optional[str] = None
    hashtags: Optional[str] = None

class ScheduleOut(BaseModel):
    id: int
    session_id: int
    post_time: datetime
    caption: Optional[str]
    hashtags: Optional[str]
    tiktok_post_id: Optional[str]
    status: str
    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Write failing tests for session CRUD**

```python
# tests/test_sessions.py
import pytest
from fastapi.testclient import TestClient

def test_create_session(client):
    res = client.post("/sessions", json={"title": "Test Video", "lang": "vi"})
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Test Video"
    assert data["step"] == 1
    assert data["status"] == "draft"

def test_list_sessions(client):
    client.post("/sessions", json={"title": "Video A", "lang": "vi"})
    client.post("/sessions", json={"title": "Video B", "lang": "en"})
    res = client.get("/sessions")
    assert res.status_code == 200
    assert len(res.json()) >= 2

def test_get_session(client):
    created = client.post("/sessions", json={"title": "My Video", "lang": "vi"}).json()
    res = client.get(f"/sessions/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]

def test_get_session_not_found(client):
    res = client.get("/sessions/99999")
    assert res.status_code == 404

def test_update_session_step(client):
    created = client.post("/sessions", json={"title": "Video", "lang": "vi"}).json()
    res = client.patch(f"/sessions/{created['id']}", json={"step": 2, "topic": "Ngủ đủ giấc"})
    assert res.status_code == 200
    assert res.json()["step"] == 2
    assert res.json()["topic"] == "Ngủ đủ giấc"

def test_delete_session(client):
    created = client.post("/sessions", json={"title": "To Delete", "lang": "vi"}).json()
    res = client.delete(f"/sessions/{created['id']}")
    assert res.status_code == 200
    assert client.get(f"/sessions/{created['id']}").status_code == 404
```

- [ ] **Step 5: Create tests/conftest.py**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

TEST_DATABASE_URL = "sqlite:///./test_milo.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
```

- [ ] **Step 6: Run tests — expect FAIL (router not created yet)**

```bash
cd backend
pytest tests/test_sessions.py -v
```

Expected: ImportError or 404s — routers not wired yet.

- [ ] **Step 7: Create routers/sessions.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import SessionModel
from schemas import SessionCreate, SessionUpdate, SessionOut
from typing import List

router = APIRouter()

@router.post("", response_model=SessionOut)
def create_session(data: SessionCreate, db: Session = Depends(get_db)):
    session = SessionModel(title=data.title, lang=data.lang)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("", response_model=List[SessionOut])
def list_sessions(db: Session = Depends(get_db)):
    return db.query(SessionModel).order_by(SessionModel.created_at.desc()).all()

@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.patch("/{session_id}", response_model=SessionOut)
def update_session(session_id: int, data: SessionUpdate, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(session, field, value)
    db.commit()
    db.refresh(session)
    return session

@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"ok": True}

@router.get("/{session_id}/scenes", response_model=List[SceneOut])
def get_scenes(session_id: int, db: Session = Depends(get_db)):
    return db.query(SceneModel).filter(SceneModel.session_id == session_id).order_by(SceneModel.order).all()
```

- [ ] **Step 8: Create empty router stubs so main.py imports work**

Create `backend/routers/__init__.py` (empty).

Create `backend/routers/pipeline.py`:
```python
from fastapi import APIRouter
router = APIRouter()
```

Create `backend/routers/schedule.py`:
```python
from fastapi import APIRouter
router = APIRouter()
```

Create `backend/routers/assets.py`:
```python
from fastapi import APIRouter
router = APIRouter()
```

Create `backend/routers/chat.py`:
```python
from fastapi import APIRouter
router = APIRouter()
```

- [ ] **Step 9: Run tests — expect PASS**

```bash
pytest tests/test_sessions.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 10: Commit**

```bash
git add backend/
git commit -m "feat: database models + session CRUD endpoints"
```

---

## Task 3: Asset Manager

**Files:**
- Create: `backend/services/asset_manager.py`
- Create: `backend/tests/test_asset_manager.py`
- Modify: `backend/routers/assets.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_asset_manager.py
import os, json, pytest
from services.asset_manager import AssetManager

@pytest.fixture
def asset_manager(tmp_path):
    milo_dir = tmp_path / "milo"
    milo_dir.mkdir()
    index = {
        "milo_wave.png": ["happy", "wave"],
        "milo_think.png": ["think", "curious"],
        "milo_point.png": ["explain", "teach"],
    }
    (milo_dir / "index.json").write_text(json.dumps(index))
    for name in index:
        (milo_dir / name).write_bytes(b"fake_image")
    return AssetManager(str(tmp_path))

def test_list_all(asset_manager):
    images = asset_manager.list_all()
    assert len(images) == 3
    assert images[0]["filename"] == "milo_wave.png"
    assert "happy" in images[0]["tags"]

def test_find_by_tag(asset_manager):
    results = asset_manager.find_by_tag("explain")
    assert len(results) == 1
    assert results[0]["filename"] == "milo_point.png"

def test_find_best_match(asset_manager):
    match = asset_manager.find_best_match("explain")
    assert match["filename"] == "milo_point.png"

def test_find_best_match_fallback(asset_manager):
    match = asset_manager.find_best_match("unknown_emotion")
    assert match is not None  # returns first image as fallback
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_asset_manager.py -v
```

Expected: ImportError — service not created yet.

- [ ] **Step 3: Create services/asset_manager.py**

```python
import json, os
from typing import List, Optional

class AssetManager:
    def __init__(self, assets_dir: str):
        self.milo_dir = os.path.join(assets_dir, "milo")
        index_path = os.path.join(self.milo_dir, "index.json")
        with open(index_path) as f:
            self._index: dict[str, list[str]] = json.load(f)

    def list_all(self) -> List[dict]:
        return [
            {"filename": name, "tags": tags, "path": os.path.join(self.milo_dir, name)}
            for name, tags in self._index.items()
        ]

    def find_by_tag(self, tag: str) -> List[dict]:
        return [
            {"filename": name, "tags": tags, "path": os.path.join(self.milo_dir, name)}
            for name, tags in self._index.items()
            if tag in tags
        ]

    def find_best_match(self, emotion: str) -> Optional[dict]:
        results = self.find_by_tag(emotion)
        if results:
            return results[0]
        all_images = self.list_all()
        return all_images[0] if all_images else None
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_asset_manager.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Wire into assets router**

```python
# routers/assets.py
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
from services.asset_manager import AssetManager
import os

router = APIRouter()
_manager = None

def get_asset_manager() -> AssetManager:
    global _manager
    if _manager is None:
        assets_dir = os.getenv("ASSETS_DIR", "../assets")
        _manager = AssetManager(assets_dir)
    return _manager

@router.get("/milo")
def list_milo_images(tag: str = None):
    mgr = get_asset_manager()
    if tag:
        return mgr.find_by_tag(tag)
    return mgr.list_all()
```

- [ ] **Step 6: Commit**

```bash
git add backend/services/asset_manager.py backend/routers/assets.py backend/tests/test_asset_manager.py
git commit -m "feat: asset manager — Milo image library indexing + tag search"
```

---

## Task 4: Trend Fetcher (Step 1A)

**Files:**
- Create: `backend/services/trend_fetcher.py`
- Create: `backend/tests/test_trend_fetcher.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_trend_fetcher.py
import pytest
from unittest.mock import patch, MagicMock
from services.trend_fetcher import TrendFetcher

@pytest.fixture
def fetcher():
    return TrendFetcher(reddit_client_id="fake", reddit_secret="fake", reddit_user_agent="test")

def test_fetch_returns_list(fetcher):
    with patch.object(fetcher, '_fetch_google_trends', return_value=[
        {"topic": "Ngủ đủ giấc", "score": 85, "source": "google_trends"}
    ]):
        with patch.object(fetcher, '_fetch_reddit', return_value=[
            {"topic": "Omega-3 benefits", "score": 70, "source": "reddit"}
        ]):
            results = fetcher.fetch(keywords=["sức khoẻ"], lang="vi", limit=5)
            assert isinstance(results, list)
            assert len(results) <= 5
            assert all("topic" in r for r in results)
            assert all("score" in r for r in results)
            assert all("source" in r for r in results)

def test_fetch_sorted_by_score(fetcher):
    with patch.object(fetcher, '_fetch_google_trends', return_value=[
        {"topic": "A", "score": 40, "source": "google"},
        {"topic": "B", "score": 90, "source": "google"},
    ]):
        with patch.object(fetcher, '_fetch_reddit', return_value=[]):
            results = fetcher.fetch(keywords=["health"], lang="en", limit=5)
            assert results[0]["score"] >= results[-1]["score"]
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_trend_fetcher.py -v
```

- [ ] **Step 3: Create services/trend_fetcher.py**

```python
from pytrends.request import TrendReq
import praw
from typing import List
import logging

logger = logging.getLogger(__name__)

class TrendFetcher:
    def __init__(self, reddit_client_id: str, reddit_secret: str, reddit_user_agent: str):
        self.reddit = praw.Reddit(
            client_id=reddit_client_id,
            client_secret=reddit_secret,
            user_agent=reddit_user_agent,
        )

    def _fetch_google_trends(self, keywords: List[str], lang: str) -> List[dict]:
        try:
            hl = "vi-VN" if lang == "vi" else "en-US"
            geo = "VN" if lang == "vi" else "US"
            pytrends = TrendReq(hl=hl, tz=420)
            pytrends.build_payload(keywords[:5], timeframe="now 7-d", geo=geo)
            related = pytrends.related_queries()
            results = []
            for kw in keywords[:2]:
                df = related.get(kw, {}).get("top")
                if df is not None and not df.empty:
                    for _, row in df.head(5).iterrows():
                        results.append({
                            "topic": row["query"],
                            "score": int(row["value"]),
                            "source": "google_trends"
                        })
            return results
        except Exception as e:
            logger.warning(f"Google Trends fetch failed: {e}")
            return []

    def _fetch_reddit(self, lang: str) -> List[dict]:
        try:
            subreddits = ["health", "nutrition", "ArtificialIntelligence"] if lang == "en" else ["suckhoe"]
            results = []
            for sub in subreddits:
                try:
                    for post in self.reddit.subreddit(sub).hot(limit=5):
                        results.append({
                            "topic": post.title,
                            "score": min(100, post.score // 10),
                            "source": f"reddit/{sub}"
                        })
                except Exception:
                    continue
            return results
        except Exception as e:
            logger.warning(f"Reddit fetch failed: {e}")
            return []

    def fetch(self, keywords: List[str], lang: str = "vi", limit: int = 8) -> List[dict]:
        trends = self._fetch_google_trends(keywords, lang)
        reddit = self._fetch_reddit(lang)
        combined = trends + reddit
        combined.sort(key=lambda x: x["score"], reverse=True)
        return combined[:limit]
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_trend_fetcher.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/services/trend_fetcher.py backend/tests/test_trend_fetcher.py
git commit -m "feat: trend fetcher — Google Trends + Reddit topic research"
```

---

## Task 5: Script Generator (Step 1B + 1C)

**Files:**
- Create: `backend/services/script_generator.py`
- Create: `backend/tests/test_script_generator.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_script_generator.py
import pytest
from unittest.mock import patch, MagicMock
from services.script_generator import ScriptGenerator

@pytest.fixture
def generator():
    return ScriptGenerator(api_key="fake_key")

def test_generate_scripts_returns_list(generator):
    mock_response = MagicMock()
    mock_response.text = """
    SCRIPT_1:
    Hook: Bạn có biết thiếu ngủ làm bạn béo không?
    Content: Ngủ dưới 6 tiếng mỗi đêm tăng hormone ghrelin...
    CTA: Follow Milo để biết thêm mẹo sống khoẻ!
    SCRIPT_2:
    Hook: Sự thật shocking về giấc ngủ và cân nặng
    Content: Nghiên cứu mới nhất cho thấy...
    CTA: Link thực phẩm chức năng hỗ trợ ngủ ngon ở bio!
    """
    with patch.object(generator._model, 'generate_content', return_value=mock_response):
        scripts = generator.generate_scripts(
            topic="Ngủ và giảm cân",
            lang="vi",
            channel_context="Kênh sống khoẻ cùng AI, robot Milo",
            affiliate_category="thực phẩm chức năng"
        )
        assert isinstance(scripts, list)
        assert len(scripts) >= 1
        assert all(isinstance(s, str) for s in scripts)

def test_parse_scripts_splits_correctly(generator):
    raw = "SCRIPT_1:\nHook A\nSCRIPT_2:\nHook B"
    scripts = generator._parse_scripts(raw)
    assert len(scripts) == 2
    assert "Hook A" in scripts[0]
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_script_generator.py -v
```

- [ ] **Step 3: Create services/script_generator.py**

```python
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
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_script_generator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/services/script_generator.py backend/tests/test_script_generator.py
git commit -m "feat: script generator — Gemini multi-script generation with affiliate context"
```

---

## Task 6: Scene Splitter (Step 2)

**Files:**
- Create: `backend/services/scene_splitter.py`
- Create: `backend/tests/test_scene_splitter.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_scene_splitter.py
from unittest.mock import patch, MagicMock
from services.scene_splitter import SceneSplitter

def test_split_returns_scenes():
    splitter = SceneSplitter(api_key="fake")
    mock_resp = MagicMock()
    mock_resp.text = """
    [{"order":1,"text":"Chào mọi người! Hôm nay Milo sẽ chia sẻ về giấc ngủ.","emotion":"wave"},
     {"order":2,"text":"Bạn có biết thiếu ngủ làm tăng cân không?","emotion":"question"},
     {"order":3,"text":"Ngủ đủ 8 tiếng giúp giảm hormone gây thèm ăn.","emotion":"explain"}]
    """
    with patch.object(splitter._model, 'generate_content', return_value=mock_resp):
        scenes = splitter.split(script="some script text", lang="vi")
        assert len(scenes) == 3
        assert scenes[0]["order"] == 1
        assert scenes[0]["emotion"] in ["wave","happy","question","explain","recommend","cta","sleep","eat","exercise"]
        assert "text" in scenes[0]

def test_split_validates_emotion_tags():
    splitter = SceneSplitter(api_key="fake")
    mock_resp = MagicMock()
    mock_resp.text = '[{"order":1,"text":"hello","emotion":"INVALID_TAG"}]'
    with patch.object(splitter._model, 'generate_content', return_value=mock_resp):
        scenes = splitter.split(script="text", lang="vi")
        assert scenes[0]["emotion"] == "explain"  # fallback for invalid tag
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_scene_splitter.py -v
```

- [ ] **Step 3: Create services/scene_splitter.py**

```python
import google.generativeai as genai
import json, re
from typing import List

VALID_EMOTIONS = {"happy","wave","question","explain","recommend","cta","sleep","eat","exercise","surprise","think","point"}

class SceneSplitter:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("gemini-2.0-flash")

    def split(self, script: str, lang: str = "vi") -> List[dict]:
        prompt = f"""Split this TikTok script into 3-8 scenes. Each scene is one visual moment.
For each scene, assign ONE emotion tag from: {', '.join(sorted(VALID_EMOTIONS))}

Return ONLY a JSON array, no explanation:
[{{"order": 1, "text": "scene text", "emotion": "tag"}}, ...]

Script:
{script}"""
        response = self._model.generate_content(prompt)
        return self._parse_scenes(response.text)

    def _parse_scenes(self, raw: str) -> List[dict]:
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if not match:
            return [{"order": 1, "text": raw.strip(), "emotion": "explain"}]
        try:
            scenes = json.loads(match.group())
            for scene in scenes:
                if scene.get("emotion") not in VALID_EMOTIONS:
                    scene["emotion"] = "explain"
            return scenes
        except json.JSONDecodeError:
            return [{"order": 1, "text": raw.strip(), "emotion": "explain"}]
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_scene_splitter.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/services/scene_splitter.py backend/tests/test_scene_splitter.py
git commit -m "feat: scene splitter — Gemini script-to-scenes with emotion tagging"
```

---

## Task 7: TTS Service (Step 4)

**Files:**
- Create: `backend/services/tts_service.py`
- Create: `backend/tests/test_tts_service.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_tts_service.py
import pytest, os
from unittest.mock import patch, AsyncMock
from services.tts_service import TTSService

@pytest.fixture
def tts():
    return TTSService(output_dir="/tmp/tts_test")

def test_voice_selection_vi(tts):
    assert tts.get_voice("vi") == "vi-VN-NamMinhNeural"

def test_voice_selection_en(tts):
    assert tts.get_voice("en") == "en-US-GuyNeural"

def test_generate_creates_file(tts, tmp_path):
    output_path = str(tmp_path / "scene_1.mp3")
    with patch("edge_tts.Communicate") as mock_comm:
        mock_instance = AsyncMock()
        mock_comm.return_value = mock_instance
        mock_instance.save = AsyncMock()
        import asyncio
        asyncio.run(tts.generate(text="Xin chào", lang="vi", output_path=output_path))
        mock_instance.save.assert_called_once_with(output_path)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_tts_service.py -v
```

- [ ] **Step 3: Create services/tts_service.py**

```python
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
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_tts_service.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/services/tts_service.py backend/tests/test_tts_service.py
git commit -m "feat: TTS service — Edge-TTS VI/EN voice generation"
```

---

## Task 8: Video Assembler (Step 4 — scene clip)

**Files:**
- Create: `backend/services/video_assembler.py`
- Create: `backend/tests/test_video_assembler.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_video_assembler.py
import pytest
from unittest.mock import patch, MagicMock
from services.video_assembler import VideoAssembler

@pytest.fixture
def assembler(tmp_path):
    return VideoAssembler(output_dir=str(tmp_path))

def test_build_command_includes_ken_burns(assembler):
    cmd = assembler._build_ffmpeg_cmd(
        image_path="/img/milo.png",
        audio_path="/audio/scene1.mp3",
        output_path="/out/scene1.mp4",
        duration=5.0
    )
    cmd_str = " ".join(cmd)
    assert "zoompan" in cmd_str
    assert "/img/milo.png" in cmd_str
    assert "/audio/scene1.mp3" in cmd_str
    assert "/out/scene1.mp4" in cmd_str

def test_assemble_calls_ffmpeg(assembler):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        with patch.object(assembler, '_get_audio_duration', return_value=4.5):
            result = assembler.assemble(
                image_path="/img/milo.png",
                audio_path="/audio/s1.mp3",
                caption="Xin chào mọi người",
                output_path="/out/scene1.mp4"
            )
            assert mock_run.called
            assert result == "/out/scene1.mp4"
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_video_assembler.py -v
```

- [ ] **Step 3: Create services/video_assembler.py**

```python
import subprocess, os
from typing import Optional

class VideoAssembler:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _get_audio_duration(self, audio_path: str) -> float:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())

    def _build_ffmpeg_cmd(
        self, image_path: str, audio_path: str, output_path: str, duration: float
    ) -> list:
        # Ken Burns: slow zoom in over duration
        fps = 25
        total_frames = int(duration * fps)
        zoom_filter = (
            f"zoompan=z='min(zoom+0.0005,1.1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={total_frames}:s=1080x1920:fps={fps}"
        )
        return [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-vf", zoom_filter,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-pix_fmt", "yuv420p",
            output_path
        ]

    def assemble(
        self, image_path: str, audio_path: str, caption: str, output_path: str
    ) -> str:
        duration = self._get_audio_duration(audio_path)
        cmd = self._build_ffmpeg_cmd(image_path, audio_path, output_path, duration)
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_video_assembler.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/services/video_assembler.py backend/tests/test_video_assembler.py
git commit -m "feat: video assembler — FFmpeg ken-burns scene clip generation"
```

---

## Task 9: Video Merger + Caption Generator (Step 5)

**Files:**
- Create: `backend/services/video_merger.py`
- Create: `backend/services/caption_generator.py`
- Create: `backend/tests/test_video_merger.py`
- Create: `backend/tests/test_caption_generator.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_video_merger.py
from unittest.mock import patch, MagicMock, mock_open
from services.video_merger import VideoMerger

def test_create_concat_file(tmp_path):
    merger = VideoMerger(output_dir=str(tmp_path))
    clips = ["/a/clip1.mp4", "/a/clip2.mp4"]
    concat_path = merger._create_concat_file(clips, str(tmp_path / "concat.txt"))
    content = open(concat_path).read()
    assert "clip1.mp4" in content
    assert "clip2.mp4" in content
    assert "file" in content

def test_merge_calls_ffmpeg(tmp_path):
    merger = VideoMerger(output_dir=str(tmp_path))
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = merger.merge(
            clip_paths=["/a/s1.mp4", "/a/s2.mp4"],
            bgm_path="/music/bg.mp3",
            output_path=str(tmp_path / "final.mp4"),
            bgm_volume=0.15
        )
        assert mock_run.called
        assert result == str(tmp_path / "final.mp4")
```

```python
# tests/test_caption_generator.py
from unittest.mock import patch, MagicMock
from services.caption_generator import CaptionGenerator

def test_generate_returns_caption_and_hashtags():
    gen = CaptionGenerator(api_key="fake")
    mock_resp = MagicMock()
    mock_resp.text = "CAPTION:\nMilo chia sẻ bí quyết ngủ ngon 💤\n\nHASHTAGS:\n#suckhoe #milo #tiktok #AI"
    with patch.object(gen._model, 'generate_content', return_value=mock_resp):
        result = gen.generate(script="Test script", topic="Ngủ ngon", lang="vi")
        assert "caption" in result
        assert "hashtags" in result
        assert isinstance(result["hashtags"], list)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_video_merger.py tests/test_caption_generator.py -v
```

- [ ] **Step 3: Create services/video_merger.py**

```python
import subprocess, os, tempfile

class VideoMerger:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _create_concat_file(self, clip_paths: list, concat_path: str) -> str:
        with open(concat_path, "w") as f:
            for path in clip_paths:
                f.write(f"file '{path}'\n")
        return concat_path

    def merge(self, clip_paths: list, bgm_path: str, output_path: str, bgm_volume: float = 0.15) -> str:
        concat_file = os.path.join(self.output_dir, "concat.txt")
        self._create_concat_file(clip_paths, concat_file)
        temp_out = os.path.join(self.output_dir, "_merged_no_bgm.mp4")
        # Step 1: concat clips
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file, "-c", "copy", temp_out
        ], check=True, capture_output=True)
        # Step 2: mix BGM
        subprocess.run([
            "ffmpeg", "-y",
            "-i", temp_out,
            "-stream_loop", "-1", "-i", bgm_path,
            "-filter_complex",
            f"[1:a]volume={bgm_volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-shortest",
            output_path
        ], check=True, capture_output=True)
        os.remove(temp_out)
        return output_path
```

- [ ] **Step 4: Create services/caption_generator.py**

```python
import google.generativeai as genai
import re
from typing import List

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
        response = self._model.generate_content(prompt)
        return self._parse(response.text)

    def _parse(self, raw: str) -> dict:
        caption_match = re.search(r'CAPTION:\n(.*?)(?:\n\nHASHTAGS:|\Z)', raw, re.DOTALL)
        hashtag_match = re.search(r'HASHTAGS:\n(.*)', raw, re.DOTALL)
        caption = caption_match.group(1).strip() if caption_match else raw.strip()
        hashtag_str = hashtag_match.group(1).strip() if hashtag_match else ""
        hashtags = re.findall(r'#\w+', hashtag_str)
        return {"caption": caption, "hashtags": hashtags}
```

- [ ] **Step 5: Run — expect PASS**

```bash
pytest tests/test_video_merger.py tests/test_caption_generator.py -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/services/video_merger.py backend/services/caption_generator.py backend/tests/
git commit -m "feat: video merger (FFmpeg concat+BGM) + caption/hashtag generator"
```

---

## Task 10: TikTok Client (Step 6)

**Files:**
- Create: `backend/services/tiktok_client.py`
- Create: `backend/tests/test_tiktok_client.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_tiktok_client.py
import pytest
from unittest.mock import patch, MagicMock
from services.tiktok_client import TikTokClient

@pytest.fixture
def client():
    return TikTokClient(
        client_key="fake_key",
        client_secret="fake_secret",
        access_token="fake_token"
    )

def test_upload_video_returns_post_id(client, tmp_path):
    fake_video = tmp_path / "final.mp4"
    fake_video.write_bytes(b"fake_video_data")
    with patch("httpx.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"data": {"publish_id": "abc123"}, "error": {"code": "ok"}}
        )
        result = client.upload(
            video_path=str(fake_video),
            caption="Test caption #health",
            schedule_time=None
        )
        assert result["publish_id"] == "abc123"

def test_upload_raises_on_api_error(client, tmp_path):
    fake_video = tmp_path / "final.mp4"
    fake_video.write_bytes(b"data")
    with patch("httpx.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"error": {"code": "access_token_invalid", "message": "Token invalid"}}
        )
        with pytest.raises(Exception, match="TikTok API error"):
            client.upload(video_path=str(fake_video), caption="test", schedule_time=None)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_tiktok_client.py -v
```

- [ ] **Step 3: Create services/tiktok_client.py**

```python
import httpx, os
from datetime import datetime
from typing import Optional

TIKTOK_UPLOAD_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
TIKTOK_UPLOAD_FILE_URL = "https://open.tiktokapis.com/v2/post/publish/video/upload/"

class TikTokClient:
    def __init__(self, client_key: str, client_secret: str, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

    def upload(
        self, video_path: str, caption: str, schedule_time: Optional[datetime]
    ) -> dict:
        file_size = os.path.getsize(video_path)
        body = {
            "post_info": {
                "title": caption[:150],
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1
            }
        }
        if schedule_time:
            body["post_info"]["scheduled_publish_time"] = int(schedule_time.timestamp())
            body["post_info"]["auto_add_music"] = False

        init_resp = httpx.post(TIKTOK_UPLOAD_URL, json=body, headers=self.headers)
        init_data = init_resp.json()

        if init_data.get("error", {}).get("code") != "ok":
            raise Exception(f"TikTok API error: {init_data.get('error', {}).get('message')}")

        upload_url = init_data["data"]["upload_url"]
        with open(video_path, "rb") as f:
            video_data = f.read()
        httpx.put(
            upload_url,
            content=video_data,
            headers={"Content-Range": f"bytes 0-{file_size-1}/{file_size}", "Content-Type": "video/mp4"}
        )
        return {"publish_id": init_data["data"]["publish_id"]}
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_tiktok_client.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/services/tiktok_client.py backend/tests/test_tiktok_client.py
git commit -m "feat: TikTok client — video upload + schedule via Content Posting API"
```

---

## Task 11: Chat Handler

**Files:**
- Create: `backend/services/chat_handler.py`
- Create: `backend/tests/test_chat_handler.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_chat_handler.py
from unittest.mock import patch, MagicMock
from services.chat_handler import ChatHandler

def test_chat_returns_text():
    handler = ChatHandler(api_key="fake")
    mock_resp = MagicMock()
    mock_resp.text = "Tôi sẽ đổi ảnh cảnh 2 cho bạn."
    with patch.object(handler._model, 'generate_content', return_value=mock_resp):
        result = handler.chat(
            message="đổi ảnh cảnh 2 sang milo_happy",
            step=3,
            session_context={"topic": "Ngủ ngon", "step": 3}
        )
        assert isinstance(result, str)
        assert len(result) > 0

def test_chat_includes_step_context():
    handler = ChatHandler(api_key="fake")
    captured_prompt = []
    mock_resp = MagicMock()
    mock_resp.text = "OK"
    with patch.object(handler._model, 'generate_content', side_effect=lambda p: (captured_prompt.append(p), mock_resp)[1]):
        handler.chat(message="help", step=3, session_context={})
        assert any("bước 3" in str(p).lower() or "step 3" in str(p).lower() for p in captured_prompt)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_chat_handler.py -v
```

- [ ] **Step 3: Create services/chat_handler.py**

```python
import google.generativeai as genai

STEP_CONTEXTS = {
    1: "User đang ở Bước 1: Trend research và tạo kịch bản. Hỗ trợ chọn topic, chỉnh sửa kịch bản.",
    2: "User đang ở Bước 2: Phân cảnh. Hỗ trợ split/merge/reorder/edit scenes.",
    3: "User đang ở Bước 3: Chọn ảnh Milo. Hỗ trợ swap ảnh, giải thích tại sao chọn ảnh đó.",
    4: "User đang ở Bước 4: Tạo video từng cảnh. Hỗ trợ redo scene, điều chỉnh TTS.",
    5: "User đang ở Bước 5: Ghép video + caption. Hỗ trợ edit caption, hashtag, BGM.",
    6: "User đang ở Bước 6: Lên lịch đăng. Hỗ trợ set giờ đăng, cuối cùng trước khi publish.",
}

BASE_SYSTEM = """Bạn là Milo — AI assistant cho kênh TikTok "Sống khoẻ cùng AI".
Trả lời ngắn gọn, thân thiện. Nếu user yêu cầu thay đổi, mô tả rõ action cần thực hiện.
Không tự thực hiện thay đổi — chỉ hướng dẫn hoặc confirm."""

class ChatHandler:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("gemini-2.0-flash", system_instruction=BASE_SYSTEM)

    def chat(self, message: str, step: int, session_context: dict) -> str:
        step_ctx = STEP_CONTEXTS.get(step, "")
        context_str = f"Topic hiện tại: {session_context.get('topic', 'chưa có')}"
        prompt = f"{step_ctx}\n{context_str}\n\nUser: {message}"
        response = self._model.generate_content(prompt)
        return response.text
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest tests/test_chat_handler.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/services/chat_handler.py backend/tests/test_chat_handler.py
git commit -m "feat: chat handler — Gemini contextual AI chat per pipeline step"
```

---

## Task 12: Pipeline Router (wire all services)

**Files:**
- Modify: `backend/routers/pipeline.py`
- Modify: `backend/routers/schedule.py`
- Modify: `backend/routers/chat.py`
- Create: `backend/tests/test_pipeline_router.py`

- [ ] **Step 1: Write failing integration tests**

```python
# tests/test_pipeline_router.py
import pytest
from unittest.mock import patch

def test_step1a_trends(client):
    with patch("services.trend_fetcher.TrendFetcher.fetch", return_value=[
        {"topic": "Ngủ đủ giấc", "score": 90, "source": "google_trends"}
    ]):
        session = client.post("/sessions", json={"title": "Test", "lang": "vi"}).json()
        res = client.post(f"/sessions/{session['id']}/step/1a")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

def test_step1c_scripts(client):
    with patch("services.script_generator.ScriptGenerator.generate_scripts", return_value=[
        "Script A: Hook...", "Script B: Hook..."
    ]):
        session = client.post("/sessions", json={"title": "Test", "lang": "vi"}).json()
        client.patch(f"/sessions/{session['id']}", json={"topic": "Ngủ ngon"})
        res = client.post(f"/sessions/{session['id']}/step/1c")
        assert res.status_code == 200
        assert len(res.json()["scripts"]) == 2

def test_step2_scenes(client):
    with patch("services.scene_splitter.SceneSplitter.split", return_value=[
        {"order": 1, "text": "Chào mọi người", "emotion": "wave"},
        {"order": 2, "text": "Hôm nay Milo chia sẻ", "emotion": "explain"},
    ]):
        session = client.post("/sessions", json={"title": "Test", "lang": "vi"}).json()
        client.patch(f"/sessions/{session['id']}", json={"topic": "Test"})
        res = client.post(f"/sessions/{session['id']}/step/2", json={"script": "Test script"})
        assert res.status_code == 200
        scenes = res.json()["scenes"]
        assert len(scenes) == 2
        assert scenes[0]["emotion"] == "wave"

def test_chat_endpoint(client):
    with patch("services.chat_handler.ChatHandler.chat", return_value="OK tôi hiểu rồi!"):
        session = client.post("/sessions", json={"title": "Test", "lang": "vi"}).json()
        res = client.post("/chat", json={
            "session_id": session["id"],
            "message": "help",
            "step": 3
        })
        assert res.status_code == 200
        assert res.json()["reply"] == "OK tôi hiểu rồi!"
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest tests/test_pipeline_router.py -v
```

- [ ] **Step 3: Implement routers/pipeline.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from database import get_db
from models import SessionModel, SceneModel
from services.trend_fetcher import TrendFetcher
from services.script_generator import ScriptGenerator
from services.scene_splitter import SceneSplitter
from services.asset_manager import AssetManager
from services.tts_service import TTSService
from services.video_assembler import VideoAssembler
from services.video_merger import VideoMerger
from services.caption_generator import CaptionGenerator
from services.tiktok_client import TikTokClient
import os

router = APIRouter()

CHANNEL_KEYWORDS = ["sức khoẻ", "healthy", "thực phẩm chức năng", "AI health", "sống khoẻ"]

def _get_trend_fetcher():
    return TrendFetcher(
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID", ""),
        reddit_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "MiloStudio/1.0")
    )

def _get_script_gen():
    return ScriptGenerator(api_key=os.getenv("GEMINI_API_KEY", ""))

def _get_scene_splitter():
    return SceneSplitter(api_key=os.getenv("GEMINI_API_KEY", ""))

def _get_asset_manager():
    return AssetManager(os.getenv("ASSETS_DIR", "../assets"))

def _get_tts():
    return TTSService(output_dir=os.path.join(os.getenv("OUTPUT_DIR", "../output"), "audio"))

def _get_assembler():
    return VideoAssembler(output_dir=os.path.join(os.getenv("OUTPUT_DIR", "../output"), "scenes"))

def _get_merger():
    return VideoMerger(output_dir=os.path.join(os.getenv("OUTPUT_DIR", "../output"), "final"))

def _get_caption_gen():
    return CaptionGenerator(api_key=os.getenv("GEMINI_API_KEY", ""))

@router.post("/{session_id}/step/1a")
def step_1a_trends(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    fetcher = _get_trend_fetcher()
    trends = fetcher.fetch(keywords=CHANNEL_KEYWORDS, lang=session.lang, limit=8)
    return trends

@router.post("/{session_id}/step/1c")
def step_1c_scripts(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session or not session.topic:
        raise HTTPException(400, "Session must have a topic set before generating scripts")
    gen = _get_script_gen()
    scripts = gen.generate_scripts(
        topic=session.topic, lang=session.lang,
        channel_context="Kênh Sống khoẻ cùng AI, robot mascot Milo",
        affiliate_category="thực phẩm chức năng, thiết bị sức khoẻ"
    )
    return {"scripts": scripts}

@router.post("/{session_id}/step/2")
def step_2_scenes(session_id: int, body: dict, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    script = body.get("script", "")
    splitter = _get_scene_splitter()
    raw_scenes = splitter.split(script=script, lang=session.lang)
    db.query(SceneModel).filter(SceneModel.session_id == session_id).delete()
    scene_objs = []
    for s in raw_scenes:
        scene = SceneModel(
            session_id=session_id, order=s["order"],
            script_text=s["text"], emotion_tag=s["emotion"]
        )
        db.add(scene)
        scene_objs.append(scene)
    session.step = 2
    db.commit()
    for s in scene_objs:
        db.refresh(s)
    return {"scenes": [{"id": s.id, "order": s.order, "script_text": s.script_text, "emotion_tag": s.emotion_tag} for s in scene_objs]}

@router.post("/{session_id}/step/3")
def step_3_images(session_id: int, db: DBSession = Depends(get_db)):
    scenes = db.query(SceneModel).filter(SceneModel.session_id == session_id).order_by(SceneModel.order).all()
    mgr = _get_asset_manager()
    updated = []
    for scene in scenes:
        match = mgr.find_best_match(scene.emotion_tag or "explain")
        scene.image_path = match["path"] if match else None
        updated.append({"id": scene.id, "image_path": scene.image_path, "emotion_tag": scene.emotion_tag})
    db.query(SessionModel).filter(SessionModel.id == session_id).update({"step": 3})
    db.commit()
    return {"scenes": updated}

@router.post("/{session_id}/step/4/{scene_id}")
def step_4_scene_video(session_id: int, scene_id: int, db: DBSession = Depends(get_db)):
    scene = db.query(SceneModel).filter(SceneModel.id == scene_id, SceneModel.session_id == session_id).first()
    if not scene:
        raise HTTPException(404, "Scene not found")
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    tts = _get_tts()
    audio_path = os.path.join(os.getenv("OUTPUT_DIR", "../output"), "audio", f"session_{session_id}_scene_{scene_id}.mp3")
    tts.generate_sync(text=scene.script_text, lang=session.lang, output_path=audio_path)
    assembler = _get_assembler()
    video_path = os.path.join(os.getenv("OUTPUT_DIR", "../output"), "scenes", f"session_{session_id}_scene_{scene_id}.mp4")
    assembler.assemble(image_path=scene.image_path, audio_path=audio_path, caption=scene.script_text, output_path=video_path)
    scene.audio_path = audio_path
    scene.video_path = video_path
    db.commit()
    return {"scene_id": scene_id, "video_path": video_path}

@router.post("/{session_id}/step/5")
def step_5_merge(session_id: int, body: dict, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    scenes = db.query(SceneModel).filter(SceneModel.session_id == session_id).order_by(SceneModel.order).all()
    clip_paths = [s.video_path for s in scenes if s.video_path]
    bgm_path = body.get("bgm_path", "")
    output_path = os.path.join(os.getenv("OUTPUT_DIR", "../output"), "final", f"session_{session_id}_final.mp4")
    merger = _get_merger()
    merger.merge(clip_paths=clip_paths, bgm_path=bgm_path, output_path=output_path, bgm_volume=body.get("bgm_volume", 0.15))
    cap_gen = _get_caption_gen()
    script_combined = " ".join(s.script_text for s in scenes)
    caption_data = cap_gen.generate(script=script_combined, topic=session.topic or "", lang=session.lang)
    session.step = 5
    db.commit()
    return {"final_video_path": output_path, "caption": caption_data["caption"], "hashtags": caption_data["hashtags"]}
```

- [ ] **Step 4: Implement routers/chat.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from database import get_db
from models import SessionModel
from services.chat_handler import ChatHandler
import os

router = APIRouter()

@router.post("")
def chat(body: dict, db: DBSession = Depends(get_db)):
    session_id = body.get("session_id")
    message = body.get("message", "")
    step = body.get("step", 1)
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    session_context = {"topic": session.topic if session else None, "step": step}
    handler = ChatHandler(api_key=os.getenv("GEMINI_API_KEY", ""))
    reply = handler.chat(message=message, step=step, session_context=session_context)
    return {"reply": reply}
```

- [ ] **Step 5: Implement routers/schedule.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from database import get_db
from models import ScheduleModel
from schemas import ScheduleCreate, ScheduleOut
from typing import List

router = APIRouter()

@router.post("", response_model=ScheduleOut)
def create_schedule(data: ScheduleCreate, db: DBSession = Depends(get_db)):
    import json
    entry = ScheduleModel(
        session_id=data.session_id,
        post_time=data.post_time,
        caption=data.caption,
        hashtags=json.dumps(data.hashtags) if data.hashtags else None
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

@router.get("", response_model=List[ScheduleOut])
def list_schedule(db: DBSession = Depends(get_db)):
    return db.query(ScheduleModel).order_by(ScheduleModel.post_time).all()

@router.patch("/{schedule_id}", response_model=ScheduleOut)
def update_schedule(schedule_id: int, body: dict, db: DBSession = Depends(get_db)):
    entry = db.query(ScheduleModel).filter(ScheduleModel.id == schedule_id).first()
    if not entry:
        raise HTTPException(404, "Schedule entry not found")
    for k, v in body.items():
        setattr(entry, k, v)
    db.commit()
    db.refresh(entry)
    return entry
```

- [ ] **Step 6: Run all tests**

```bash
pytest tests/ -v
```

Expected: all tests PASS (pipeline router tests use mocks).

- [ ] **Step 7: Smoke test — start server**

```bash
uvicorn main:app --reload --port 8000
```

Expected: server starts, visit `http://localhost:8000/health` → `{"status": "ok"}`

- [ ] **Step 8: Commit**

```bash
git add backend/routers/ backend/tests/test_pipeline_router.py
git commit -m "feat: pipeline router — all 6 steps + chat + schedule endpoints wired"
```

---

## Task 13: Full Test Suite + README

**Files:**
- Create: `backend/README.md`

- [ ] **Step 1: Run full test suite**

```bash
cd backend
pytest tests/ -v --tb=short
```

Expected: all tests PASS.

- [ ] **Step 2: Create backend/README.md**

```markdown
# Milo Studio — Backend

FastAPI backend for the Milo Studio TikTok video pipeline.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in GEMINI_API_KEY and other keys
uvicorn main:app --reload --port 8000
```

## API Endpoints

- `GET /health` — health check
- `POST /sessions` — create session
- `GET /sessions` — list sessions
- `GET /sessions/{id}` — get session
- `PATCH /sessions/{id}` — update step/topic/status
- `POST /sessions/{id}/step/1a` — fetch trends
- `POST /sessions/{id}/step/1c` — generate scripts
- `POST /sessions/{id}/step/2` — split to scenes
- `POST /sessions/{id}/step/3` — assign Milo images
- `POST /sessions/{id}/step/4/{scene_id}` — gen scene video
- `POST /sessions/{id}/step/5` — merge + caption
- `GET /assets/milo?tag=happy` — list Milo images
- `POST /chat` — AI chat
- `GET /schedule` — list schedule
- `POST /schedule` — create schedule entry
```

- [ ] **Step 3: Final commit**

```bash
git add backend/README.md
git commit -m "docs: backend README + verify full test suite passes"
```

---

## Plan 2 Preview

After backend is complete and API tested, **Plan 2** covers:
- Next.js 14 project setup (TailwindCSS)
- API client (`lib/api.ts`)
- Shared components: `Stepper`, `ChatSidebar`, `NavBar`
- 6 step components: `Step1Trend` through `Step6Publish`
- `/sessions` page — session grid + resume flow
- `/schedule` page — calendar view + drag-drop reschedule
