from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
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
    character_id = Column(Integer, nullable=True)  # soft ref to characters.id
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    scenes = relationship("SceneModel", back_populates="session", cascade="all, delete-orphan")
    schedules = relationship("ScheduleModel", back_populates="session", cascade="all, delete-orphan")

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    personality = Column(Text, nullable=True)       # personality description
    ref_image_paths = Column(Text, nullable=True)   # JSON list of local paths
    fal_image_urls = Column(Text, nullable=True)    # JSON list of fal.ai URLs
    char_description = Column(Text, nullable=True)  # auto-generated from name + personality
    created_at = Column(DateTime, default=datetime.utcnow)

class SceneModel(Base):
    __tablename__ = "scenes"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True, nullable=False)
    order = Column(Integer, nullable=False)
    script_text = Column(Text, nullable=False)
    emotion_tag = Column(String(50), nullable=True)
    act = Column(String(20), nullable=True)    # "hook" | "main" | "cta"
    action = Column(Text, nullable=True)       # Milo action description → image gen prompt
    dialogue = Column(Text, nullable=True)     # Milo spoken words → TTS
    image_path = Column(String(500), nullable=True)
    audio_path = Column(String(500), nullable=True)
    video_path = Column(String(500), nullable=True)
    approved = Column(Boolean, default=False)

    session = relationship("SessionModel", back_populates="scenes")

class ScheduleModel(Base):
    __tablename__ = "schedule"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True, nullable=False)
    post_time = Column(DateTime(timezone=True), nullable=False)
    caption = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)
    tiktok_post_id = Column(String(200), nullable=True)
    status = Column(String(20), default="pending")

    session = relationship("SessionModel", back_populates="schedules")
