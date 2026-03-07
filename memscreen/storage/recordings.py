### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-03-07             ###
### license: MIT                 ###

"""SQLite repository for recording metadata."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class RecordingMetadataRepository:
    """Encapsulates SQLite access for recording metadata."""

    _recording_columns = (
        "filename",
        "timestamp",
        "frame_count",
        "fps",
        "duration",
        "file_size",
        "recording_mode",
        "region_bbox",
        "window_title",
        "content_tags",
        "content_keywords",
        "content_summary",
        "analysis_status",
        "audio_file",
        "audio_source",
    )

    _column_defaults = {
        "filename": "",
        "timestamp": "",
        "frame_count": 0,
        "fps": 0.0,
        "duration": 0.0,
        "file_size": 0,
        "recording_mode": "fullscreen",
        "region_bbox": None,
        "window_title": None,
        "content_tags": None,
        "content_keywords": None,
        "content_summary": None,
        "analysis_status": "pending",
        "audio_file": None,
        "audio_source": None,
    }

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
                CREATE TABLE IF NOT EXISTS recordings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    frame_count INTEGER,
                    fps REAL,
                    duration REAL,
                    file_size INTEGER,
                    recording_mode TEXT DEFAULT 'fullscreen',
                    region_bbox TEXT,
                    window_title TEXT,
                    content_tags TEXT,
                    content_keywords TEXT,
                    content_summary TEXT,
                    analysis_status TEXT,
                    audio_file TEXT,
                    audio_source TEXT
                )
                """
            )

            for statement in (
                "ALTER TABLE recordings ADD COLUMN recording_mode TEXT DEFAULT 'fullscreen'",
                "ALTER TABLE recordings ADD COLUMN region_bbox TEXT",
                "ALTER TABLE recordings ADD COLUMN window_title TEXT",
                "ALTER TABLE recordings ADD COLUMN content_tags TEXT",
                "ALTER TABLE recordings ADD COLUMN content_summary TEXT",
                "ALTER TABLE recordings ADD COLUMN content_keywords TEXT",
                "ALTER TABLE recordings ADD COLUMN analysis_status TEXT",
                "ALTER TABLE recordings ADD COLUMN audio_file TEXT",
                "ALTER TABLE recordings ADD COLUMN audio_source TEXT",
            ):
                try:
                    cursor.execute(statement)
                except sqlite3.OperationalError:
                    pass

            conn.commit()
        finally:
            conn.close()

    def ensure_saved_regions_schema(self) -> None:
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS saved_regions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    region_type TEXT NOT NULL,
                    bbox TEXT NOT NULL,
                    window_title TEXT,
                    window_app TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def list_recordings(
        self,
        *,
        limit: Optional[int] = None,
        order: str = "timestamp_desc",
        existing_only: bool = False,
        clean_missing: bool = False,
    ) -> List[Dict[str, Any]]:
        if not os.path.exists(self.db_path):
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            if not self._table_exists(conn, "recordings"):
                return []

            selected_columns = self._selected_columns(conn)
            order_clause = "timestamp DESC" if order != "rowid_desc" else "rowid DESC"
            query = f"SELECT {', '.join(selected_columns)} FROM recordings ORDER BY {order_clause}"
            params: List[Any] = []
            if limit is not None:
                query += " LIMIT ?"
                params.append(int(limit))

            rows = [self._normalize_row(row) for row in conn.execute(query, params).fetchall()]

            missing_files: List[str] = []
            if existing_only or clean_missing:
                filtered_rows: List[Dict[str, Any]] = []
                for row in rows:
                    filename = str(row.get("filename") or "")
                    exists = bool(filename) and os.path.exists(filename)
                    if exists:
                        filtered_rows.append(row)
                    elif clean_missing and filename:
                        missing_files.append(filename)
                if clean_missing and missing_files:
                    conn.executemany(
                        "DELETE FROM recordings WHERE filename = ?",
                        [(filename,) for filename in missing_files],
                    )
                    conn.commit()
                if existing_only:
                    rows = filtered_rows

            return rows
        finally:
            conn.close()

    def get_recording(self, filename: str) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.db_path):
            return None

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            if not self._table_exists(conn, "recordings"):
                return None

            selected_columns = self._selected_columns(conn)
            row = conn.execute(
                f"SELECT {', '.join(selected_columns)} FROM recordings WHERE filename = ? ORDER BY rowid DESC LIMIT 1",
                (filename,),
            ).fetchone()
            if not row:
                return None
            return self._normalize_row(row)
        finally:
            conn.close()

    def get_recording_metrics(self, filename: str) -> Tuple[int, float, str, float]:
        row = self.get_recording(filename)
        if not row:
            return 0, 0.0, "", 0.0
        return (
            int(row.get("frame_count") or 0),
            float(row.get("fps") or 0.0),
            str(row.get("timestamp") or ""),
            float(row.get("duration") or 0.0),
        )

    def insert_recording(
        self,
        *,
        filename: str,
        frame_count: int,
        fps: float,
        duration: float,
        file_size: int,
        recording_mode: str = "fullscreen",
        region_bbox: Optional[str] = None,
        window_title: Optional[str] = None,
        content_tags: Optional[str] = None,
        content_keywords: Optional[str] = None,
        content_summary: Optional[str] = None,
        analysis_status: str = "pending",
        audio_file: Optional[str] = None,
        audio_source: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> int:
        self.ensure_schema()
        insert_timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO recordings (
                    filename, timestamp, frame_count, fps, duration, file_size,
                    recording_mode, region_bbox, window_title, content_tags, content_keywords,
                    content_summary, analysis_status, audio_file, audio_source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    filename,
                    insert_timestamp,
                    frame_count,
                    fps,
                    duration,
                    file_size,
                    recording_mode,
                    region_bbox,
                    window_title,
                    content_tags,
                    content_keywords,
                    content_summary,
                    analysis_status,
                    audio_file,
                    audio_source,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid or 0)
        finally:
            conn.close()

    def update_content_metadata(
        self,
        *,
        filename: str,
        content_tags: List[str],
        content_keywords: Optional[List[str]] = None,
        content_summary: Optional[str] = None,
        analysis_status: str = "ready",
    ) -> int:
        if not os.path.exists(self.db_path):
            return 0

        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE recordings
                SET content_tags = ?, content_keywords = ?, content_summary = ?, analysis_status = ?
                WHERE filename = ?
                """,
                (
                    json.dumps(content_tags, ensure_ascii=False),
                    json.dumps(content_keywords or [], ensure_ascii=False),
                    content_summary[:500] if content_summary else None,
                    analysis_status,
                    filename,
                ),
            )
            conn.commit()
            return int(cursor.rowcount or 0)
        finally:
            conn.close()

    def delete_recording(self, filename: str) -> int:
        if not os.path.exists(self.db_path):
            return 0

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recordings WHERE filename = ?", (filename,))
            conn.commit()
            return int(cursor.rowcount or 0)
        finally:
            conn.close()

    def _selected_columns(self, conn: sqlite3.Connection) -> List[str]:
        available = self._table_columns(conn, "recordings")
        return [column for column in self._recording_columns if column in available]

    def _normalize_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        keys = set(row.keys())
        data: Dict[str, Any] = {}
        for column in self._recording_columns:
            if column in keys:
                data[column] = row[column]
            else:
                data[column] = self._column_defaults[column]
        return data

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
            (table_name,),
        ).fetchone()
        return row is not None

    @staticmethod
    def _table_columns(conn: sqlite3.Connection, table_name: str) -> set:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row[1] for row in rows}
