"""
Process Mining session storage and analysis (Core).
Moved from UI: same logic, same DB schema (process_mining.db, sessions table).
"""

import json
import os
import sqlite3
import datetime
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple


DEFAULT_DB_PATH = "./db/process_mining.db"


def _ensure_db_dir(db_path: str) -> None:
    d = os.path.dirname(db_path)
    if d:
        os.makedirs(d, exist_ok=True)


def _parse_datetime_value(
    value: Any,
    reference: Optional[datetime.datetime] = None,
) -> Optional[datetime.datetime]:
    """Parse a naive local datetime from common timestamp formats."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        if value.tzinfo is not None:
            try:
                return value.astimezone().replace(tzinfo=None)
            except Exception:
                return value.replace(tzinfo=None)
        return value

    raw = str(value).strip()
    if not raw:
        return None

    try:
        dt = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00").replace(" ", "T"))
        if dt.tzinfo is not None:
            return dt.astimezone().replace(tzinfo=None)
        return dt
    except Exception:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M:%S"):
        try:
            dt = datetime.datetime.strptime(raw, fmt)
            if fmt == "%H:%M:%S" and reference is not None:
                return datetime.datetime.combine(reference.date(), dt.time())
            return dt
        except Exception:
            continue
    return None


def _extract_event_datetime(
    event: Dict[str, Any],
    reference: Optional[datetime.datetime] = None,
) -> Optional[datetime.datetime]:
    """Extract event time from either the session or tracker event schema."""
    if not isinstance(event, dict):
        return None
    for key in ("time", "timestamp"):
        dt = _parse_datetime_value(event.get(key), reference=reference)
        if dt is not None:
            return dt
    return None


def categorize_activities(events: List[Dict]) -> Dict[str, Any]:
    """Categorize events into detailed activity types (same logic as former UI _categorize_activities)."""
    typing_score = 0
    browsing_score = 0
    design_score = 0
    programming_score = 0
    communication_score = 0
    document_score = 0
    gaming_score = 0
    other_score = 0

    for event in events:
        event_type = event.get("type", "")
        text = event.get("text", "").lower()

        if event_type == "keypress":
            typing_score += 1

        if any(word in text for word in ["scroll", "browser", "chrome", "safari", "firefox", "edge", "webkit", "navigator"]):
            browsing_score += 2

        if any(word in text for word in ["figma", "sketch", "design", "draw", "paint", "canvas", "adobe", "photoshop", "illustrator"]):
            design_score += 3

        if any(word in text for word in ["code", "python", "javascript", "java", "terminal", "console", "debug", "compile", "git", "vscode", "intellij", "vim", "emacs", "function", "class", "import"]):
            programming_score += 3

        if any(word in text for word in ["slack", "teams", "zoom", "meet", "chat", "message", "email", "outlook", "telegram", "whatsapp", "discord"]):
            communication_score += 2

        if any(word in text for word in ["word", "excel", "powerpoint", "docs", "sheets", "slides", "notion", "evernote", "text", "edit", "document", "write"]):
            document_score += 2

        if any(word in text for word in ["game", "play", "steam", "epic", "minecraft", "lol", "valorant", "overwatch", "fps", "rpg"]):
            gaming_score += 3

        other_score += 0.5

    total = typing_score + browsing_score + design_score + programming_score + communication_score + document_score + gaming_score + other_score

    if total == 0:
        return {
            'typing': {'score': 0, 'percentage': 0},
            'browsing': {'score': 0, 'percentage': 0},
            'design': {'score': 0, 'percentage': 0},
            'programming': {'score': 0, 'percentage': 0},
            'communication': {'score': 0, 'percentage': 0},
            'document': {'score': 0, 'percentage': 0},
            'gaming': {'score': 0, 'percentage': 0},
            'other': {'score': 0, 'percentage': 100},
            'primary': 'Unknown'
        }

    typing_pct = int((typing_score / total) * 100)
    browsing_pct = int((browsing_score / total) * 100)
    design_pct = int((design_score / total) * 100)
    programming_pct = int((programming_score / total) * 100)
    communication_pct = int((communication_score / total) * 100)
    document_pct = int((document_score / total) * 100)
    gaming_pct = int((gaming_score / total) * 100)
    other_pct = 100 - typing_pct - browsing_pct - design_pct - programming_pct - communication_pct - document_pct - gaming_pct

    scores = {
        'Typing': typing_pct,
        'Browsing': browsing_pct,
        'Design': design_pct,
        'Programming': programming_pct,
        'Communication': communication_pct,
        'Documents': document_pct,
        'Gaming': gaming_pct,
        'Other': other_pct
    }
    primary = max(scores, key=scores.get)

    return {
        'typing': {'score': typing_score, 'percentage': typing_pct},
        'browsing': {'score': browsing_score, 'percentage': browsing_pct},
        'design': {'score': design_score, 'percentage': design_pct},
        'programming': {'score': programming_score, 'percentage': programming_pct},
        'communication': {'score': communication_score, 'percentage': communication_pct},
        'document': {'score': document_score, 'percentage': document_pct},
        'gaming': {'score': gaming_score, 'percentage': gaming_pct},
        'other': {'score': other_score, 'percentage': other_pct},
        'primary': primary
    }


def analyze_patterns(events: List[Dict]) -> Dict[str, Any]:
    """Analyze patterns in session events (same logic as former UI _analyze_patterns)."""
    key_events = [e for e in events if e.get("type") == "keypress"]
    click_events = [e for e in events if e.get("type") == "click"]

    key_texts = []
    for e in key_events:
        text = e.get("text", "")
        if "Key press:" in text:
            key = text.split("Key press:")[-1].strip().strip("'\"")
            key_texts.append(key)

    top_keys = [k for k, v in Counter(key_texts).most_common(5)]

    if len(events) >= 2:
        try:
            start_t = _extract_event_datetime(events[0])
            end_t = _extract_event_datetime(events[-1], reference=start_t)
            if not start_t or not end_t:
                raise ValueError("invalid event time")
            duration_minutes = (end_t - start_t).total_seconds() / 60
            if duration_minutes < 0:
                duration_minutes = 24 * 60 + duration_minutes
        except Exception:
            duration_minutes = 0
    else:
        duration_minutes = 0

    avg_events_per_minute = len(events) / duration_minutes if duration_minutes > 0 else 0
    click_ratio = len(click_events) / len(events) if events else 0

    return {
        "top_keys": top_keys if top_keys else ["N/A"],
        "avg_events_per_minute": avg_events_per_minute,
        "click_ratio": click_ratio,
        "duration_minutes": duration_minutes
    }


def _top_event_actions(events: List[Dict], limit: int = 5) -> List[str]:
    """Extract the most common event text snippets for one session."""
    counter: Counter = Counter()
    for event in events:
        text = " ".join(str(event.get("text", "")).split()).strip()
        if not text:
            continue
        counter[text] += 1
    out: List[str] = []
    for text, count in counter.most_common(limit):
        out.append(f"{text} ({count})")
    return out


def build_session_overlap_stats(
    session_id: int,
    events: List[Dict],
    start_time: Any,
    end_time: Any,
    window_start: Any,
    window_end: Any,
) -> Optional[Dict[str, Any]]:
    """Compute clipped overlap stats between one process session and another time window."""
    session_start_dt = _parse_datetime_value(start_time)
    session_end_dt = _parse_datetime_value(end_time, reference=session_start_dt)
    window_start_dt = _parse_datetime_value(window_start)
    window_end_dt = _parse_datetime_value(window_end, reference=window_start_dt)

    if session_start_dt is None or session_end_dt is None:
        return None
    if window_start_dt is None or window_end_dt is None:
        return None
    if session_end_dt < session_start_dt or window_end_dt < window_start_dt:
        return None

    overlap_start = max(session_start_dt, window_start_dt)
    overlap_end = min(session_end_dt, window_end_dt)
    if overlap_end <= overlap_start:
        return None

    overlap_seconds = max(0.0, (overlap_end - overlap_start).total_seconds())
    session_seconds = max(0.0, (session_end_dt - session_start_dt).total_seconds())
    window_seconds = max(0.0, (window_end_dt - window_start_dt).total_seconds())
    session_coverage_ratio = (overlap_seconds / session_seconds) if session_seconds > 0 else 0.0
    window_coverage_ratio = (overlap_seconds / window_seconds) if window_seconds > 0 else 0.0

    parsed_total = 0
    clipped_events: List[Dict[str, Any]] = []
    for event in events or []:
        event_dt = _extract_event_datetime(event, reference=session_start_dt)
        if event_dt is None:
            continue
        parsed_total += 1
        if overlap_start <= event_dt <= overlap_end:
            clipped_event = dict(event)
            clipped_event["time"] = event_dt.strftime("%Y-%m-%d %H:%M:%S")
            clipped_events.append(clipped_event)

    estimated = False
    overlap_events = clipped_events
    if not clipped_events and (events or []) and parsed_total == 0 and session_seconds > 0 and overlap_seconds > 0:
        estimated = True
        estimated_count = max(1, int(round(len(events) * session_coverage_ratio)))
        overlap_events = list(events[:estimated_count])

    overlap_event_count = len(overlap_events)
    overlap_keystrokes = sum(1 for e in overlap_events if e.get("type") == "keypress")
    overlap_clicks = sum(1 for e in overlap_events if e.get("type") == "click")

    categories = categorize_activities(overlap_events) if overlap_events else {"primary": "Unknown"}
    patterns = analyze_patterns(overlap_events) if overlap_events else {"top_keys": ["N/A"]}
    primary_activity = str(categories.get("primary", "Unknown") or "Unknown")
    common_actions = _top_event_actions(overlap_events, limit=3)
    top_keys = [
        str(item).strip()
        for item in (patterns.get("top_keys", []) or [])
        if str(item).strip() and str(item).strip() != "N/A"
    ]

    summary_parts = [f"process#{int(session_id)} {overlap_seconds:.1f}s overlap"]
    if overlap_event_count > 0:
        approx = "~" if estimated else ""
        summary_parts.append(
            f"{approx}{overlap_event_count} events ({overlap_keystrokes}K/{overlap_clicks}M)"
        )
    elif primary_activity != "Unknown":
        summary_parts.append("low input")
    if primary_activity != "Unknown":
        summary_parts.append(primary_activity)

    return {
        "session_id": int(session_id),
        "overlap_start": overlap_start.strftime("%Y-%m-%d %H:%M:%S"),
        "overlap_end": overlap_end.strftime("%Y-%m-%d %H:%M:%S"),
        "overlap_seconds": round(overlap_seconds, 2),
        "session_coverage_ratio": round(session_coverage_ratio, 3),
        "window_coverage_ratio": round(window_coverage_ratio, 3),
        "event_count": int(overlap_event_count),
        "keystrokes": int(overlap_keystrokes),
        "clicks": int(overlap_clicks),
        "primary_activity": primary_activity,
        "common_actions": common_actions,
        "top_keys": top_keys[:5],
        "estimated": bool(estimated),
        "summary": ", ".join(summary_parts),
    }


def build_session_memory_payload(
    session_id: int,
    events: List[Dict],
    start_time: str,
    end_time: str,
    event_count: int,
    keystrokes: int,
    clicks: int,
) -> Dict[str, Any]:
    """Build a structured summary + metadata for storing one process session in memory."""
    categories = categorize_activities(events)
    patterns = analyze_patterns(events)

    primary_activity = str(categories.get("primary", "Unknown") or "Unknown")
    duration_minutes = float(patterns.get("duration_minutes", 0.0) or 0.0)
    if duration_minutes <= 0:
        try:
            start_dt = datetime.datetime.fromisoformat(str(start_time).replace("Z", "+00:00").replace(" ", "T"))
            end_dt = datetime.datetime.fromisoformat(str(end_time).replace("Z", "+00:00").replace(" ", "T"))
            duration_minutes = max(0.0, (end_dt - start_dt).total_seconds() / 60.0)
        except Exception:
            duration_minutes = 0.0
    top_keys = [str(k).strip() for k in (patterns.get("top_keys", []) or []) if str(k).strip() and str(k).strip() != "N/A"]
    common_actions = _top_event_actions(events, limit=5)
    key_label = "keystroke" if int(keystrokes) == 1 else "keystrokes"
    click_label = "click" if int(clicks) == 1 else "clicks"

    activity_weights = []
    for key, value in categories.items():
        if key == "primary" or not isinstance(value, dict):
            continue
        pct = int(value.get("percentage", 0) or 0)
        if pct <= 0:
            continue
        activity_weights.append((str(key), pct))
    activity_weights.sort(key=lambda item: item[1], reverse=True)

    activity_tags = [primary_activity.lower()]
    for name, pct in activity_weights[:3]:
        if pct >= 12:
            normalized = name.lower()
            if normalized not in activity_tags:
                activity_tags.append(normalized)

    summary_parts = [
        f"Process session {session_id} from {start_time} to {end_time}.",
        f"Primary activity: {primary_activity}.",
        f"{event_count} events ({keystrokes} {key_label}, {clicks} {click_label}) over {duration_minutes:.1f} minutes.",
    ]
    if common_actions:
        summary_parts.append("Common actions: " + "; ".join(common_actions[:3]) + ".")
    if top_keys:
        summary_parts.append("Top keys: " + ", ".join(top_keys[:5]) + ".")

    memory_text = " ".join(summary_parts).strip()
    metadata = {
        "source": "process_mining",
        "type": "process_session",
        "category": "process_session",
        "session_id": int(session_id),
        "start_time": start_time,
        "end_time": end_time,
        "timestamp": end_time,
        "seen_at": end_time,
        "event_count": int(event_count),
        "keystrokes": int(keystrokes),
        "clicks": int(clicks),
        "duration_minutes": round(duration_minutes, 2),
        "primary_activity": primary_activity,
        "activity_summary": memory_text[:1000],
        "activity_tags": ",".join(activity_tags),
        "activity_tags_json": json.dumps(activity_tags, ensure_ascii=False),
        "common_actions": " | ".join(common_actions[:5]),
        "common_actions_json": json.dumps(common_actions[:5], ensure_ascii=False),
        "top_keys": ",".join(top_keys[:8]),
        "top_keys_json": json.dumps(top_keys[:8], ensure_ascii=False),
        "avg_events_per_minute": round(float(patterns.get("avg_events_per_minute", 0.0) or 0.0), 2),
        "click_ratio": round(float(patterns.get("click_ratio", 0.0) or 0.0), 3),
    }
    return {"memory_text": memory_text, "metadata": metadata}


def save_session(
    events: List[Dict],
    start_time: str,
    end_time: str,
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """Save session to DB (same schema as former UI). Creates table if not exists."""
    _ensure_db_dir(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            end_time TEXT,
            event_count INTEGER,
            keystrokes INTEGER,
            clicks INTEGER,
            events_json TEXT
        )
    ''')
    keystrokes = sum(1 for e in events if e.get("type") == "keypress")
    clicks = sum(1 for e in events if e.get("type") == "click")
    events_json = json.dumps(events)
    cursor.execute('''
        INSERT INTO sessions (start_time, end_time, event_count, keystrokes, clicks, events_json)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (start_time, end_time, len(events), keystrokes, clicks, events_json))
    session_id = int(cursor.lastrowid or 0)
    conn.commit()
    conn.close()
    return session_id


def load_sessions(
    limit: int = 20,
    db_path: str = DEFAULT_DB_PATH,
) -> List[Tuple[int, str, str, int, int, int]]:
    """Load session list: (id, start_time, end_time, event_count, keystrokes, clicks)."""
    _ensure_db_dir(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            end_time TEXT,
            event_count INTEGER,
            keystrokes INTEGER,
            clicks INTEGER,
            events_json TEXT
        )
    ''')
    cursor.execute('''
        SELECT id, start_time, end_time, event_count, keystrokes, clicks
        FROM sessions
        ORDER BY id DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_session_events(
    session_id: int,
    db_path: str = DEFAULT_DB_PATH,
) -> Optional[List[Dict]]:
    """Load events JSON for a session. Returns None if not found."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT events_json FROM sessions WHERE id=?', (session_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return json.loads(row[0])


