from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import List
from database import get_db
from models import ScheduleModel
from schemas import ScheduleCreate, ScheduleOut

router = APIRouter()


@router.post("", response_model=ScheduleOut)
def create_schedule(data: ScheduleCreate, db: DBSession = Depends(get_db)):
    entry = ScheduleModel(
        session_id=data.session_id,
        post_time=data.post_time,
        caption=data.caption,
        hashtags=data.hashtags,
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
