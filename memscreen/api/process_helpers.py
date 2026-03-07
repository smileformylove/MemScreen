"""Helpers for process session persistence and memory linking."""

import json
from datetime import datetime, timedelta
from typing import Any, List, Optional


def _memory_result_rows(result: Any) -> List[dict]:
    """Normalize memory.get_all/search responses into a list of rows."""
    if isinstance(result, dict):
        rows = result.get("results", []) or []
        return [row for row in rows if isinstance(row, dict)]
    if isinstance(result, list):
        return [row for row in result if isinstance(row, dict)]
    return []


def parse_local_datetime(value: Any) -> Optional[datetime]:
    """Parse local naive datetime from common timestamp strings."""
    if not value:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            try:
                return value.astimezone().replace(tzinfo=None)
            except Exception:
                return value.replace(tzinfo=None)
        return value
    raw = str(value).strip().replace("Z", "+00:00")
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace(" ", "T"))
        if dt.tzinfo is not None:
            return dt.astimezone().replace(tzinfo=None)
        return dt
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            continue
    return None


def find_linked_recordings_for_range(
    *,
    session_id: int,
    events: List[dict],
    start_time: str,
    end_time: str,
    limit: int = 4,
) -> List[dict]:
    """Find recordings whose time span overlaps with the given process session."""
    from memscreen.config import get_config
    from memscreen.services import session_analysis
    from memscreen.storage import RecordingMetadataRepository
    import os

    start_dt = parse_local_datetime(start_time)
    end_dt = parse_local_datetime(end_time)
    if start_dt is None or end_dt is None or end_dt < start_dt:
        return []

    db_path = str(get_config().db_path)
    if not os.path.exists(db_path):
        return []

    linked_candidates: List[dict] = []
    try:
        rows = RecordingMetadataRepository(db_path).list_recordings(
            limit=80,
            order="rowid_desc",
        )
    except Exception:
        return []

    for row in rows:
        filename = str(row.get("filename") or "")
        ts = str(row.get("timestamp") or "")
        duration = float(row.get("duration") or 0.0)
        rec_start = parse_local_datetime(ts)
        if rec_start is None:
            continue
        rec_end = rec_start + timedelta(seconds=max(duration, 0.0))
        overlap = session_analysis.build_session_overlap_stats(
            session_id=int(session_id),
            events=events or [],
            start_time=start_time,
            end_time=end_time,
            window_start=rec_start,
            window_end=rec_end,
        )
        if not overlap:
            continue
        linked_candidates.append(
            {
                "timestamp": ts,
                "basename": os.path.basename(filename) if filename else "",
                "duration": round(duration, 2),
                "recording_mode": str(row.get("recording_mode") or ""),
                "window_title": str(row.get("window_title") or ""),
                "overlap_seconds": float(overlap.get("overlap_seconds", 0.0) or 0.0),
                "window_coverage_ratio": float(overlap.get("window_coverage_ratio", 0.0) or 0.0),
                "session_coverage_ratio": float(overlap.get("session_coverage_ratio", 0.0) or 0.0),
                "overlap_event_count": int(overlap.get("event_count", 0) or 0),
                "overlap_keystrokes": int(overlap.get("keystrokes", 0) or 0),
                "overlap_clicks": int(overlap.get("clicks", 0) or 0),
                "primary_activity": str(overlap.get("primary_activity", "") or ""),
                "overlap_summary": str(overlap.get("summary", "") or ""),
            }
        )

    linked_candidates.sort(
        key=lambda item: (
            float(item.get("overlap_seconds", 0.0) or 0.0),
            float(item.get("window_coverage_ratio", 0.0) or 0.0),
            int(item.get("overlap_event_count", 0) or 0),
            str(item.get("timestamp", "")),
        ),
        reverse=True,
    )
    return linked_candidates[:limit]


