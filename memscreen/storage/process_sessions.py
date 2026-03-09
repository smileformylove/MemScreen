"""SQLite repository for process session persistence."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional


class ProcessSessionRepository:
    """Encapsulates SQLite access for process sessions."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def ensure_schema(self) -> None:
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT,
                    end_time TEXT,
                    event_count INTEGER,
                    keystrokes INTEGER,
                    clicks INTEGER,
                    events_json TEXT
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def insert_session(
        self,
        *,
        events: List[Dict[str, Any]],
        start_time: str,
        end_time: str,
    ) -> int:
        self.ensure_schema()
        keystrokes = sum(1 for event in events if event.get("type") == "keypress")
        clicks = sum(1 for event in events if event.get("type") == "click")

        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sessions (start_time, end_time, event_count, keystrokes, clicks, events_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    start_time,
                    end_time,
                    len(events),
                    keystrokes,
                    clicks,
                    json.dumps(events, ensure_ascii=False),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid or 0)
        finally:
            conn.close()

    def list_sessions(
        self,
        *,
        limit: int = 20,
        include_events: bool = False,
    ) -> List[Dict[str, Any]]:
        self.ensure_schema()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            columns = ["id", "start_time", "end_time", "event_count", "keystrokes", "clicks"]
            if include_events:
                columns.append("events_json")
            rows = conn.execute(
                f"SELECT {', '.join(columns)} FROM sessions ORDER BY id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
            return [self._normalize_row(row, include_events=include_events) for row in rows]
        finally:
            conn.close()

    def get_session(
        self,
        session_id: int,
        *,
        include_events: bool = False,
    ) -> Optional[Dict[str, Any]]:
        self.ensure_schema()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            columns = ["id", "start_time", "end_time", "event_count", "keystrokes", "clicks"]
            if include_events:
                columns.append("events_json")
            row = conn.execute(
                f"SELECT {', '.join(columns)} FROM sessions WHERE id = ?",
                (int(session_id),),
            ).fetchone()
            if row is None:
                return None
            return self._normalize_row(row, include_events=include_events)
        finally:
            conn.close()

    def delete_session(self, session_id: int) -> int:
        self.ensure_schema()

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE id = ?", (int(session_id),))
            conn.commit()
            return int(cursor.rowcount or 0)
        finally:
            conn.close()

    def delete_all_sessions(self) -> int:
        self.ensure_schema()

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            count_row = cursor.execute("SELECT COUNT(*) FROM sessions").fetchone()
            cursor.execute("DELETE FROM sessions")
            conn.commit()
            return int((count_row or [0])[0] or 0)
        finally:
            conn.close()

    def _normalize_row(self, row: sqlite3.Row, *, include_events: bool) -> Dict[str, Any]:
        data = {
            "session_id": int(row["id"] or 0),
            "start_time": str(row["start_time"] or ""),
            "end_time": str(row["end_time"] or ""),
            "event_count": int(row["event_count"] or 0),
            "keystrokes": int(row["keystrokes"] or 0),
            "clicks": int(row["clicks"] or 0),
        }
        if include_events:
            data["events"] = self._decode_events(row["events_json"])
        return data

    @staticmethod
    def _decode_events(events_json: Any) -> List[Dict[str, Any]]:
        if not events_json:
            return []
        try:
            parsed = json.loads(str(events_json))
        except Exception:
            return []
        if not isinstance(parsed, list):
            return []
        return [event for event in parsed if isinstance(event, dict)]
