"""
FastAPI application for MemScreen Core API.
Serves Flutter and other frontends; does not modify Kivy or start.py.
"""

import asyncio
import json
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Any, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from memscreen.version import __version__

# deps imported lazily in routes so /health and /config work without heavy deps (chromadb, etc.)

app = FastAPI(
    title="MemScreen API",
    description="HTTP API for MemScreen core (Chat, Process, Recording, Video).",
    version=__version__,
)

_executor = ThreadPoolExecutor(max_workers=2)


# ---------- Request/Response models ----------

class ChatMessageBody(BaseModel):
    message: str


class ChatReplyResponse(BaseModel):
    reply: Optional[str] = None
    error: Optional[str] = None


class SetModelBody(BaseModel):
    model: str


class ModelDownloadBody(BaseModel):
    model: str
    timeout_sec: int = 1800


class ProcessSaveSessionBody(BaseModel):
    events: List[dict]
    start_time: str
    end_time: str


class RecordingStartBody(BaseModel):
    duration: int = 60
    interval: float = 2.0
    mode: Optional[str] = None  # fullscreen, fullscreen-single, region (legacy: window)
    region: Optional[List[float]] = None  # [left, top, right, bottom]
    screen_index: Optional[int] = None
    screen_display_id: Optional[int] = None
    window_title: Optional[str] = None
    audio_source: Optional[str] = None  # mixed, system_audio, microphone, none
    video_format: Optional[str] = None  # mp4, mov, mkv, avi
    audio_format: Optional[str] = None  # wav, m4a, mp3, aac
    audio_denoise: Optional[bool] = None  # basic ffmpeg denoise filter


class VideoReanalyzeBody(BaseModel):
    filename: str


class VideoPlayableBody(BaseModel):
    filename: str


# ---------- Chat ----------

@app.post("/chat", response_model=ChatReplyResponse)
async def chat_post(body: ChatMessageBody):
    """Non-streaming chat: send message, get full reply."""
    from . import deps
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    loop = asyncio.get_event_loop()
    result = [None, None]  # [ai_text, error_text]
    done = threading.Event()

    def on_done(ai_text: str, error_text: Optional[str]):
        result[0], result[1] = ai_text, error_text
        done.set()

    presenter.send_message_sync(body.message, on_done=on_done)
    await loop.run_in_executor(_executor, lambda: done.wait(180))
    ai_text, error_text = result[0], result[1]
    if ai_text is None and error_text is None:
        return ChatReplyResponse(reply=None, error="Chat request timed out")
    if error_text:
        return ChatReplyResponse(reply=None, error=error_text)
    return ChatReplyResponse(reply=ai_text, error=None)


@app.post("/chat/stream")
async def chat_stream(body: ChatMessageBody):
    """Stream chat response via SSE. Chunks pushed from presenter thread via queue."""
    from . import deps
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")

    chunk_queue: queue.Queue = queue.Queue()
    full_response = [None]
    SENTINEL = object()

    class StreamView:
        def on_message_added(self, role: str, content: str):
            pass

        def on_response_started(self):
            pass

        def on_response_chunk(self, chunk: str):
            chunk_queue.put(chunk)

        def on_response_completed(self, full: str):
            full_response[0] = full
            chunk_queue.put(SENTINEL)

    stream_view = StreamView()
    presenter.set_view(stream_view)

    def run_stream():
        # Use send_message_sync for reliable, simple flow (same as Kivy)
        def on_done(ai_text: str, error_text: Optional[str]):
            if error_text:
                chunk_queue.put({"error": error_text})
            else:
                full_response[0] = ai_text
                # Send full response as one chunk
                chunk_queue.put(ai_text)
            chunk_queue.put(SENTINEL)

        presenter.send_message_sync(body.message, on_done=on_done)

    loop = asyncio.get_event_loop()
    loop.run_in_executor(_executor, run_stream)

    async def event_stream():
        while True:
            try:
                item = chunk_queue.get_nowait()
            except queue.Empty:
                if full_response[0] is not None:
                    break
                await asyncio.sleep(0.05)
                continue
            if item is SENTINEL:
                break
            if isinstance(item, dict) and "error" in item:
                yield f"data: {json.dumps({'error': item['error']})}\n\n"
                break
            yield f"data: {json.dumps({'chunk': item})}\n\n"
        if full_response[0] is not None:
            yield f"data: {json.dumps({'done': True, 'full': full_response[0]})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/chat/models")
async def chat_get_models():
    """List available models."""
    from . import deps
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    return {"models": presenter.get_available_models()}


