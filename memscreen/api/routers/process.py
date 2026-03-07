"""Process-session and tracking HTTP routes."""

import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from .. import deps
from ..process_helpers import (
    delete_all_process_session_memories,
    delete_process_session_memory,
    persist_process_session_memory,
)
from memscreen.services import session_analysis

router = APIRouter(prefix="/process", tags=["process"])


class ProcessSaveSessionBody(BaseModel):
    events: List[dict]
    start_time: str
    end_time: str


def _tracking_timestamp_to_local_datetime(ts_value):
    if isinstance(ts_value, datetime.datetime):
        if ts_value.tzinfo is not None:
            return ts_value.astimezone().replace(tzinfo=None)
        return ts_value
    if not isinstance(ts_value, str):
        return datetime.datetime.now()

    raw = ts_value.strip()
    if not raw:
        return datetime.datetime.now()

    try:
        iso_raw = raw.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(iso_raw)
        if dt.tzinfo is not None:
            return dt.astimezone().replace(tzinfo=None)
        return dt
    except Exception:
        pass

    try:
        dt = datetime.datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=datetime.timezone.utc).astimezone().replace(tzinfo=None)
    except Exception:
        return datetime.datetime.now()


@router.get("/sessions")
async def process_get_sessions(limit: int = Query(20, ge=1, le=100)):
    """List sessions."""
    db_path = deps.get_process_db_path()
    rows = await run_in_threadpool(session_analysis.load_sessions, limit, db_path)
    return {
        "sessions": [
            {
                "id": row[0],
                "start_time": row[1],
                "end_time": row[2],
                "event_count": row[3],
                "keystrokes": row[4],
                "clicks": row[5],
            }
            for row in rows
        ]
    }


@router.post("/sessions")
async def process_save_session(body: ProcessSaveSessionBody):
    """Save a session."""
    db_path = deps.get_process_db_path()
    session_id = await run_in_threadpool(
        session_analysis.save_session,
        body.events,
        body.start_time,
        body.end_time,
        db_path,
    )
    await run_in_threadpool(
        persist_process_session_memory,
        session_id=session_id,
        events=body.events,
        start_time=body.start_time,
        end_time=body.end_time,
    )
    return {"ok": True, "session_id": session_id}


@router.post("/sessions/from-tracking")
async def process_save_session_from_tracking():
    """Save current session from recent keyboard/mouse events."""
    presenter = deps.get_process_mining_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Process mining not available")

    events_raw = await run_in_threadpool(presenter.get_recent_events, 10000)
    if not events_raw:
        raise HTTPException(status_code=400, detail="No events to save")

    session_events = []
    for event in events_raw:
        operate_type = (event.get("operate_type") or "").strip().lower()
        action = (event.get("action") or "").strip().lower()
        ts = _tracking_timestamp_to_local_datetime(event.get("timestamp"))
        time_str = ts.strftime("%Y-%m-%d %H:%M:%S")

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

    session_events.sort(key=lambda event: event["_dt"])
    start_time = session_events[0]["time"]
    end_time = session_events[-1]["time"]
    for event in session_events:
        event.pop("_dt", None)

    db_path = deps.get_process_db_path()
    session_id = await run_in_threadpool(
        session_analysis.save_session,
        session_events,
        start_time,
        end_time,
        db_path,
    )
    await run_in_threadpool(
        persist_process_session_memory,
        session_id=session_id,
        events=session_events,
        start_time=start_time,
        end_time=end_time,
    )
    await run_in_threadpool(presenter.advance_tracking_baseline)
    return {
        "ok": True,
        "session_id": session_id,
        "events_saved": len(session_events),
        "start_time": start_time,
        "end_time": end_time,
    }


@router.get("/sessions/{session_id}")
async def process_get_session_events(session_id: int):
    """Get events for one session."""
    db_path = deps.get_process_db_path()
    events = await run_in_threadpool(session_analysis.get_session_events, session_id, db_path)
    if events is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"events": events}


@router.get("/sessions/{session_id}/analysis")
async def process_get_session_analysis(session_id: int):
    """Get analysis for one session."""
    db_path = deps.get_process_db_path()
    row = await run_in_threadpool(session_analysis.get_session_summary, session_id, db_path)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    _, start_time, end_time, event_count, keystrokes, clicks = row
    result = await run_in_threadpool(
        session_analysis.get_session_analysis,
        session_id,
        event_count,
        keystrokes,
        clicks,
        start_time,
        end_time,
        db_path,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.delete("/sessions/{session_id}")
async def process_delete_session(session_id: int):
    """Delete one session."""
    db_path = deps.get_process_db_path()
    deleted = await run_in_threadpool(session_analysis.delete_session, session_id, db_path)
    memory_deleted = await run_in_threadpool(delete_process_session_memory, session_id)
    return {"deleted": deleted, "memory_deleted": memory_deleted}


@router.delete("/sessions")
async def process_delete_all_sessions():
    """Delete all sessions."""
    db_path = deps.get_process_db_path()
    deleted = await run_in_threadpool(session_analysis.delete_all_sessions, db_path)
    memory_deleted = await run_in_threadpool(delete_all_process_session_memories)
    return {"deleted": deleted, "memory_deleted": memory_deleted}


@router.post("/tracking/start")
async def process_tracking_start():
    """Start keyboard/mouse tracking on the backend machine."""
    presenter = deps.get_process_mining_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Process mining not available")
    try:
        ok = await run_in_threadpool(presenter.start_tracking)
        if not ok:
            raise HTTPException(status_code=400, detail="Tracking already active or failed to start")
        return {"ok": True, "is_tracking": True}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/tracking/stop")
async def process_tracking_stop():
    """Stop keyboard/mouse tracking."""
    presenter = deps.get_process_mining_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Process mining not available")
    await run_in_threadpool(presenter.stop_tracking)
    return {"ok": True, "is_tracking": False}


@router.get("/tracking/status")
async def process_tracking_status():
    """Get tracking status and refresh event_count when tracking."""
    presenter = deps.get_process_mining_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Process mining not available")
    if presenter.is_tracking:
        await run_in_threadpool(presenter.get_recent_events, 10000)
    return presenter.get_tracking_status()


@router.post("/tracking/mark-start")
async def process_tracking_mark_start():
    """Mark a new tracking baseline while current tracking remains active."""
    presenter = deps.get_process_mining_presenter()
    if not presenter:
        raise HTTPException(status_code=503, detail="Process mining not available")
    ok = await run_in_threadpool(presenter.mark_tracking_baseline)
    if not ok:
        raise HTTPException(status_code=400, detail="Tracking is not active, cannot mark baseline")
    return {"ok": True}
