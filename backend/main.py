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
