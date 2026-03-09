"""Fallback data access helpers for chat when vector memory is unavailable."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from memscreen.storage import ProcessSessionRepository, RecordingMetadataRepository


class ChatFallbackDataService:
    """Loads recording and process-session fallback data for chat flows."""

    def __init__(
        self,
        *,
        recording_db_path: Optional[str] = None,
        process_db_path: Optional[str] = None,
    ):
        self._recording_db_path = recording_db_path
        self._process_db_path = process_db_path

    def get_recording_db_path(self) -> str:
        if self._recording_db_path:
            return str(self._recording_db_path)
        try:
            from memscreen.config import get_config

            return str(get_config().db_path)
        except Exception:
            return "./db/memories.db"

    def get_process_db_path(self) -> str:
        if self._process_db_path:
            return str(self._process_db_path)
        try:
            from memscreen.config import get_config

            return str(get_config().db_dir / "process_mining.db")
        except Exception:
            return "./db/process_mining.db"

    def load_recent_recordings(self, limit: int = 5) -> List[Dict[str, Any]]:
        db_path = self.get_recording_db_path()
        try:
            rows = RecordingMetadataRepository(db_path).list_recordings(
                limit=limit,
                order="rowid_desc",
            )
            return [self._normalize_recording_row(row) for row in rows]
        except Exception:
            return []

    def load_recent_process_sessions(
        self,
        *,
        limit: int = 20,
        include_events: bool = False,
    ) -> List[Dict[str, Any]]:
        db_path = self.get_process_db_path()
        if not os.path.exists(db_path):
            return []
        try:
            return ProcessSessionRepository(db_path).list_sessions(
                limit=limit,
                include_events=include_events,
            )
        except Exception:
            return []

    @staticmethod
    def _normalize_recording_row(row: Dict[str, Any]) -> Dict[str, Any]:
        filename = str(row.get("filename") or "")
        return {
            "filename": filename,
            "basename": os.path.basename(filename),
            "timestamp": str(row.get("timestamp") or ""),
            "duration": float(row.get("duration") or 0.0),
            "frame_count": int(row.get("frame_count") or 0),
            "recording_mode": str(row.get("recording_mode") or "fullscreen"),
            "window_title": str(row.get("window_title") or ""),
            "content_tags": row.get("content_tags"),
            "content_summary": str(row.get("content_summary") or ""),
            "content_keywords": row.get("content_keywords"),
        }
