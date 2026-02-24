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
            def _parse_event_time(v: str) -> Optional[datetime.datetime]:
                if not isinstance(v, str):
                    return None
                raw = v.strip()
                if not raw:
                    return None
                # Full datetime first.
                try:
                    return datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
                except Exception:
                    pass
                for fmt in ("%Y-%m-%d %H:%M:%S", "%H:%M:%S"):
                    try:
                        return datetime.datetime.strptime(raw, fmt)
                    except Exception:
                        continue
                return None

            start_t = _parse_event_time(events[0].get("time", ""))
            end_t = _parse_event_time(events[-1].get("time", ""))
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


def save_session(
    events: List[Dict],
    start_time: str,
    end_time: str,
    db_path: str = DEFAULT_DB_PATH,
) -> None:
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
    conn.commit()
    conn.close()


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