@app.get("/chat/model")
async def chat_get_model():
    """Get current model."""
    from . import deps
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    return {"model": presenter.get_current_model()}


@app.put("/chat/model")
async def chat_set_model(body: SetModelBody):
    """Set current model."""
    from . import deps
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    ok = presenter.set_model(body.model)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Model not available: {body.model}")
    return {"model": presenter.get_current_model()}


@app.get("/models/catalog")
async def models_catalog():
    """List required local models with install status from Ollama runtime."""
    from memscreen.config import get_config
    import os
    import requests

    cfg = get_config()
    base_url = cfg.ollama_base_url.rstrip("/")
    disable_models = os.getenv("MEMSCREEN_DISABLE_MODELS", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    required_specs = [
        (cfg.ollama_llm_model, "Chat", True),
        (cfg.ollama_vision_model, "Video tags", True),
        (cfg.ollama_embedding_model, "Memory retrieval", True),
        ("qwen2.5vl:7b", "Advanced vision (optional)", False),
    ]

    deduped_specs = []
    seen_names = set()
    for name, purpose, required in required_specs:
        clean = str(name or "").strip()
        if not clean or clean in seen_names:
            continue
        seen_names.add(clean)
        deduped_specs.append((clean, purpose, required))

    installed = {}
    runtime_ready = False
    runtime_error = None
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=4)
        if resp.status_code != 200:
            runtime_error = f"HTTP {resp.status_code}"
        else:
            runtime_ready = True
            payload = resp.json() if resp.content else {}
            for item in payload.get("models", []) or []:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                installed[name] = {
                    "size_bytes": item.get("size"),
                    "modified_at": item.get("modified_at"),
                }
    except Exception as e:
        runtime_error = str(e)

    def _split_model_ref(name: str):
        clean = str(name or "").strip().lower()
        if not clean:
            return "", None
        if ":" in clean:
            base, tag = clean.rsplit(":", 1)
            if base and tag and "/" not in tag:
                return base, tag
        return clean, None

    def _find_installed_model(name: str):
        req_base, req_tag = _split_model_ref(name)
        if not req_base:
            return None, {}
        for installed_name, meta in installed.items():
            ins_base, ins_tag = _split_model_ref(installed_name)
            if ins_base != req_base:
                continue
            if req_tag is None:
                return installed_name, meta
            if ins_tag == req_tag:
                return installed_name, meta
            if req_tag == "latest" and ins_tag is None:
                return installed_name, meta
        return None, {}

    models = []
    for name, purpose, required in deduped_specs:
        matched_name, meta = _find_installed_model(name)
        models.append(
            {
                "name": name,
                "purpose": purpose,
                "required": required,
                "installed": matched_name is not None,
                "installed_name": matched_name,
                "size_bytes": meta.get("size_bytes"),
                "modified_at": meta.get("modified_at"),
            }
        )

    return {
        "base_url": base_url,
        "models_disabled": disable_models,
        "runtime_ready": runtime_ready,
        "runtime_error": runtime_error,
        "models": models,
    }


