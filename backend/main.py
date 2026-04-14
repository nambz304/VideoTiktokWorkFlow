from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from database import engine, Base
from routers import sessions, pipeline, schedule, assets, chat, characters as characters_router
from services.asset_manager import AssetManager
import os

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.asset_manager = AssetManager(os.getenv("ASSETS_DIR", "../assets"))
    Base.metadata.create_all(bind=engine)
    output_dir = os.getenv("OUTPUT_DIR", "../output")
    for sub in ("audio", "scenes", "images", "final"):
        os.makedirs(os.path.join(output_dir, sub), exist_ok=True)
    yield

app = FastAPI(title="Milo Studio API", version="1.0.0", lifespan=lifespan)

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
app.include_router(characters_router.router, prefix="/characters", tags=["characters"])

app.mount("/static", StaticFiles(directory=os.getenv("ASSETS_DIR", "../assets")), name="static")
app.mount("/output", StaticFiles(directory=os.getenv("OUTPUT_DIR", "../output")), name="output")

@app.get("/health")
def health():
    return {"status": "ok"}
