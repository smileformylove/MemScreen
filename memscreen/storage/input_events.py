"""SQLite repository for keyboard/mouse input events."""

from __future__ import annotations

import os
import sqlite3
from typing import Any, Dict, List, Optional


class InputEventRepository:
    """Encapsulates SQLite access for keyboard and mouse event logs."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def ensure_schema(self) -> None:
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS keyboard_mouse_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operate_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    operate_type TEXT NOT NULL,
                    action TEXT NOT NULL,
                    content TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_operate_time
                ON keyboard_mouse_logs(operate_time)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_operate_type
                ON keyboard_mouse_logs(operate_type)
                """
            )
            conn.commit()
        finally:
            conn.close()

    def insert_event(
        self,
        *,
        event_type: str,
        action: str,
        content: str = "",
        details: str = "",
        operate_time: Optional[str] = None,
    ) -> int:
        self.ensure_schema()

        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO keyboard_mouse_logs (operate_time, operate_type, action, content, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (operate_time, event_type, action, content, details),
            )
            conn.commit()
            return int(cursor.lastrowid or 0)
        finally:
            conn.close()

    def get_latest_event_id(self) -> int:
        self.ensure_schema()

        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("SELECT COALESCE(MAX(id), 0) FROM keyboard_mouse_logs").fetchone()
            return int((row or [0])[0] or 0)
        finally:
            conn.close()

    def list_recent_events(self, *, limit: int = 100, since_id: Optional[int] = None) -> List[Dict[str, Any]]:
        self.ensure_schema()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            if since_id is not None and since_id >= 0:
                rows = conn.execute(
                    """
                    SELECT id, operate_time, operate_type, action, content, details
                    FROM keyboard_mouse_logs
                    WHERE id > ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (int(since_id), int(limit)),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, operate_time, operate_type, action, content, details
                    FROM keyboard_mouse_logs
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (int(limit),),
                ).fetchall()
            return [self._normalize_row(row) for row in rows]
        finally:
            conn.close()

    def list_events(
        self,
        *,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        operate_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        self.ensure_schema()

        query = (
            "SELECT id, operate_time, operate_type, action, content, details "
            "FROM keyboard_mouse_logs WHERE 1=1"
        )
        params: List[Any] = []

        if start_time:
            query += " AND operate_time >= ?"
            params.append(str(start_time))
        if end_time:
            query += " AND operate_time <= ?"
            params.append(str(end_time))
        if operate_type:
            query += " AND operate_type = ?"
            params.append(str(operate_type))
        query += " ORDER BY operate_time ASC"

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(query, params).fetchall()
            return [self._normalize_row(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def _normalize_row(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": int(row["id"] or 0),
            "timestamp": row["operate_time"],
            "operate_type": str(row["operate_type"] or ""),
            "action": str(row["action"] or ""),
            "content": row["content"],
            "details": row["details"],
        }