def persist_process_session_memory(
    *,
    session_id: int,
    events: List[dict],
    start_time: str,
    end_time: str,
) -> bool:
    """Persist one process session into vector memory for later chat retrieval."""
    from . import deps
    from memscreen.services import session_analysis

    memory = deps.get_memory()
    if not memory:
        return False

    try:
        event_count = len(events)
        keystrokes = sum(1 for e in events if e.get("type") == "keypress")
        clicks = sum(1 for e in events if e.get("type") == "click")
        payload = session_analysis.build_session_memory_payload(
            session_id=session_id,
            events=events,
            start_time=start_time,
            end_time=end_time,
            event_count=event_count,
            keystrokes=keystrokes,
            clicks=clicks,
        )
        linked_recordings = find_linked_recordings_for_range(
            session_id=session_id,
            events=events,
            start_time=start_time,
            end_time=end_time,
            limit=4,
        )
        if linked_recordings:
            payload["metadata"]["linked_recording_count"] = len(linked_recordings)
            payload["metadata"]["linked_recordings_json"] = json.dumps(linked_recordings, ensure_ascii=False)
            payload["metadata"]["linked_recordings"] = " | ".join(
                f"{item.get('timestamp', '')} {item.get('basename', '')} "
                f"{float(item.get('overlap_seconds', 0.0) or 0.0):.1f}s "
                f"{int(item.get('overlap_keystrokes', 0) or 0)}K/{int(item.get('overlap_clicks', 0) or 0)}M"
                for item in linked_recordings
            )
            linked_text = "; ".join(
                f"{item.get('basename', '')} "
                f"({float(item.get('overlap_seconds', 0.0) or 0.0):.1f}s overlap, "
                f"{int(item.get('overlap_keystrokes', 0) or 0)} keystrokes, "
                f"{int(item.get('overlap_clicks', 0) or 0)} clicks)"
                for item in linked_recordings
            )
            if linked_text:
                payload["memory"] += f"\nLinked recordings: {linked_text}"

        metadata = payload["metadata"]
        content = payload["memory"]
        memory_id = payload["memory_id"]

        existing_rows = _memory_result_rows(
            memory.get_all(user_id="default_user", filters={"type": "process_session", "session_id": session_id})
        )
        if existing_rows:
            existing_id = str(existing_rows[0].get("id") or "").strip()
            if existing_id:
                memory.delete(memory_id=existing_id)

        memory.add(
            content,
            user_id="default_user",
            metadata={
                **metadata,
                "memory_id": memory_id,
                "type": "process_session",
                "session_id": session_id,
            },
        )
        return True
    except Exception as e:
        print(f"[API] Failed to persist process session memory: {e}")
        return False


def delete_process_session_memory(session_id: int) -> int:
    """Delete stored memory rows for one process session."""
    from . import deps

    memory = deps.get_memory()
    if not memory:
        return 0
    try:
        rows = _memory_result_rows(
            memory.get_all(
                user_id="default_user",
                filters={"type": "process_session", "session_id": session_id},
            )
        )
        deleted = 0
        for row in rows:
            memory_id = str(row.get("id") or "").strip()
            if not memory_id:
                continue
            try:
                memory.delete(memory_id=memory_id)
                deleted += 1
            except Exception:
                continue
        return deleted
    except Exception as e:
        print(f"[API] Failed to delete process session memory: {e}")
        return 0


def delete_all_process_session_memories() -> int:
    """Delete all stored process-session memory rows."""
    from . import deps

    memory = deps.get_memory()
    if not memory:
        return 0
    try:
        rows = _memory_result_rows(
            memory.get_all(user_id="default_user", filters={"type": "process_session"})
        )
        deleted = 0
        for row in rows:
            memory_id = str(row.get("id") or "").strip()
            if not memory_id:
                continue
            try:
                memory.delete(memory_id=memory_id)
                deleted += 1
            except Exception:
                continue
        return deleted
    except Exception as e:
        print(f"[API] Failed to delete all process session memories: {e}")
        return 0
