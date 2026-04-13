import json
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session as DBSession
from typing import List, Optional
from database import get_db
from models import Character
from services.character_manager import CharacterManager
from services.kontext_generator import KontextGenerator

router = APIRouter()

ASSETS_DIR = os.getenv("ASSETS_DIR", "../assets")
FAL_KEY = os.getenv("FAL_KEY", "")


def _get_char_manager():
    return CharacterManager(assets_dir=ASSETS_DIR)


def _get_kontext_gen():
    return KontextGenerator(
        fal_key=FAL_KEY,
        output_dir=os.path.join(os.getenv("OUTPUT_DIR", "../output"), "images"),
    )


@router.get("/")
def list_characters(db: DBSession = Depends(get_db)):
    chars = db.query(Character).order_by(Character.created_at.desc()).all()
    return {"characters": [_serialize(c) for c in chars]}


@router.post("/")
async def create_character(
    name: str = Form(...),
    personality: str = Form(""),
    files: List[UploadFile] = File(default=[]),
    db: DBSession = Depends(get_db),
):
    mgr = _get_char_manager()
    gen = _get_kontext_gen()

    char = Character(
        name=name,
        personality=personality,
        char_description=mgr.build_char_description(name, personality),
    )
    db.add(char)
    db.commit()
    db.refresh(char)

    # Save ref images
    saved_paths = []
    for upload in files[:3]:   # max 3 images
        tmp_path = f"/tmp/char_{char.id}_{upload.filename}"
        with open(tmp_path, "wb") as f:
            content = await upload.read()
            f.write(content)
        saved_paths.append(tmp_path)

    if saved_paths:
        local_paths = mgr.save_ref_images(char.id, saved_paths)
        char.ref_image_paths = json.dumps(local_paths)

        # Upload to fal.ai for Kontext usage
        try:
            fal_urls = [gen.upload_ref_image(p) for p in local_paths]
            char.fal_image_urls = json.dumps(fal_urls)
        except Exception as e:
            # Don't fail if fal upload fails — will retry when generating
            char.fal_image_urls = json.dumps([])

        db.commit()

    return _serialize(char)


@router.get("/{char_id}")
def get_character(char_id: int, db: DBSession = Depends(get_db)):
    char = db.query(Character).filter(Character.id == char_id).first()
    if not char:
        raise HTTPException(404, "Character not found")
    return _serialize(char)


@router.delete("/{char_id}")
def delete_character(char_id: int, db: DBSession = Depends(get_db)):
    char = db.query(Character).filter(Character.id == char_id).first()
    if not char:
        raise HTTPException(404, "Character not found")
    db.delete(char)
    db.commit()
    return {"deleted": char_id}


def _serialize(c: Character) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "personality": c.personality,
        "char_description": c.char_description,
        "ref_image_count": len(json.loads(c.ref_image_paths or "[]")),
        "fal_ready": bool(json.loads(c.fal_image_urls or "[]")),
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