@app.post("/models/download")
async def models_download(body: ModelDownloadBody):
    """Download one local model through Ollama runtime."""
    from memscreen.config import get_config
    import subprocess
    import time
    import shutil
    import requests

    model_name = str(body.model or "").strip()
    if not model_name:
        raise HTTPException(status_code=400, detail="model is required")

    timeout_sec = int(body.timeout_sec) if int(body.timeout_sec) > 0 else 1800
    timeout_sec = max(60, min(timeout_sec, 7200))
    base_url = get_config().ollama_base_url.rstrip("/")

    def _ensure_ollama_runtime() -> bool:
        try:
            health = requests.get(f"{base_url}/api/tags", timeout=2)
            if health.status_code == 200:
                return True
        except Exception:
            pass

        ollama_bin = shutil.which("ollama")
        if not ollama_bin:
            return False

        try:
            subprocess.Popen(
                [ollama_bin, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception:
            return False

        for _ in range(6):
            try:
                health = requests.get(f"{base_url}/api/tags", timeout=2)
                if health.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(1.0)
        return False

    def _pull():
        if not _ensure_ollama_runtime():
            return {
                "ok": False,
                "error": "Ollama runtime is unavailable. Please start Ollama and retry.",
            }

        try:
            response = requests.post(
                f"{base_url}/api/pull",
                json={"name": model_name, "stream": False},
                timeout=timeout_sec,
            )
        except Exception as e:
            return {"ok": False, "error": f"Ollama is unavailable: {e}"}

        if response.status_code != 200:
            detail = ""
            try:
                payload = response.json()
                detail = str(payload.get("error") or payload.get("detail") or "").strip()
            except Exception:
                detail = response.text.strip()
            error = (
                f"Model download failed (HTTP {response.status_code})"
                + (f": {detail}" if detail else "")
            )
            return {"ok": False, "error": error}

        status_text = "success"
        try:
            payload = response.json() if response.content else {}
            status_text = str(payload.get("status") or payload.get("detail") or "success")
        except Exception:
            pass
        return {"ok": True, "status": status_text}

    result = await asyncio.get_event_loop().run_in_executor(_executor, _pull)
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error", "Model download failed"))
    return {
        "ok": True,
        "model": model_name,
        "status": result.get("status", "success"),
    }


@app.get("/chat/history")
async def chat_get_history():
    """Get current conversation history."""
    from . import deps
    presenter = deps.get_chat_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Chat not available")
    history = presenter.get_conversation_history()
    return {
        "messages": [
            {"role": m.role, "content": m.content}
            for m in history
        ]
    }


# ---------- Process (session_analysis) ----------

@app.get("/process/sessions")
async def process_get_sessions(limit: int = Query(20, ge=1, le=100)):
    """List sessions."""
    from . import deps
    from memscreen.services import session_analysis
    db_path = deps.get_process_db_path()
    rows = session_analysis.load_sessions(limit=limit, db_path=db_path)
    return {
        "sessions": [
            {
                "id": r[0],
                "start_time": r[1],
                "end_time": r[2],
                "event_count": r[3],
                "keystrokes": r[4],
                "clicks": r[5],
            }
            for r in rows
        ]
    }


@app.post("/process/sessions")
async def process_save_session(body: ProcessSaveSessionBody):
    """Save a session."""
    from . import deps
    from memscreen.services import session_analysis
    db_path = deps.get_process_db_path()
    session_analysis.save_session(
        events=body.events,
        start_time=body.start_time,
        end_time=body.end_time,
        db_path=db_path,
    )
    return {"ok": True}


@app.get("/process/sessions/{session_id}")
async def process_get_session_events(session_id: int):
    """Get events for one session."""
    from . import deps
    from memscreen.services import session_analysis
    db_path = deps.get_process_db_path()
    events = session_analysis.get_session_events(session_id=session_id, db_path=db_path)
    if events is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"events": events}


@app.get("/process/sessions/{session_id}/analysis")
async def process_get_session_analysis(session_id: int):
    """Get analysis for one session (backend loads metadata from DB)."""
    from . import deps
    from memscreen.services import session_analysis
    import sqlite3
    db_path = deps.get_process_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, start_time, end_time, event_count, keystrokes, clicks FROM sessions WHERE id=?",
        (session_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    _id, start_time, end_time, event_count, keystrokes, clicks = row
    result = session_analysis.get_session_analysis(
        session_id=session_id,
        event_count=event_count,
        keystrokes=keystrokes,
        clicks=clicks,
        start_time=start_time,
        end_time=end_time,
        db_path=db_path,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@app.delete("/process/sessions/{session_id}")
async def process_delete_session(session_id: int):
    """Delete one session."""
    from . import deps
    from memscreen.services import session_analysis
    db_path = deps.get_process_db_path()
    n = session_analysis.delete_session(session_id=session_id, db_path=db_path)
    return {"deleted": n}


@app.delete("/process/sessions")
async def process_delete_all_sessions():
    """Delete all sessions."""
    from . import deps
    from memscreen.services import session_analysis
    db_path = deps.get_process_db_path()
    n = session_analysis.delete_all_sessions(db_path=db_path)
    return {"deleted": n}


# ---------- Process: Keyboard/Mouse Tracking (InputTracker) ----------

@app.post("/process/tracking/start")
async def process_tracking_start():
    """Start keyboard/mouse tracking on the backend machine (same behavior as Kivy tracking start)."""
    from . import deps
    presenter = deps.get_process_mining_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Process mining not available")
    try:
        ok = await asyncio.get_event_loop().run_in_executor(_executor, lambda: presenter.start_tracking())
        if not ok:
            raise HTTPException(status_code=400, detail="Tracking already active or failed to start")
        return {"ok": True, "is_tracking": True}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.post("/process/tracking/stop")
async def process_tracking_stop():
    """Stop keyboard/mouse tracking."""
    from . import deps
    presenter = deps.get_process_mining_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Process mining not available")
    ok = await asyncio.get_event_loop().run_in_executor(_executor, lambda: presenter.stop_tracking())
    return {"ok": True, "is_tracking": False}


@app.get("/process/tracking/status")
async def process_tracking_status():
    """Get tracking status (is_tracking, event_count). Refreshes event_count from tracker when tracking."""
    from . import deps
    presenter = deps.get_process_mining_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Process mining not available")
    if presenter.is_tracking:
        # Refresh event count from InputTracker
        await asyncio.get_event_loop().run_in_executor(
            _executor, lambda: presenter.get_recent_events(limit=10000)
        )
    return presenter.get_tracking_status()


@app.post("/process/tracking/mark-start")
async def process_tracking_mark_start():
    """Mark a new tracking baseline while current tracking remains active."""
    from . import deps
    presenter = deps.get_process_mining_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Process mining not available")
    ok = await asyncio.get_event_loop().run_in_executor(
        _executor, lambda: presenter.mark_tracking_baseline()
    )
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Tracking is not active, cannot mark baseline",
        )
    return {"ok": True}


@app.post("/process/sessions/from-tracking")
async def process_save_session_from_tracking():
    """Save current session from recent keyboard/mouse events (same behavior as Kivy save-current-session)."""
    import datetime
    from . import deps
    from memscreen.services import session_analysis
    presenter = deps.get_process_mining_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Process mining not available")
    events_raw = await asyncio.get_event_loop().run_in_executor(
        _executor, lambda: presenter.get_recent_events(limit=10000)
    )
    if not events_raw:
        raise HTTPException(status_code=400, detail="No events to save")
    # Convert to session format (type, text, time) and chronological order (raw is DESC)
    def _to_local_dt(ts_value):
        # Normalize timestamp from tracker DB to local datetime.
        if isinstance(ts_value, datetime.datetime):
            if ts_value.tzinfo is not None:
                return ts_value.astimezone().replace(tzinfo=None)
            return ts_value
        if not isinstance(ts_value, str):
            return datetime.datetime.now()

        raw = ts_value.strip()
        if not raw:
            return datetime.datetime.now()

        # ISO-like: supports offset and Z.
        try:
            iso_raw = raw.replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(iso_raw)
            if dt.tzinfo is not None:
                return dt.astimezone().replace(tzinfo=None)
            return dt
        except Exception:
            pass

        # Legacy SQLite CURRENT_TIMESTAMP format is UTC without timezone.
        try:
            dt = datetime.datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=datetime.timezone.utc).astimezone().replace(tzinfo=None)
        except Exception:
            return datetime.datetime.now()

    session_events = []
    for event in events_raw:
        operate_type = (event.get("operate_type") or "").strip().lower()
        action = (event.get("action") or "").strip().lower()
        ts = _to_local_dt(event.get("timestamp"))
        time_str = ts.strftime("%Y-%m-%d %H:%M:%S")

        # Keep session metrics meaningful:
        # - keyboard press => keypress
        # - mouse press => click
        # - mouse move => skip (too noisy)
        if operate_type == "keyboard":
            if action != "press":
                continue
            event_type = "keypress"
        elif operate_type == "mouse":
            if action in {"move", "scroll"}:
                continue
            if action == "press":
                event_type = "click"
            else:
                continue
        else:
            continue

        text = f"{operate_type}: {action}"
        if event.get("content"):
            text += f" ({event['content']})"
        session_events.append({"time": time_str, "text": text, "type": event_type, "_dt": ts})
    if len(session_events) < 1:
        raise HTTPException(status_code=400, detail="No meaningful events to save")
    session_events.sort(key=lambda e: e["_dt"])
    start_time = session_events[0]["time"]
    end_time = session_events[-1]["time"]
    for e in session_events:
        e.pop("_dt", None)
    db_path = deps.get_process_db_path()
    await asyncio.get_event_loop().run_in_executor(
        _executor,
        lambda: session_analysis.save_session(
            events=session_events, start_time=start_time, end_time=end_time, db_path=db_path
        ),
    )
    # Advance baseline after saving so repeated saves do not include already-saved history.
    await asyncio.get_event_loop().run_in_executor(
        _executor, lambda: presenter.advance_tracking_baseline()
    )
    return {"ok": True, "events_saved": len(session_events), "start_time": start_time, "end_time": end_time}


# ---------- Recording ----------

@app.post("/recording/start")
async def recording_start(body: RecordingStartBody):
    """Start recording (optionally set mode/region/screen first)."""
    from . import deps
    presenter = deps.get_recording_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Recording not available")
    if body.mode:
        requested_mode = body.mode.strip().lower()
        # Backward compatibility for old clients.
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
                detail = getattr(presenter, "last_start_error", None) or f"Invalid recording mode arguments: {normalized_mode}"
                raise HTTPException(status_code=400, detail=detail)
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
    ok = await asyncio.get_event_loop().run_in_executor(
        _executor,
        lambda: presenter.start_recording(duration=body.duration, interval=body.interval),
    )
    if not ok:
        detail = getattr(presenter, "last_start_error", None) or "Failed to start recording"
        raise HTTPException(status_code=500, detail=detail)
    return {"ok": True}


@app.post("/recording/stop")
async def recording_stop():
    """Stop recording."""
    from . import deps
    presenter = deps.get_recording_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Recording not available")
    await asyncio.get_event_loop().run_in_executor(_executor, lambda: presenter.stop_recording())
    return {"ok": True}


@app.get("/recording/status")
async def recording_status():
    """Get recording status and current mode (fullscreen / fullscreen-single / region)."""
    from . import deps
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


@app.get("/recording/audio/diagnose")
async def recording_audio_diagnose(source: str = Query("mixed")):
    """Diagnose audio capture readiness for selected source."""
    from . import deps
    from memscreen.audio import AudioSource

    presenter = deps.get_recording_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Recording not available")
    normalized = source.strip().lower()
    if normalized not in {"mixed", "system_audio", "microphone", "none"}:
        raise HTTPException(status_code=400, detail=f"Invalid source: {source}")
    out = await asyncio.get_event_loop().run_in_executor(
        _executor,
        lambda: presenter.audio_recorder.diagnose_source(AudioSource(normalized)),
    )
    return out


@app.get("/recording/screens")
async def recording_screens():
    """List available screens for fullscreen-single mode (index, name, width, height, is_primary)."""
    from . import deps
    presenter = deps.get_recording_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Recording not available")
    return {"screens": presenter.get_available_screens()}


# ---------- Video ----------

@app.get("/video/list")
async def video_list():
    """List videos (metadata from VideoPresenter)."""
    from . import deps
    presenter = deps.get_video_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Video not available")
    videos = presenter.get_video_list()
    return {"videos": [v.to_dict() for v in videos]}


@app.post("/video/reanalyze")
async def video_reanalyze(body: VideoReanalyzeBody):
    """Reanalyze one video with vision model and refresh content tags/summary."""
    from . import deps
    presenter = deps.get_recording_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Recording presenter not available")

    result = await asyncio.get_event_loop().run_in_executor(
        _executor,
        lambda: presenter.reanalyze_recording_content(body.filename),
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "reanalysis failed"))
    return result


