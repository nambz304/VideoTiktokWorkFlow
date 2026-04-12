from fastapi import APIRouter
from services.asset_manager import AssetManager
import os

router = APIRouter()
_manager = None

def get_asset_manager() -> AssetManager:
    global _manager
    if _manager is None:
        assets_dir = os.getenv("ASSETS_DIR", "../assets")
        _manager = AssetManager(assets_dir)
    return _manager

@router.get("/milo")
def list_milo_images(tag: str = None):
    mgr = get_asset_manager()
    if tag:
        return mgr.find_by_tag(tag)
    return mgr.list_all()
