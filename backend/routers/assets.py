from fastapi import APIRouter, Request
from typing import Optional

router = APIRouter()

@router.get("/milo")
def list_milo_images(request: Request, tag: Optional[str] = None):
    mgr = request.app.state.asset_manager
    if tag:
        return mgr.find_by_tag(tag)
    return mgr.list_all()
