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
