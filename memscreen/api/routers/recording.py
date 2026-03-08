"""Recording-related HTTP routes."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from .. import deps

router = APIRouter(prefix="/recording", tags=["recording"])


class RecordingImportBody(BaseModel):
    filename: str
    duration_sec: Optional[float] = None
    mode: Optional[str] = None
    window_title: Optional[str] = None
    audio_source: Optional[str] = None


class RecordingStartBody(BaseModel):
    duration: int = 60
    interval: float = 2.0
    mode: Optional[str] = None
    region: Optional[List[float]] = None
    screen_index: Optional[int] = None
    screen_display_id: Optional[int] = None
    window_title: Optional[str] = None
    audio_source: Optional[str] = None
    video_format: Optional[str] = None
    audio_format: Optional[str] = None
    audio_denoise: Optional[bool] = None


@router.post("/start")
async def recording_start(body: RecordingStartBody):
    """Start recording (optionally set mode/region/screen first)."""
    presenter = deps.get_recording_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Recording not available")

    if body.mode:
        requested_mode = body.mode.strip().lower()
        normalized_mode = "region" if requested_mode == "window" else requested_mode
        kwargs = {}
        if normalized_mode == "region" and body.region and len(body.region) == 4:
            kwargs["bbox"] = tuple(body.region)
            if body.screen_index is not None:
                kwargs["screen_index"] = body.screen_index
            if body.screen_display_id is not None:
                kwargs["screen_display_id"] = body.screen_display_id
        elif normalized_mode == "fullscreen-single":
            if body.screen_index is not None:
                kwargs["screen_index"] = body.screen_index
            if body.screen_display_id is not None:
                kwargs["screen_display_id"] = body.screen_display_id
        if body.window_title:
            kwargs["window_title"] = body.window_title
        try:
            mode_ok = presenter.set_recording_mode(normalized_mode, **kwargs)
            if not mode_ok:
                detail = getattr(presenter, "last_start_error", None) or (
                    f"Invalid recording mode arguments: {normalized_mode}"
                )
                raise HTTPException(status_code=400, detail=detail)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    if body.audio_source:
        try:
            from memscreen.audio import AudioSource

            normalized = body.audio_source.strip().lower()
            if normalized not in {"mixed", "system_audio", "microphone", "none"}:
                raise HTTPException(status_code=400, detail=f"Invalid audio_source: {body.audio_source}")
            presenter.set_audio_source(AudioSource(normalized))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to set audio source: {e}")

    if body.video_format:
        normalized_video_format = body.video_format.strip().lower()
        if normalized_video_format not in {"mp4", "mov", "mkv", "avi"}:
            raise HTTPException(status_code=400, detail=f"Invalid video_format: {body.video_format}")
        try:
            presenter.set_video_format(normalized_video_format)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to set video format: {e}")

    if body.audio_format:
        normalized_audio_format = body.audio_format.strip().lower()
        if normalized_audio_format not in {"wav", "m4a", "mp3", "aac"}:
            raise HTTPException(status_code=400, detail=f"Invalid audio_format: {body.audio_format}")
        try:
            presenter.set_audio_output_format(normalized_audio_format)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to set audio format: {e}")

    if body.audio_denoise is not None:
        try:
            presenter.set_audio_denoise(bool(body.audio_denoise))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to set audio denoise: {e}")

    ok = await run_in_threadpool(
        presenter.start_recording,
        body.duration,
        body.interval,
    )
    if not ok:
        detail = getattr(presenter, "last_start_error", None) or "Failed to start recording"
        raise HTTPException(status_code=500, detail=detail)
    return {"ok": True}


@router.post("/stop")
async def recording_stop():
    """Stop recording."""
    presenter = deps.get_recording_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Recording not available")
    await run_in_threadpool(presenter.stop_recording)
    return {"ok": True}


@router.get("/status")
async def recording_status():
    """Get recording status and current mode."""
    presenter = deps.get_recording_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Recording not available")
    out = dict(presenter.get_recording_status())
    mode_info = presenter.get_recording_mode()
    out["mode"] = mode_info.get("mode", "fullscreen")
    out["region"] = list(mode_info["bbox"]) if mode_info.get("bbox") else None
    out["screen_index"] = mode_info.get("screen_index")
    out["screen_display_id"] = mode_info.get("screen_display_id")
    return out


@router.get("/audio/diagnose")
async def recording_audio_diagnose(source: str = Query("mixed")):
    """Diagnose audio capture readiness for selected source."""
    from memscreen.audio import AudioSource

    presenter = deps.get_recording_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Recording not available")
    normalized = source.strip().lower()
    if normalized not in {"mixed", "system_audio", "microphone", "none"}:
        raise HTTPException(status_code=400, detail=f"Invalid source: {source}")
    return await run_in_threadpool(
        presenter.audio_recorder.diagnose_source,
        AudioSource(normalized),
    )


@router.get("/screens")
async def recording_screens():
    """List available screens for fullscreen-single mode."""
    presenter = deps.get_recording_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Recording not available")
    return {"screens": presenter.get_available_screens()}


@router.post("/import")
async def recording_import(body: RecordingImportBody):
    """Import a recording file created natively into the local video catalog."""
    from memscreen.config import get_config
    from memscreen.services.recording_import import RecordingImportService

    service = RecordingImportService(str(get_config().db_path))
    result = await run_in_threadpool(
        service.import_file,
        body.filename,
        duration_sec=body.duration_sec,
        recording_mode=body.mode,
        window_title=body.window_title,
        audio_source=body.audio_source,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to import recording"))
    return result
