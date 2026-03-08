"""Lightweight recording import service for packaged/native recording flows."""

from __future__ import annotations

import os
from typing import Dict, Optional, Any

from memscreen.storage import RecordingMetadataRepository


class RecordingImportService:
    def __init__(self, db_path: str):
        self.repo = RecordingMetadataRepository(db_path)

    def import_file(
        self,
        filename: str,
        *,
        duration_sec: Optional[float] = None,
        recording_mode: Optional[str] = None,
        window_title: Optional[str] = None,
        audio_source: Optional[str] = None,
    ) -> Dict[str, Any]:
        target = str(filename or '').strip()
        if not target:
            return {'ok': False, 'error': 'filename is required'}
        if not os.path.exists(target):
            return {'ok': False, 'error': f'file not found: {target}'}

        existing = self.repo.get_recording(target)
        if existing:
            return {'ok': True, 'filename': target, 'imported': False, 'existing': True}

        file_size = os.path.getsize(target)
        resolved_duration = float(duration_sec or 0.0)
        self.repo.insert_recording(
            filename=target,
            frame_count=0,
            fps=0.0,
            duration=resolved_duration,
            file_size=file_size,
            recording_mode=str(recording_mode or 'fullscreen'),
            region_bbox=None,
            window_title=window_title,
            content_tags=None,
            content_keywords=None,
            content_summary='Native macOS recording',
            analysis_status='pending',
            audio_file=None,
            audio_source=audio_source,
        )
        return {
            'ok': True,
            'filename': target,
            'imported': True,
            'duration': resolved_duration,
            'fps': 0.0,
            'frame_count': 0,
        }
