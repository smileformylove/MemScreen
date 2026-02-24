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

# deps imported lazily in routes so /health and /config work without heavy deps (chromadb, etc.)

app = FastAPI(
    title="MemScreen API",
    description="HTTP API for MemScreen core (Chat, Process, Recording, Video).",
    version="0.1.0",
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


class ProcessSaveSessionBody(BaseModel):
    events: List[dict]
    start_time: str
    end_time: str


class RecordingStartBody(BaseModel):
    duration: int = 60
    interval: float = 2.0
    mode: Optional[str] = None  # fullscreen, fullscreen-single, region
    region: Optional[List[float]] = None  # [left, top, right, bottom]
    screen_index: Optional[int] = None
    window_title: Optional[str] = None


class VideoReanalyzeBody(BaseModel):
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
    if len(session_events) <= 1:
        raise HTTPException(status_code=400, detail="Not enough events to save (need at least 2)")
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
        kwargs = {}
        if body.mode == "region" and body.region and len(body.region) == 4:
            kwargs["bbox"] = tuple(body.region)
            if body.screen_index is not None:
                kwargs["screen_index"] = body.screen_index
        elif body.mode == "fullscreen-single" and body.screen_index is not None:
            kwargs["screen_index"] = body.screen_index
        if body.window_title:
            kwargs["window_title"] = body.window_title
        try:
            mode_ok = presenter.set_recording_mode(body.mode, **kwargs)
            if not mode_ok:
                detail = getattr(presenter, "last_start_error", None) or f"Invalid recording mode arguments: {body.mode}"
                raise HTTPException(status_code=400, detail=detail)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
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
