# Milo Studio — Backend

FastAPI backend for the Milo Studio TikTok video pipeline.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in GEMINI_API_KEY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
uvicorn main:app --reload --port 8000
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Gemini 2.0 Flash API key (free tier) |
| `REDDIT_CLIENT_ID` | No | Reddit app client ID for trend fetching |
| `REDDIT_CLIENT_SECRET` | No | Reddit app secret |
| `REDDIT_USER_AGENT` | No | Reddit user agent string |
| `ASSETS_DIR` | No | Path to assets dir (default: `../assets`) |
| `OUTPUT_DIR` | No | Path to output dir (default: `../output`) |

## API Endpoints

### Health
- `GET /health` — health check

### Sessions
- `POST /sessions` — create session (`{"title": "...", "lang": "vi"}`)
- `GET /sessions` — list all sessions
- `GET /sessions/{id}` — get session with scenes
- `PATCH /sessions/{id}` — update step/topic/status
- `DELETE /sessions/{id}` — delete session

### Pipeline (6-step video creation)
- `POST /sessions/{id}/step/1a` — fetch trending topics
- `POST /sessions/{id}/step/1c` — generate 2 scripts (requires topic set)
- `POST /sessions/{id}/step/2` — split script → scenes (`{"script": "..."}`)
- `POST /sessions/{id}/step/3` — assign Milo images to scenes
- `POST /sessions/{id}/step/4/{scene_id}` — generate scene video (TTS + ken-burns)
- `POST /sessions/{id}/step/5` — merge scenes + BGM + generate caption

### Assets
- `GET /assets/milo` — list all Milo images
- `GET /assets/milo?tag=happy` — filter by emotion tag

### Chat
- `POST /chat` — AI chat (`{"session_id": 1, "message": "...", "step": 3}`)

### Schedule
- `POST /schedule` — create schedule entry
- `GET /schedule` — list all scheduled posts
- `PATCH /schedule/{id}` — update schedule entry

## Running Tests

```bash
cd backend
pytest tests/ -v
```

Expected: 33 tests passing.
