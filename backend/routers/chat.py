import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from google.api_core.exceptions import ResourceExhausted
from database import get_db
from models import SessionModel
from services.chat_handler import GeminiHandler

router = APIRouter()


@router.post("")
def chat(body: dict, db: DBSession = Depends(get_db)):
    session_id = body.get("session_id")
    message = body.get("message", "")
    step = body.get("step", 1)
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    session_context = {"topic": session.topic if session else None, "step": step}
    handler = GeminiHandler(api_key=os.getenv("GEMINI_API_KEY", ""))
    try:
        reply = handler.chat(message=message, step=step, session_context=session_context)
    except ResourceExhausted:
        raise HTTPException(status_code=429, detail="Gemini API quota exhausted. Upgrade plan or wait.")
    return {"reply": reply}
