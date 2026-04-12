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