def get_session_analysis(
    session_id: int,
    event_count: int,
    keystrokes: int,
    clicks: int,
    start_time: str,
    end_time: str,
    db_path: str = DEFAULT_DB_PATH,
) -> Optional[Dict[str, Any]]:
    """
    Load session events and return categories + patterns for UI.
    Returns None if session not found. Otherwise dict with 'categories', 'patterns'.
    """
    events = get_session_events(session_id, db_path=db_path)
    if events is None:
        return None
    categories = categorize_activities(events)
    patterns = analyze_patterns(events)
    return {
        "categories": categories,
        "patterns": patterns,
        "event_count": event_count,
        "keystrokes": keystrokes,
        "clicks": clicks,
        "start_time": start_time,
        "end_time": end_time,
    }


def delete_session(session_id: int, db_path: str = DEFAULT_DB_PATH) -> int:
    """Delete one session. Returns number of rows deleted."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sessions WHERE id=?', (session_id,))
    n = cursor.rowcount
    conn.commit()
    conn.close()
    return n


def delete_all_sessions(db_path: str = DEFAULT_DB_PATH) -> int:
    """Delete all sessions. Returns number of rows deleted."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM sessions')
    count = cursor.fetchone()[0]
    cursor.execute('DELETE FROM sessions')
    conn.commit()
    conn.close()
    return count
