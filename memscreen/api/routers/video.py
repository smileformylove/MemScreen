"""Video-related HTTP routes."""

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from .. import deps

router = APIRouter(prefix="/video", tags=["video"])


class VideoReanalyzeBody(BaseModel):
    filename: str


class VideoPlayableBody(BaseModel):
    filename: str


@router.get("/list")
async def video_list():
    """List videos (metadata from VideoPresenter)."""
    presenter = deps.get_video_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Video not available")
    videos = presenter.get_video_list()
    return {"videos": [video.to_dict() for video in videos]}


@router.post("/reanalyze")
async def video_reanalyze(body: VideoReanalyzeBody):
    """Reanalyze one video with vision model and refresh content tags/summary."""
    presenter = deps.get_recording_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Recording presenter not available")

    result = await run_in_threadpool(
        presenter.reanalyze_recording_content,
        body.filename,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "reanalysis failed"))
    return result


@router.post("/playable")
async def video_playable(body: VideoPlayableBody):
    """Resolve a frontend-playable local file path (with compatibility fallback)."""
    presenter = deps.get_video_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Video not available")
    filename = str(body.filename or "").strip()
    if not filename:
        raise HTTPException(status_code=400, detail="filename is required")

    try:
        playable = await run_in_threadpool(presenter.resolve_playable_path, filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve playable path: {e}")
    return {"filename": playable}
