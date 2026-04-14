import json
import logging
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DBSession
from database import get_db
from models import SessionModel, SceneModel, Character
from services.trend_fetcher import TrendFetcher
from services.script_generator import ScriptGenerator
from services.scene_splitter import SceneSplitter
from services.asset_manager import AssetManager
from services.tts_service import TTSService
from services.video_assembler import VideoAssembler
from services.video_merger import VideoMerger
from services.caption_generator import CaptionGenerator
from services.character_manager import CharacterManager
from services.kontext_generator import KontextGenerator

logger = logging.getLogger(__name__)

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


def _get_char_manager():
    return CharacterManager(assets_dir=os.getenv("ASSETS_DIR", "../assets"))


def _get_kontext_gen():
    return KontextGenerator(
        fal_key=os.getenv("FAL_KEY", ""),
        output_dir=os.path.join(os.getenv("OUTPUT_DIR", "../output"), "images"),
    )


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
    # Save character_id if provided
    character_id = body.get("character_id")
    if character_id:
        session.character_id = character_id
    script = body.get("script", "")
    splitter = _get_scene_splitter()
    raw_scenes = splitter.split(script=script, lang=session.lang)
    db.query(SceneModel).filter(SceneModel.session_id == session_id).delete()
    scene_objs = []
    for s in raw_scenes:
        scene = SceneModel(
            session_id=session_id,
            order=s["order"],
            script_text=s.get("action", s.get("text", "")),  # backward compat
            emotion_tag=s.get("emotion", "explain"),
            act=s.get("act"),
            action=s.get("action"),
            dialogue=s.get("dialogue"),
        )
        db.add(scene)
        scene_objs.append(scene)
    session.step = 2
    db.commit()
    for s in scene_objs:
        db.refresh(s)
    return {
        "character_id": session.character_id,
        "scenes": [
            {
                "id": s.id,
                "order": s.order,
                "act": s.act,
                "action": s.action,
                "dialogue": s.dialogue,
                "script_text": s.script_text,
                "emotion_tag": s.emotion_tag,
            }
            for s in scene_objs
        ]
    }


@router.post("/{session_id}/step/3")
def step_3_advance(session_id: int, db: DBSession = Depends(get_db)):
    """Advance session to step 3. Images are generated per-scene via /scenes/{scene_id}/image."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    session.step = 3
    db.commit()
    scenes = (
        db.query(SceneModel)
        .filter(SceneModel.session_id == session_id)
        .order_by(SceneModel.order)
        .all()
    )
    return {
        "scenes": [
            {
                "id": s.id,
                "order": s.order,
                "script_text": s.script_text,
                "emotion_tag": s.emotion_tag,
                "image_path": s.image_path,
                "act": s.act,
                "action": s.action,
                "dialogue": s.dialogue,
            }
            for s in scenes
        ]
    }


@router.post("/{session_id}/scenes/{scene_id}/image")
def generate_scene_image(session_id: int, scene_id: int, db: DBSession = Depends(get_db)):
    """Generate (or regenerate) image for a single scene via FLUX Kontext."""
    scene = (
        db.query(SceneModel)
        .filter(SceneModel.id == scene_id, SceneModel.session_id == session_id)
        .first()
    )
    if not scene:
        raise HTTPException(404, "Scene not found")
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

    character = None
    if session.character_id:
        character = db.query(Character).filter(Character.id == session.character_id).first()

    mgr = _get_char_manager()
    kontext = _get_kontext_gen()

    if character:
        fal_urls = mgr.get_fal_urls(character)
        if not fal_urls:
            ref_paths = json.loads(character.ref_image_paths or "[]")
            if ref_paths:
                try:
                    fal_urls = [kontext.upload_ref_image(p) for p in ref_paths]
                    character.fal_image_urls = json.dumps(fal_urls)
                    db.commit()
                except Exception as upload_err:
                    logger.warning(f"fal.ai upload failed: {upload_err}")
                    fal_urls = []

        if fal_urls:
            prompt = mgr.build_kontext_prompt(
                character,
                scene.action or scene.script_text,
                scene.act or "main",
            )
            filename = f"session_{session_id}_scene_{scene_id}.png"
            import time
            seed = int(time.time()) % 1000000
            try:
                image_path = kontext.generate(
                    prompt=prompt,
                    ref_image_urls=fal_urls,
                    output_filename=filename,
                    seed=seed,
                )
                scene.image_path = image_path
                db.commit()
                return {"scene_id": scene_id, "image_path": image_path}
            except Exception as e:
                logger.error(f"Kontext failed for scene {scene_id}: {e}")
                raise HTTPException(500, f"Image generation failed: {e}")
        else:
            raise HTTPException(400, "Nhân vật chưa có ref image hoặc upload fal.ai thất bại")
    else:
        # No character — fallback to sprite
        _fallback_asset(scene)
        db.commit()
        return {"scene_id": scene_id, "image_path": scene.image_path}


def _fallback_asset(scene: SceneModel):
    """Fallback: use old Milo sprite PNG."""
    from services.asset_manager import AssetManager
    asset_mgr = AssetManager(os.getenv("ASSETS_DIR", "../assets"))
    match = asset_mgr.find_best_match(scene.emotion_tag or "explain")
    scene.image_path = match["path"] if match else None


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
    tts_text = scene.dialogue or scene.script_text
    tts.generate_sync(text=tts_text, lang=session.lang, output_path=audio_path)
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


@router.get("/{session_id}/video")
def download_video(session_id: int):
    path = os.path.abspath(os.path.join(
        os.getenv("OUTPUT_DIR", "../output"), "final",
        f"session_{session_id}_final.mp4"
    ))
    if not os.path.exists(path):
        raise HTTPException(404, "Video chưa được tạo")
    return FileResponse(path, media_type="video/mp4",
                        filename=f"milo_session_{session_id}.mp4")
