from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import SessionModel, SceneModel
from schemas import SessionCreate, SessionUpdate, SessionOut, SceneOut
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
