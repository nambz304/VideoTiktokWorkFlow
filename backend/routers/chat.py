import os
import anthropic
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from database import get_db
from models import SessionModel
from services.chat_handler import ClaudeHandler

router = APIRouter()


@router.post("")
def chat(body: dict, db: DBSession = Depends(get_db)):
    session_id = body.get("session_id")
    message = body.get("message", "")
    step = body.get("step", 1)
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    session_context = {"topic": session.topic if session else None, "step": step}
    handler = ClaudeHandler(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
    try:
        reply = handler.chat(message=message, step=step, session_context=session_context)
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="Claude API rate limit hit. Retry later.")
    return {"reply": reply}