@app.post("/video/playable")
async def video_playable(body: VideoPlayableBody):
    """Resolve a frontend-playable local file path (with compatibility fallback)."""
    from . import deps
    presenter = deps.get_video_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Video not available")
    filename = str(body.filename or "").strip()
    if not filename:
        raise HTTPException(status_code=400, detail="filename is required")

    try:
        playable = await asyncio.get_event_loop().run_in_executor(
            _executor,
            lambda: presenter.resolve_playable_path(filename),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve playable path: {e}")
    return {"filename": playable}


# ---------- Config & Health ----------

@app.get("/config")
async def get_config_readonly():
    """Read-only config for Flutter (ollama URL, db path, etc.)."""
    from memscreen.config import get_config
    c = get_config()
    return {
        "ollama_base_url": c.ollama_base_url,
        "db_dir": str(c.db_dir),
        "videos_dir": str(c.videos_dir),
    }


@app.get("/health")
async def health():
    """Health check (process alive; optional Ollama/DB)."""
    out = {"status": "ok"}
    try:
        from memscreen.config import get_config
        c = get_config()
        import requests
        r = requests.get(f"{c.ollama_base_url}/api/tags", timeout=2)
        out["ollama"] = "ok" if r.status_code == 200 else f"status_{r.status_code}"
    except Exception as e:
        out["ollama"] = f"error: {str(e)}"
    try:
        from memscreen.config import get_config
        c = get_config()
        import sqlite3
        conn = sqlite3.connect(str(c.db_path))
        conn.close()
        out["db"] = "ok"
    except Exception as e:
        out["db"] = f"error: {str(e)}"
    return out


# Fix /config: use get_config from config module
def _get_config():
    from memscreen.config import get_config
    return get_config()
