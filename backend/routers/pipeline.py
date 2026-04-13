import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from database import get_db
from models import SessionModel, SceneModel
from services.trend_fetcher import TrendFetcher
from services.script_generator import ScriptGenerator
from services.scene_splitter import SceneSplitter
from services.asset_manager import AssetManager
from services.tts_service import TTSService
from services.video_assembler import VideoAssembler
from services.video_merger import VideoMerger
from services.caption_generator import CaptionGenerator

router = APIRouter()

CHANNEL_KEYWORDS = ["sức khoẻ", "healthy", "thực phẩm chức năng", "AI health", "sống khoẻ"]


def _get_trend_fetcher():
    return TrendFetcher(
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID", ""),
        reddit_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "MiloStudio/1.0"),
    )


def _get_script_gen():
    return ScriptGenerator(api_key=os.getenv("ANTHROPIC_API_KEY", ""))


def _get_scene_splitter():
    return SceneSplitter(api_key=os.getenv("ANTHROPIC_API_KEY", ""))


def _get_asset_manager():
    return AssetManager(os.getenv("ASSETS_DIR", "../assets"))


def _get_tts():
    return TTSService(
        output_dir=os.path.join(os.getenv("OUTPUT_DIR", "../output"), "audio")
    )


def _get_assembler():
    return VideoAssembler(
        output_dir=os.path.join(os.getenv("OUTPUT_DIR", "../output"), "scenes")
    )


def _get_merger():
    return VideoMerger(
        output_dir=os.path.join(os.getenv("OUTPUT_DIR", "../output"), "final")
    )


def _get_caption_gen():
    return CaptionGenerator(api_key=os.getenv("ANTHROPIC_API_KEY", ""))


@router.post("/{session_id}/step/1a")
def step_1a_trends(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    fetcher = _get_trend_fetcher()
    trends = fetcher.fetch(keywords=CHANNEL_KEYWORDS, lang=session.lang, limit=8)
    return trends


@router.post("/{session_id}/step/1c")
def step_1c_scripts(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session or not session.topic:
        raise HTTPException(400, "Session must have a topic set before generating scripts")
    gen = _get_script_gen()
    scripts = gen.generate_scripts(
        topic=session.topic,
        lang=session.lang,
        channel_context="Kênh Sống khoẻ cùng AI, robot mascot Milo",
        affiliate_category="thực phẩm chức năng, thiết bị sức khoẻ",
    )
    return {"scripts": scripts}


@router.post("/{session_id}/step/2")
def step_2_scenes(session_id: int, body: dict, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    script = body.get("script", "")
    splitter = _get_scene_splitter()
    raw_scenes = splitter.split(script=script, lang=session.lang)
    db.query(SceneModel).filter(SceneModel.session_id == session_id).delete()
    scene_objs = []
    for s in raw_scenes:
        scene = SceneModel(
            session_id=session_id,
            order=s["order"],
            script_text=s["text"],
            emotion_tag=s["emotion"],
        )
        db.add(scene)
        scene_objs.append(scene)
    session.step = 2
    db.commit()
    for s in scene_objs:
        db.refresh(s)
    return {
        "scenes": [
            {
                "id": s.id,
                "order": s.order,
                "script_text": s.script_text,
                "emotion_tag": s.emotion_tag,
            }
            for s in scene_objs
        ]
    }


@router.post("/{session_id}/step/3")
def step_3_images(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    scenes = (
        db.query(SceneModel)
        .filter(SceneModel.session_id == session_id)
        .order_by(SceneModel.order)
        .all()
    )
    mgr = _get_asset_manager()
    updated = []
    for scene in scenes:
        match = mgr.find_best_match(scene.emotion_tag or "explain")
        scene.image_path = match["path"] if match else None
        updated.append(
            {"id": scene.id, "image_path": scene.image_path, "emotion_tag": scene.emotion_tag}
        )
    session.step = 3
    db.commit()
    return {"scenes": updated}


@router.post("/{session_id}/step/4/{scene_id}")
def step_4_scene_video(
    session_id: int, scene_id: int, db: DBSession = Depends(get_db)
):
    scene = (
        db.query(SceneModel)
        .filter(SceneModel.id == scene_id, SceneModel.session_id == session_id)
        .first()
    )
    if not scene:
        raise HTTPException(404, "Scene not found")
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    output_dir = os.getenv("OUTPUT_DIR", "../output")
    audio_path = os.path.join(
        output_dir, "audio", f"session_{session_id}_scene_{scene_id}.mp3"
    )
    tts = _get_tts()
    tts.generate_sync(text=scene.script_text, lang=session.lang, output_path=audio_path)
    video_path = os.path.join(
        output_dir, "scenes", f"session_{session_id}_scene_{scene_id}.mp4"
    )
    assembler = _get_assembler()
    assembler.assemble(
        image_path=scene.image_path,
        audio_path=audio_path,
        caption=scene.script_text,
        output_path=video_path,
    )
    scene.audio_path = audio_path
    scene.video_path = video_path
    db.commit()
    return {"scene_id": scene_id, "video_path": video_path}


@router.post("/{session_id}/step/5")
def step_5_merge(session_id: int, body: dict, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    scenes = (
        db.query(SceneModel)
        .filter(SceneModel.session_id == session_id)
        .order_by(SceneModel.order)
        .all()
    )
    clip_paths = [s.video_path for s in scenes if s.video_path]
    bgm_path = body.get("bgm_path", "")
    output_path = os.path.abspath(os.path.join(
        os.getenv("OUTPUT_DIR", "../output"), "final", f"session_{session_id}_final.mp4"
    ))
    merger = _get_merger()
    merger.merge(
        clip_paths=clip_paths,
        bgm_path=bgm_path,
        output_path=output_path,
        bgm_volume=body.get("bgm_volume", 0.15),
    )
    try:
        cap_gen = _get_caption_gen()
        script_combined = " ".join(s.script_text for s in scenes if s.script_text)
        caption_data = cap_gen.generate(
            script=script_combined, topic=session.topic or "", lang=session.lang
        )
    except Exception:
        caption_data = {"caption": "", "hashtags": []}
    session.step = 5
    db.commit()
    return {
        "final_video_path": output_path,
        "caption": caption_data["caption"],
        "hashtags": caption_data["hashtags"],
    }
