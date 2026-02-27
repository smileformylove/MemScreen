### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""Presenter for Screen Recording functionality (MVP Pattern)"""

import os
import time
import threading
import sqlite3
import json
import hashlib
import re
import subprocess
import sys
import shutil
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from .base_presenter import BasePresenter
from memscreen.audio import AudioRecorder, AudioSource
from memscreen.cv2_loader import get_cv2
from memscreen.services.model_capability import RecordingModelCapabilityService

SUPPORTED_VIDEO_FORMATS = ("mp4", "mov", "mkv", "avi")
SUPPORTED_AUDIO_FORMATS = ("wav", "m4a", "mp3", "aac")


class RecordingPresenter(BasePresenter):
    """
    Presenter for Screen Recording functionality.

    Responsibilities:
    - Manage recording state and logic
    - Coordinate screen capture
    - Handle video encoding and saving
    - Add recordings to memory system
    - Provide data to view for display

    View (RecordingTab) responsibilities:
    - Display UI elements
    - Show preview frames
    - Update status labels
    - Handle button clicks
    """

    def __init__(
        self,
        view=None,
        memory_system=None,
        db_path=None,
        output_dir=None,
        audio_dir=None,
        model_capability: Optional[RecordingModelCapabilityService] = None,
    ):
        """
        Initialize recording presenter.

        Args:
            view: RecordingTab view instance
            memory_system: Memory system for storing recordings
            db_path: Path to SQLite database
            output_dir: Directory for video output
            audio_dir: Directory for audio output
        """
        super().__init__(view, memory_system)

        # Use centralized config for any missing paths
        from memscreen.config import get_config
        config = get_config()

        # Set db_path
        if db_path is None:
            db_path = str(config.db_path)

        # Set output_dir
        if output_dir is None:
            output_dir = str(config.videos_dir)

        # Set audio_dir
        if audio_dir is None:
            audio_dir = str(config.db_dir / "audio")

        self.db_path = db_path
        self.memory_system = memory_system

        # Recording state
        self.is_recording = False
        self.recording_thread = None
        self._save_thread = None  # Thread for saving recording to database
        self._memory_index_ready_event = threading.Event()
        self.recording_frames = []
        self.recording_start_time = None

        # Recording settings (with defaults)
        self.duration = 60  # seconds per segment
        self.interval = 2.0  # seconds between screenshots
        self.output_dir = output_dir
        self.video_format = "mp4"
        self.audio_output_format = "wav"
        self.audio_denoise = True

        # Audio recording
        self.audio_recorder = AudioRecorder(output_dir=audio_dir)
        self.audio_recorder.set_output_format(self.audio_output_format)
        self.audio_recorder.set_noise_reduction(self.audio_denoise)
        self.audio_source = AudioSource.NONE  # none, mixed, microphone, system_audio
        self._active_audio_source = AudioSource.NONE

        # Statistics
        self.frame_count = 0
        self.current_file = None

        # Recording mode support
        self.recording_mode = 'fullscreen'  # fullscreen, region
        self.region_bbox = None  # (left, top, right, bottom) or None
        self.screen_index = None  # Index of screen to record (None = all screens/primary)
        self.screen_display_id: Optional[int] = None  # Stable OS display identifier when available
        self.window_title = None  # Optional window/app label for region-window mode
        self._window_follow_enabled = False
        self._window_follow_owner: Optional[str] = None
        self._window_follow_name: Optional[str] = None
        self._window_follow_window_id: Optional[int] = None
        self._window_follow_import_failed = False
        self.content_tags: List[str] = []
        self.content_summary: Optional[str] = None

        # Services (lazy loaded)
        self.region_config = None

        self._is_initialized = False
        self.last_start_error: Optional[str] = None
        self.model_capability = model_capability or RecordingModelCapabilityService(
            ollama_base_url=config.ollama_base_url,
            vision_model=config.ollama_vision_model,
        )

        # Check if cv2 is available
        self.cv2_available = self._check_cv2_available()

    def _check_cv2_available(self) -> bool:
        """Check if cv2 is available for video processing"""
        # Use the safe cv2 loader that handles PyInstaller recursion
        cv2 = get_cv2()
        if cv2 is not None:
            print(f"[RecordingPresenter] ✓ cv2 is available (version: {cv2.__version__})")
            return True
        else:
            print("[RecordingPresenter] ✗ cv2 not available")
            print("[RecordingPresenter] Recording and preview will be disabled")
            return False

    def initialize(self):
        """Initialize presenter and create output directory"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)

            # Create audio directory if it doesn't exist
            audio_dir = getattr(self.audio_recorder, 'output_dir', './db/audio')
            os.makedirs(audio_dir, exist_ok=True)
            print(f"[RecordingPresenter] Created output directories: {self.output_dir}, {audio_dir}")

            # Initialize database
            self._init_database()

            self._is_initialized = True
            print(f"[RecordingPresenter] Initialized successfully (cv2_available={self.cv2_available})")
        except Exception as e:
            self.handle_error(e, "Failed to initialize RecordingPresenter")
            raise

    def cleanup(self):
        """Clean up resources"""
        # Stop recording if active
        if self.is_recording:
            self.stop_recording()

        # Wait for recording thread to finish
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5)

        # Clean up audio recorder
        if self.audio_recorder:
            self.audio_recorder.cleanup()

        self._is_initialized = False

    def _init_database(self):
        """Initialize SQLite database for recording metadata"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create recordings table with new columns for region/window support
            cursor.execute('''
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
                    content_summary TEXT,
                    audio_file TEXT,
                    audio_source TEXT
                )
            ''')

            # Create saved_regions table for storing custom regions and windows
            cursor.execute('''
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
            ''')

            # Try to add new columns to existing recordings table (for backwards compatibility)
            try:
                cursor.execute('ALTER TABLE recordings ADD COLUMN recording_mode TEXT DEFAULT \'fullscreen\'')
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute('ALTER TABLE recordings ADD COLUMN region_bbox TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute('ALTER TABLE recordings ADD COLUMN window_title TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute('ALTER TABLE recordings ADD COLUMN content_tags TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute('ALTER TABLE recordings ADD COLUMN content_summary TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute('ALTER TABLE recordings ADD COLUMN audio_file TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute('ALTER TABLE recordings ADD COLUMN audio_source TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists

            conn.commit()
            conn.close()
        except Exception as e:
            self.handle_error(e, "Failed to initialize database")
            raise

    # ==================== Public API for View ====================

    def get_recording_status(self) -> Dict[str, Any]:
        """
        Get current recording status.

        Returns:
            Dictionary with recording status information
        """
        return {
            "is_recording": self.is_recording,
            "duration": self.duration,
            "interval": self.interval,
            "output_dir": self.output_dir,
            "frame_count": self.frame_count,
            "elapsed_time": time.time() - self.recording_start_time if self.recording_start_time else 0
        }

    def set_audio_source(self, source: AudioSource):
        """
        Set the audio source for recording.

        Args:
            source: AudioSource enum (MIXED, MICROPHONE, SYSTEM_AUDIO, NONE)
        """
        self.audio_source = source
        self.audio_recorder.set_audio_source(source)
        print(f"[RecordingPresenter] Audio source set to: {source.value}")

    def set_video_format(self, video_format: str):
        """
        Set output video container format.

        Args:
            video_format: mp4, mov, mkv, avi
        """
        normalized = str(video_format or "").strip().lower()
        if normalized not in SUPPORTED_VIDEO_FORMATS:
            raise ValueError(
                f"Unsupported video format: {video_format}. "
                f"Supported: {', '.join(SUPPORTED_VIDEO_FORMATS)}"
            )
        self.video_format = normalized
        print(f"[RecordingPresenter] Video format set to: {self.video_format}")

    def set_audio_output_format(self, audio_format: str):
        """
        Set output audio format for recorded audio tracks.

        Args:
            audio_format: wav, m4a, mp3, aac
        """
        normalized = str(audio_format or "").strip().lower()
        if normalized not in SUPPORTED_AUDIO_FORMATS:
            raise ValueError(
                f"Unsupported audio format: {audio_format}. "
                f"Supported: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
            )
        self.audio_output_format = normalized
        self.audio_recorder.set_output_format(normalized)
        print(f"[RecordingPresenter] Audio format set to: {self.audio_output_format}")

    def set_audio_denoise(self, enabled: bool):
        """
        Enable/disable basic post-recording audio denoise.
        """
        self.audio_denoise = bool(enabled)
        self.audio_recorder.set_noise_reduction(self.audio_denoise)
        print(f"[RecordingPresenter] Audio denoise set to: {self.audio_denoise}")

    def get_audio_sources(self) -> list:
        """
        Get list of available audio sources.

        Returns:
            List of available AudioSource values
        """
        return [AudioSource.NONE, AudioSource.MIXED, AudioSource.MICROPHONE, AudioSource.SYSTEM_AUDIO]

    def _check_screen_capture_ready(self) -> Tuple[bool, Optional[str]]:
        """
        Validate screen capture permission/readiness before recording starts.
        Returns:
            (is_ready, error_message)
        """
        if sys.platform == "darwin":
            # On macOS, this API reliably reports screen recording permission.
            try:
                from Quartz import CGPreflightScreenCaptureAccess  # type: ignore

                if not bool(CGPreflightScreenCaptureAccess()):
                    return (
                        False,
                        "Screen recording permission is required. "
                        "Grant access in System Settings > Privacy & Security > Screen Recording.",
                    )
            except Exception as e:
                # Non-fatal: fall back to runtime grab probe below.
                print(f"[RecordingPresenter] Screen permission preflight API unavailable: {e}")

        try:
            from PIL import ImageGrab
            test_img = ImageGrab.grab(bbox=(0, 0, 4, 4))
            if test_img is None:
                return False, "Failed to capture screen frame during pre-flight check."
        except Exception as e:
            error_msg = str(e).lower()
            if "permission" in error_msg or "denied" in error_msg or "screen" in error_msg:
                return (
                    False,
                    "Screen recording permission is required. "
                    "Grant access in System Settings > Privacy & Security > Screen Recording.",
                )
            return False, f"Failed to verify screen capture readiness: {e}"

        return True, None

    def start_recording(self, duration: int = 60, interval: float = 2.0) -> bool:
        """
        Start screen recording.

        Args:
            duration: Duration in seconds per video segment
            interval: Interval in seconds between frame captures

        Returns:
            True if recording started successfully
        """
        self.last_start_error = None
        if self.is_recording:
            self.last_start_error = "Recording is already in progress"
            self.show_error(self.last_start_error)
            return False

        # Check if cv2 is available
        if not self.cv2_available:
            error_msg = "Video recording requires opencv-python (cv2), but it's not available. "
            error_msg += "This is likely due to missing SDL2 dependencies. "
            error_msg += "Please check the console for details."
            self.last_start_error = error_msg
            self.show_error(error_msg)
            print("[RecordingPresenter] ERROR: Cannot start recording - cv2 not available")
            return False

        # Reset permission denied flag - user is explicitly trying to record
        self._preview_permission_denied = False

        print("[RecordingPresenter] Performing pre-flight permission check...")
        capture_ready, capture_error = self._check_screen_capture_ready()
        if not capture_ready:
            print(f"[RecordingPresenter] ✗ Pre-flight permission check failed: {capture_error}")
            self._preview_permission_denied = True
            self.last_start_error = capture_error or (
                "Screen recording permission is required. Please grant permission in "
                "System Settings > Privacy & Security > Screen Recording, then restart the app."
            )
            self.show_error(self.last_start_error)
            return False
        print("[RecordingPresenter] ✓ Pre-flight permission check passed")

        try:
            self.duration = duration
            self.interval = interval
            self.is_recording = True
            self.recording_frames = []
            self.recording_start_time = time.time()
            self.frame_count = 0
            print(
                "[RecordingPresenter] Recording start requested "
                f"(mode={self.recording_mode}, duration={self.duration}, interval={self.interval})"
            )

            # Start audio recording if audio source is set
            if self.audio_source != AudioSource.NONE:
                audio_started = self.audio_recorder.start_recording(self.audio_source)
                if audio_started:
                    effective_source = self.audio_recorder.get_effective_source()
                    self._active_audio_source = effective_source if effective_source != AudioSource.NONE else self.audio_source
                    if self.audio_source == AudioSource.MIXED and self._active_audio_source != AudioSource.MIXED:
                        self.show_info("System audio is unavailable. Recording microphone input only.")
                        print("[RecordingPresenter] Mixed audio requested, but system audio unavailable.")
                else:
                    self._active_audio_source = AudioSource.NONE
                    audio_error = self.audio_recorder.get_last_error() or (
                        f"Audio capture failed to start for source={self.audio_source.value}."
                    )
                    self.show_error(audio_error)
                    print(
                        f"[RecordingPresenter] {audio_error} "
                        "Recording will continue without audio."
                    )
            else:
                self._active_audio_source = AudioSource.NONE

            # Start recording in background thread
            self.recording_thread = threading.Thread(
                target=self._record_screen,
                daemon=True
            )
            self.recording_thread.start()

            # Notify view
            if self.view:
                self.view.on_recording_started()

            return True

        except Exception as e:
            self.is_recording = False
            self.last_start_error = str(e)
            self.handle_error(e, "Failed to start recording")
            return False

    def stop_recording(self) -> bool:
        """
        Stop screen recording.

        Returns:
            True if recording stopped successfully
        """
        if not self.is_recording:
            return False

        try:
            self.is_recording = False

            # Stop audio recording
            audio_file = None
            if self._active_audio_source != AudioSource.NONE:
                audio_file = self.audio_recorder.stop_recording()
                effective_source = self.audio_recorder.get_effective_source()
                if effective_source != AudioSource.NONE:
                    self._active_audio_source = effective_source

            # Wait for recording thread to finish
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=10)

            # Save the recording with audio
            if self.recording_frames:
                self._memory_index_ready_event.clear()

                # Save in background thread (non-daemon to ensure database save completes)
                save_thread = threading.Thread(
                    target=self._save_recording,
                    args=(self.recording_frames, audio_file),
                    daemon=False  # Changed: must complete database save
                )
                save_thread.start()
                print(f"[RecordingPresenter] 📀 Save thread started (non-daemon, will wait for completion)")

                # Store thread reference for waiting on app exit
                self._save_thread = save_thread

                # Ensure memory has at least placeholder timeline before returning.
                self._memory_index_ready_event.wait(timeout=8)
            else:
                self._memory_index_ready_event.set()

            # Notify view
            if self.view:
                self.view.on_recording_stopped()

            return True

        except Exception as e:
            self.handle_error(e, "Failed to stop recording")
            return False

    def update_settings(self, duration: int, interval: float, output_dir: str):
        """
        Update recording settings.

        Args:
            duration: Duration in seconds per video segment
            interval: Interval in seconds between frame captures
            output_dir: Output directory for recordings
        """
        self.duration = duration
        self.interval = interval
        self.output_dir = output_dir

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def set_recording_mode(self, mode: str, **kwargs) -> bool:
        """
        Set recording mode (fullscreen, fullscreen-single, or region).

        Args:
            mode: 'fullscreen', 'fullscreen-single', 'region', or legacy 'window'
            **kwargs:
                - bbox: region bbox tuple (for 'region' mode)
                - screen_index: screen index (for 'fullscreen-single' or screen-local 'region' mode)
                - screen_display_id: stable screen id (preferred when available)

        Returns:
            True if mode set successfully
        """
        try:
            self.last_start_error = None
            mode_normalized = (mode or "").strip().lower()
            # Backward compatibility for old clients that send "window".
            if mode_normalized == "window":
                mode_normalized = "region"
            self.recording_mode = mode_normalized
            window_title = kwargs.get('window_title')
            self.window_title = window_title.strip() if isinstance(window_title, str) and window_title.strip() else None
            requested_display_id = kwargs.get('screen_display_id')

            if mode_normalized == 'fullscreen':
                # Capture all screens combined
                self.region_bbox = None
                self.screen_index = None
                self.screen_display_id = None
                self.window_title = None
                self._reset_window_follow()
                print("[RecordingPresenter] Mode set to: Full Screen (all screens)")

            elif mode_normalized == 'fullscreen-single':
                # Capture a specific screen
                screen_index = kwargs.get('screen_index')
                resolved_screen = None
                if requested_display_id is not None:
                    from memscreen.utils import get_screen_by_display_id

                    resolved_screen = get_screen_by_display_id(int(requested_display_id))
                    if not resolved_screen:
                        raise ValueError(
                            f"Invalid screen_display_id for fullscreen-single mode: {requested_display_id}"
                        )
                    self.screen_index = int(resolved_screen.index)
                    self.screen_display_id = (
                        int(resolved_screen.display_id)
                        if resolved_screen.display_id is not None
                        else int(requested_display_id)
                    )
                    self.region_bbox = None
                    self.window_title = None
                    self._reset_window_follow()
                    print(
                        f"[RecordingPresenter] Mode set to: Full Screen {self.screen_index + 1} "
                        f"(display_id={self.screen_display_id})"
                    )
                elif screen_index is not None:
                    from memscreen.utils import get_screen_by_index

                    self.screen_index = int(screen_index)
                    resolved_screen = get_screen_by_index(self.screen_index)
                    self.screen_display_id = (
                        int(resolved_screen.display_id)
                        if resolved_screen and resolved_screen.display_id is not None
                        else None
                    )
                    self.region_bbox = None
                    self.window_title = None
                    self._reset_window_follow()
                    print(
                        f"[RecordingPresenter] Mode set to: Full Screen {self.screen_index + 1} "
                        f"(display_id={self.screen_display_id})"
                    )
                else:
                    raise ValueError("screen_index or screen_display_id is required for fullscreen-single mode")

            elif mode_normalized == 'region':
                bbox = kwargs.get('bbox')
                if bbox and len(bbox) == 4:
                    # Ensure bbox elements are integers for PIL ImageGrab.
                    local_bbox = tuple(int(x) for x in bbox)
                    screen_index = kwargs.get('screen_index')
                    screen_info = None
                    if requested_display_id is not None:
                        from memscreen.utils import get_screen_by_display_id

                        screen_info = get_screen_by_display_id(int(requested_display_id))
                        if not screen_info:
                            raise ValueError(
                                f"Invalid screen_display_id for region mode: {requested_display_id}"
                            )
                        resolved_screen_index = int(screen_info.index)
                    elif screen_index is not None:
                        from memscreen.utils import get_screen_by_index
                        resolved_screen_index = int(screen_index)
                        screen_info = get_screen_by_index(resolved_screen_index)
                        if not screen_info:
                            raise ValueError(f"Invalid screen_index for region mode: {resolved_screen_index}")

                    if screen_info is not None:
                        # Region bbox from native selector is screen-local (top-left origin).
                        # Convert to global bbox in PIL coordinate space.
                        x1 = screen_info.x + local_bbox[0]
                        y1 = screen_info.y + local_bbox[1]
                        x2 = screen_info.x + local_bbox[2]
                        y2 = screen_info.y + local_bbox[3]

                        # Clamp to the selected screen bounds.
                        screen_x1 = screen_info.x
                        screen_y1 = screen_info.y
                        screen_x2 = screen_info.x + screen_info.width
                        screen_y2 = screen_info.y + screen_info.height

                        x1 = max(screen_x1, min(screen_x2, x1))
                        y1 = max(screen_y1, min(screen_y2, y1))
                        x2 = max(screen_x1, min(screen_x2, x2))
                        y2 = max(screen_y1, min(screen_y2, y2))

                        if x2 <= x1 or y2 <= y1:
                            raise ValueError("Invalid region after screen mapping")

                        self.region_bbox = (x1, y1, x2, y2)
                        self.screen_index = resolved_screen_index
                        self.screen_display_id = (
                            int(screen_info.display_id)
                            if screen_info.display_id is not None
                            else (
                                int(requested_display_id)
                                if requested_display_id is not None
                                else None
                            )
                        )
                    else:
                        # Backward-compatible path: treat bbox as global coordinates.
                        self.region_bbox = local_bbox
                        self.screen_index = None
                        self.screen_display_id = None
                    if self.window_title:
                        self._enable_window_follow(self.window_title)
                        print(f"[RecordingPresenter] Mode set to: Window Region {self.region_bbox} ({self.window_title})")
                    else:
                        self._reset_window_follow()
                        print(f"[RecordingPresenter] Mode set to: Custom Region {self.region_bbox}")
                else:
                    raise ValueError("Invalid bbox for region mode")

            else:
                raise ValueError(f"Invalid recording mode: {mode_normalized}")

            return True

        except Exception as e:
            self.last_start_error = str(e)
            self.handle_error(e, f"Failed to set recording mode to {mode}")
            return False

    def _reset_window_follow(self) -> None:
        """Disable dynamic window-follow tracking."""
        self._window_follow_enabled = False
        self._window_follow_owner = None
        self._window_follow_name = None
        self._window_follow_window_id = None

    def _enable_window_follow(self, window_title: str) -> None:
        """Enable dynamic window-follow tracking for app-window recording mode."""
        text = (window_title or "").strip()
        if not text:
            self._reset_window_follow()
            return
        # Expected format: "Window: <owner> · <name>" (or owner only).
        text = re.sub(r"^window\s*:\s*", "", text, flags=re.IGNORECASE).strip()
        owner = text
        name = None
        if "·" in text:
            parts = [p.strip() for p in text.split("·", 1)]
            owner = parts[0] if parts else text
            name = parts[1] if len(parts) > 1 and parts[1] else None
        self._window_follow_enabled = bool(owner)
        self._window_follow_owner = owner or None
        self._window_follow_name = name

    def _refresh_window_follow_bbox_if_needed(self) -> None:
        """
        Refresh region bbox from live window bounds so recording follows move/resize.
        Only applies to region mode with selected app window metadata.
        """
        if not self._window_follow_enabled or self.recording_mode != "region":
            return
        if self._window_follow_import_failed:
            return
        try:
            from Quartz import (  # type: ignore
                CGWindowListCopyWindowInfo,
                kCGNullWindowID,
                kCGWindowLayer,
                kCGWindowBounds,
                kCGWindowOwnerName,
                kCGWindowName,
                kCGWindowNumber,
            )
        except Exception:
            self._window_follow_import_failed = True
            print("[RecordingPresenter] Window-follow disabled: Quartz is unavailable")
            return

        try:
            info_list = CGWindowListCopyWindowInfo(
                1 | 16,  # .optionOnScreenOnly | .excludeDesktopElements
                kCGNullWindowID,
            )
            if not info_list:
                return

            owner_key = (self._window_follow_owner or "").lower().strip()
            name_key = (self._window_follow_name or "").lower().strip()
            best_bbox = None
            best_window_id: Optional[int] = None
            fallback_bbox = None
            fallback_window_id: Optional[int] = None
            best_overlap = -1.0

            for info in info_list:
                layer = int(info.get(kCGWindowLayer, 0))
                if layer != 0:
                    continue

                owner = str(info.get(kCGWindowOwnerName, "") or "").strip()
                if not owner:
                    continue
                owner_l = owner.lower()
                if owner_key and owner_key not in owner_l:
                    continue

                win_name = str(info.get(kCGWindowName, "") or "").strip()
                win_name_l = win_name.lower()
                if name_key and name_key not in win_name_l and win_name_l not in name_key:
                    continue

                bounds = info.get(kCGWindowBounds) or {}
                x = int(bounds.get("X", 0))
                y = int(bounds.get("Y", 0))
                w = int(bounds.get("Width", 0))
                h = int(bounds.get("Height", 0))
                if w < 50 or h < 40:
                    continue

                candidate_bbox = (x, y, x + w, y + h)
                raw_window_id = (
                    info.get(kCGWindowNumber)
                    or info.get("kCGWindowNumber")
                    or info.get("WindowNumber")
                    or 0
                )
                candidate_window_id = int(raw_window_id or 0)

                # Primary match: owner/name textual match.
                if owner_key and owner_key in owner_l:
                    if not name_key or name_key in win_name_l or win_name_l in name_key:
                        best_bbox = candidate_bbox
                        best_window_id = candidate_window_id if candidate_window_id > 0 else None
                        break  # list order is top-most first

                # Fallback candidate: maximize overlap with current region.
                if self.region_bbox:
                    overlap = self._bbox_overlap_ratio(self.region_bbox, candidate_bbox)
                    if overlap > best_overlap:
                        best_overlap = overlap
                        fallback_bbox = candidate_bbox
                        fallback_window_id = candidate_window_id if candidate_window_id > 0 else None
                elif fallback_bbox is None:
                    fallback_bbox = candidate_bbox
                    fallback_window_id = candidate_window_id if candidate_window_id > 0 else None

            final_bbox = best_bbox or fallback_bbox
            final_window_id = best_window_id if best_bbox else fallback_window_id
            if final_bbox and final_bbox != self.region_bbox:
                self.region_bbox = final_bbox
                print(f"[RecordingPresenter] Window-follow bbox updated: {self.region_bbox}")
            if final_window_id and final_window_id != self._window_follow_window_id:
                self._window_follow_window_id = final_window_id
                print(f"[RecordingPresenter] Window-follow target id updated: {self._window_follow_window_id}")
        except Exception as e:
            print(f"[RecordingPresenter] Window-follow refresh failed: {e}")

    def _capture_window_frame_by_id(self, window_id: Optional[int]):
        """
        Capture one window directly by CGWindow ID.
        This avoids occlusion by other top windows.
        Returns BGR ndarray or None on failure.
        """
        if not window_id:
            return None
        try:
            cv2 = get_cv2()
            if cv2 is None:
                return None

            from Quartz import (  # type: ignore
                CGWindowListCreateImage,
                CGRectNull,
                kCGWindowListOptionIncludingWindow,
                kCGWindowImageBoundsIgnoreFraming,
                CGImageGetWidth,
                CGImageGetHeight,
                CGImageGetBytesPerRow,
                CGImageGetDataProvider,
                CGDataProviderCopyData,
            )

            cg_img = CGWindowListCreateImage(
                CGRectNull,
                kCGWindowListOptionIncludingWindow,
                int(window_id),
                kCGWindowImageBoundsIgnoreFraming,
            )
            if cg_img is None:
                return None

            width = int(CGImageGetWidth(cg_img))
            height = int(CGImageGetHeight(cg_img))
            if width <= 0 or height <= 0:
                return None

            provider = CGImageGetDataProvider(cg_img)
            data = CGDataProviderCopyData(provider)
            if data is None:
                return None

            bytes_per_row = int(CGImageGetBytesPerRow(cg_img))
            raw = np.frombuffer(data, dtype=np.uint8)
            if raw.size < bytes_per_row * height:
                return None

            rgba = raw.reshape((height, bytes_per_row // 4, 4))[:, :width, :]
            frame = cv2.cvtColor(rgba, cv2.COLOR_BGRA2BGR)
            return frame
        except Exception:
            return None

    def _bbox_overlap_ratio(self, a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> float:
        """Compute overlap ratio between two bboxes (intersection over smaller area)."""
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)
        iw = max(0, ix2 - ix1)
        ih = max(0, iy2 - iy1)
        inter = float(iw * ih)
        if inter <= 0:
            return 0.0
        area_a = float(max(1, (ax2 - ax1) * (ay2 - ay1)))
        area_b = float(max(1, (bx2 - bx1) * (by2 - by1)))
        return inter / min(area_a, area_b)

    def get_recording_mode(self) -> Dict[str, Any]:
        """
        Get current recording mode information.

        Returns:
            Dict with mode, bbox, and screen_index
        """
        return {
            'mode': self.recording_mode,
            'bbox': self.region_bbox,
            'screen_index': self.screen_index,
            'screen_display_id': self.screen_display_id,
        }


    def get_preview_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame for preview.

        Returns:
            numpy array of the frame or None if capture failed
        """
        # Check if we've already detected permission denial
        if hasattr(self, '_preview_permission_denied') and self._preview_permission_denied:
            # Don't keep trying if permission was denied
            return None

        try:
            cv2 = get_cv2()
            if cv2 is None:
                print("[RecordingPresenter] cv2 not available: cannot capture preview")
                return None

            from PIL import ImageGrab

            # Capture screen with region and screen selection support
            try:
                if self.region_bbox:
                    self._refresh_window_follow_bbox_if_needed()
                    if self._window_follow_enabled:
                        win_frame = self._capture_window_frame_by_id(self._window_follow_window_id)
                        if win_frame is not None:
                            return win_frame
                    # Custom region mode
                    screenshot = ImageGrab.grab(bbox=self.region_bbox)
                elif self.screen_index is not None:
                    # Single screen mode - get screen bbox from screen utils
                    try:
                        from memscreen.utils import get_screen_by_index
                        screen_info = get_screen_by_index(self.screen_index)
                        if screen_info:
                            screenshot = ImageGrab.grab(bbox=screen_info.bbox)
                        else:
                            print(f"[RecordingPresenter] Invalid screen index {self.screen_index}, falling back to all screens")
                            screenshot = ImageGrab.grab()
                    except Exception as screen_error:
                        print(f"[RecordingPresenter] Error getting screen bbox: {screen_error}, falling back to all screens")
                        screenshot = ImageGrab.grab()
                else:
                    # Full screen mode (all screens)
                    try:
                        from memscreen.utils import get_combined_screen_bbox
                        screenshot = ImageGrab.grab(bbox=get_combined_screen_bbox())
                    except Exception:
                        screenshot = ImageGrab.grab()
            except Exception as grab_error:
                error_msg = str(grab_error).lower()
                # Check if it's a permission error
                if "permission" in error_msg or "denied" in error_msg or "screen" in error_msg:
                    # Mark permission as denied and stop trying
                    self._preview_permission_denied = True
                    print("[RecordingPresenter] Screen recording permission denied - stopping preview")
                    return None
                else:
                    # Some other error
                    raise grab_error

            # Convert to numpy array and ensure proper format
            frame_array = np.array(screenshot)
            # Ensure uint8 format
            if frame_array.dtype != np.uint8:
                frame_array = frame_array.astype(np.uint8)
            # Convert RGB to BGR
            frame = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)

            return frame

        except ImportError as e:
            # cv2 import failed - likely due to PyInstaller bundling issue
            print(f"[RecordingPresenter] cv2 not available: {e}")
            print("[RecordingPresenter] Preview function requires cv2 - please install opencv-python")
            return None
        except Exception as e:
            self.handle_error(e, "Failed to capture preview frame")
            return None
            return None

    def get_available_screens(self) -> list:
        """
        Get list of available screens for multi-monitor recording.

        Returns:
            List of screen dictionaries with index, name, width, height
        """
        try:
            from memscreen.utils import get_screens

            screens = get_screens()
            screen_list = []

            for screen in screens:
                screen_list.append({
                    'index': screen.index,
                    'name': screen.name,
                    'width': screen.width,
                    'height': screen.height,
                    'is_primary': screen.is_primary,
                    'display_id': screen.display_id,
                })

            return screen_list

        except Exception as e:
            self.handle_error(e, "Failed to get available screens")
            return []

    def get_recordings_list(self) -> list:
        """
        Get list of all recordings.

        Returns:
            List of recording metadata dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT filename, timestamp, frame_count, fps, duration, file_size
                FROM recordings
                ORDER BY timestamp DESC
            ''')

            recordings = []
            for row in cursor.fetchall():
                recordings.append({
                    "filename": row[0],
                    "timestamp": row[1],
                    "frame_count": row[2],
                    "fps": row[3],
                    "duration": row[4],
                    "file_size": row[5]
                })

            conn.close()
            return recordings

        except Exception as e:
            self.handle_error(e, "Failed to get recordings list")
            return []

    def reanalyze_recording_content(self, filename: str) -> Dict[str, Any]:
        """
        Re-run visual analysis on an existing recording and refresh content tags/summary.

        Args:
            filename: Absolute path of the video file.

        Returns:
            Dict with status and generated tags.
        """
        try:
            if not filename:
                return {"ok": False, "error": "filename is required"}
            if not os.path.exists(filename):
                return {"ok": False, "error": f"file not found: {filename}"}

            frame_count, fps, captured_at, duration = self._load_recording_metrics(filename)

            # Fallback metrics from video itself if DB misses.
            if frame_count <= 0 or fps <= 0:
                cv2 = get_cv2()
                if cv2 is not None:
                    cap = cv2.VideoCapture(filename)
                    if cap.isOpened():
                        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or frame_count or 0)
                        fps = float(cap.get(cv2.CAP_PROP_FPS) or fps or 0)
                    cap.release()

            if fps <= 0:
                fps = 1.0 / self.interval if self.interval > 0 else 1.0
            if frame_count <= 0:
                frame_count = max(3, int(duration * fps)) if duration > 0 else 30
            if duration <= 0:
                duration = frame_count / fps if fps > 0 else 0
            if not captured_at:
                captured_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            content_description, frame_details = self._analyze_video_content(filename, frame_count, fps)
            content_tags = self._generate_content_tags(content_description, frame_details)
            self._save_recording_content_metadata(
                filename=filename,
                content_description=content_description,
                content_tags=content_tags,
            )

            # Refresh memory metadata/text as well when memory is available.
            if self.model_capability.can_enrich_memory(self.memory_system):
                timeline_lines, timeline_text = self._build_recording_timeline(captured_at, frame_details)
                suggestion_items = self._generate_recording_suggestions(content_description, frame_details)
                frame_summary = "\n".join(timeline_lines) if timeline_lines else "No frame analysis available."
                memory_text = f"""Screen Recording captured at {captured_at}:
- Duration: {duration:.1f} seconds
- Frames: {frame_count}
- File: {filename}

Observed Timeline (when things were seen):
{frame_summary}

Content Description: {content_description}

Content Tags: {", ".join(content_tags)}
"""
                metadata_updates = {
                    "content_description": content_description,
                    "timeline_text": timeline_text,
                    "frame_details_json": json.dumps(frame_details, ensure_ascii=False),
                    "content_tags": ",".join(content_tags),
                    "content_tags_json": json.dumps(content_tags, ensure_ascii=False),
                    "suggestions": " | ".join(suggestion_items),
                    "analysis_status": "ready",
                    "ocr_text": content_description,
                    "tags": self._build_recording_memory_tags(content_tags),
                }
                memory_id = self._find_recording_memory_id(filename)
                if memory_id:
                    self._update_recording_memory_entry(memory_id, memory_text, metadata_updates)
                else:
                    self.memory_system.add(
                        [{"role": "user", "content": memory_text}],
                        user_id="default_user",
                        metadata={
                            "type": "screen_recording",
                            "category": "screen_recording",
                            "filename": filename,
                            "file_basename": os.path.basename(filename),
                            "frame_count": frame_count,
                            "fps": fps,
                            "duration": duration,
                            "timestamp": captured_at,
                            "seen_at": captured_at,
                            **metadata_updates,
                        },
                        infer=False,
                    )

            return {
                "ok": True,
                "filename": filename,
                "content_tags": content_tags,
                "content_summary": content_description,
            }
        except Exception as e:
            self.handle_error(e, f"Failed to reanalyze recording: {filename}")
            return {"ok": False, "error": str(e)}

    def _load_recording_metrics(self, filename: str) -> Tuple[int, float, str, float]:
        """Load frame_count/fps/timestamp/duration from DB for one recording."""
        frame_count = 0
        fps = 0.0
        timestamp = ""
        duration = 0.0
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT frame_count, fps, timestamp, duration
                FROM recordings
                WHERE filename = ?
                ORDER BY rowid DESC
                LIMIT 1
                """,
                (filename,),
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                frame_count = int(row[0] or 0)
                fps = float(row[1] or 0.0)
                timestamp = str(row[2] or "")
                duration = float(row[3] or 0.0)
        except Exception as e:
            print(f"[RecordingPresenter] Failed to load recording metrics: {e}")
        return frame_count, fps, timestamp, duration

    def _find_recording_memory_id(self, filename: str) -> Optional[str]:
        """Find existing memory id for this recording file if available."""
        if not self.memory_system:
            return None
        try:
            result = self.memory_system.search(
                query=os.path.basename(filename),
                user_id="default_user",
                filters={"type": "screen_recording"},
                limit=10,
                threshold=0.0,
            )
            rows = result.get("results", []) if isinstance(result, dict) else (result or [])
            for row in rows:
                if not isinstance(row, dict):
                    continue
                md = row.get("metadata", {}) or {}
                if str(md.get("filename", "")) == filename:
                    rid = row.get("id")
                    return str(rid) if rid is not None else None
        except Exception as e:
            print(f"[RecordingPresenter] Failed to find recording memory id: {e}")
        return None

    # ==================== Private Methods ====================

    def _record_screen(self):
        """
        Record screen in background thread.
        This method runs in a separate thread.
        """
        # Use safe cv2 loader to avoid PyInstaller recursion
        cv2 = get_cv2()
        if cv2 is None:
            print("[RecordingPresenter] ERROR: cv2 not available for recording")
            self.is_recording = False
            return
        # Capture the very first frame immediately on start.
        # Waiting a full interval before first capture can trigger false startup
        # timeout for users with larger saved interval values.
        last_screenshot_time = 0.0
        last_save_time = time.time()
        consecutive_capture_failures = 0
        # Allow at least one capture interval before declaring startup failure.
        # If interval is configured to a large value (set in Settings), a fixed
        # 4s timeout can falsely fail startup before first frame capture.
        startup_grace = max(4.0, min(30.0, float(self.interval) * 3.0 + 2.0))
        first_frame_deadline = (self.recording_start_time or time.time()) + startup_grace

        # Check if permission was denied before entering recording loop
        if hasattr(self, '_preview_permission_denied') and self._preview_permission_denied:
            print("[RecordingPresenter] Permission was denied during pre-flight check - not starting recording loop")
            self.is_recording = False
            if self.view:
                self.view.show_error("Screen recording permission is required. Please grant permission in System Settings > Privacy & Security > Screen Recording, then restart the app.")
            return

        try:
            from PIL import ImageGrab

            while self.is_recording:
                current_time = time.time()
                elapsed = current_time - self.recording_start_time

                # Startup guard: if no frame is captured shortly after start, fail fast
                # so user can immediately reselect window/region and retry.
                if self.frame_count == 0 and current_time > first_frame_deadline:
                    if self.recording_mode == "region" and self._window_follow_enabled:
                        self.last_start_error = (
                            "Unable to capture selected window. "
                            "Please reselect the target window and retry."
                        )
                    else:
                        self.last_start_error = (
                            "Unable to capture screen frames. "
                            "Please retry recording."
                        )
                    print(f"[RecordingPresenter] {self.last_start_error}")
                    self.is_recording = False
                    if self.view:
                        self.view.show_error(self.last_start_error)
                    break

                # Check if it's time to save a new video segment
                time_since_last_save = current_time - last_save_time
                if time_since_last_save >= self.duration:
                    # Save current frames as a video segment
                    if len(self.recording_frames) > 0:
                        frames_to_save = list(self.recording_frames)
                        self.recording_frames = []

                        # Save in background thread
                        threading.Thread(
                            target=self._save_video_segment,
                            args=(frames_to_save,),
                            daemon=True
                        ).start()

                    last_save_time = current_time

                # Capture frame at specified interval
                time_since_last_shot = current_time - last_screenshot_time
                if time_since_last_shot >= self.interval:
                    try:
                        frame = None
                        # Capture screen with region and screen selection support
                        if self.region_bbox:
                            self._refresh_window_follow_bbox_if_needed()
                            if self._window_follow_enabled:
                                frame = self._capture_window_frame_by_id(self._window_follow_window_id)
                                if frame is None:
                                    # If direct window capture fails temporarily, fall back to region.
                                    screenshot = ImageGrab.grab(bbox=self.region_bbox)
                            else:
                                screenshot = ImageGrab.grab(bbox=self.region_bbox)
                            # Custom region mode
                        elif self.screen_index is not None:
                            # Single screen mode - get screen bbox from screen utils
                            try:
                                from memscreen.utils import get_screen_by_index
                                screen_info = get_screen_by_index(self.screen_index)
                                if screen_info:
                                    screenshot = ImageGrab.grab(bbox=screen_info.bbox)
                                else:
                                    print(f"[RecordingPresenter] Invalid screen index {self.screen_index}, falling back to all screens")
                                    screenshot = ImageGrab.grab()
                            except Exception as screen_error:
                                print(f"[RecordingPresenter] Error getting screen bbox: {screen_error}, falling back to all screens")
                                screenshot = ImageGrab.grab()
                        else:
                            # Full screen mode (all screens)
                            try:
                                from memscreen.utils import get_combined_screen_bbox
                                screenshot = ImageGrab.grab(bbox=get_combined_screen_bbox())
                            except Exception:
                                screenshot = ImageGrab.grab()

                        if frame is None:
                            # Convert to numpy array
                            frame_array = np.array(screenshot)

                            # Debug: print dtype
                            if self.frame_count == 0:
                                print(f"[Recording] Initial frame dtype: {frame_array.dtype}, shape: {frame_array.shape}")

                            # Handle different data types
                            if frame_array.dtype == np.float64 or frame_array.dtype == np.float32:
                                # Float images - normalize to 0-255
                                if frame_array.max() <= 1.0:
                                    frame_array = np.clip(frame_array * 255, 0, 255).astype(np.uint8)
                                else:
                                    frame_array = np.clip(frame_array, 0, 255).astype(np.uint8)
                            elif frame_array.dtype != np.uint8:
                                # Any other non-uint8 type
                                frame_array = np.clip(frame_array, 0, 255).astype(np.uint8)

                            # Ensure we have the right shape and channels
                            if len(frame_array.shape) == 2:
                                # Grayscale - convert to RGB
                                frame_array = cv2.cvtColor(frame_array, cv2.COLOR_GRAY2RGB)
                            elif len(frame_array.shape) == 3 and frame_array.shape[2] == 4:
                                # RGBA - convert to RGB
                                frame_array = cv2.cvtColor(frame_array, cv2.COLOR_RGBA2RGB)

                            # Now convert RGB to BGR for OpenCV
                            if len(frame_array.shape) == 3 and frame_array.shape[2] == 3:
                                frame = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
                            else:
                                frame = frame_array

                        # Validate final frame
                        if frame.dtype != np.uint8:
                            print(f"[Recording] Warning: frame dtype is still {frame.dtype}, converting...")
                            frame = frame.astype(np.uint8)

                        # Keep frame size stable for VideoWriter (window move/resize can change bbox).
                        if self.recording_frames:
                            base_h, base_w = self.recording_frames[0].shape[:2]
                            cur_h, cur_w = frame.shape[:2]
                            if cur_h != base_h or cur_w != base_w:
                                frame = cv2.resize(frame, (base_w, base_h))

                        # Add to frames list
                        self.recording_frames.append(frame)
                        self.frame_count += 1
                        consecutive_capture_failures = 0
                        last_screenshot_time = current_time

                        # Update view with frame count (every frame for responsiveness)
                        if self.view:
                            self.view.on_frame_captured(self.frame_count, elapsed)

                    except Exception as grab_error:
                        error_msg = str(grab_error).lower()
                        # Check if it's a permission error
                        if "permission" in error_msg or "denied" in error_msg or "screen" in error_msg:
                            # Permission denied - stop recording
                            print("[RecordingPresenter] Screen recording permission denied during recording")
                            self._preview_permission_denied = True
                            self.is_recording = False
                            # Notify user
                            if self.view:
                                self.view.show_error("Screen recording permission denied. Please grant permission in System Settings > Privacy & Security > Screen Recording, then restart the app.")
                            break  # Exit the recording loop
                        else:
                            # Some other error - log and continue
                            print(f"[Recording] Error capturing frame: {grab_error}")
                            import traceback
                            traceback.print_exc()
                            consecutive_capture_failures += 1
                            if self.frame_count == 0 and consecutive_capture_failures >= 12:
                                self.last_start_error = (
                                    "Capture failed repeatedly at startup. "
                                    "Please reselect region/window and retry."
                                )
                                self.is_recording = False
                                if self.view:
                                    self.view.show_error(self.last_start_error)
                                break
                            # Continue to next iteration.
                            # Keep retrying quickly until first frame succeeds.
                            if self.frame_count == 0:
                                last_screenshot_time = 0.0
                            else:
                                last_screenshot_time = current_time
                            time.sleep(0.1)
                            continue

                # Sleep a bit to avoid CPU spike
                time.sleep(0.1)

        except Exception as e:
            self.is_recording = False
            self.handle_error(e, "Error during recording")

    def _save_video_segment(self, frames):
        """
        Save a video segment to disk and add to memory.

        Args:
            frames: List of video frames
        """
        try:
            cv2 = get_cv2()
            if cv2 is None:
                print("[RecordingPresenter] ERROR: cv2 not available for saving video")
                return

            if not frames:
                return

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self._build_video_output_path("segment", timestamp)

            # Save video
            fps = 1.0 / self.interval
            target_w, target_h = self._normalize_video_size(frames[0].shape[1], frames[0].shape[0])
            if target_w != frames[0].shape[1] or target_h != frames[0].shape[0]:
                normalized = []
                for frame in frames:
                    if frame.shape[1] != target_w or frame.shape[0] != target_h:
                        frame = cv2.resize(frame, (target_w, target_h))
                    normalized.append(frame)
                frames = normalized
            out, filename, _used_ext = self._open_video_writer(
                cv2,
                filename,
                fps,
                (target_w, target_h),
            )

            for frame in frames:
                out.write(frame)

            out.release()

            # Get file size
            file_size = os.path.getsize(filename)

            # Save to database
            self._save_to_database(filename, len(frames), fps, len(frames) / fps, file_size)

            # Add to memory system
            if self.memory_system:
                self._add_video_to_memory(filename, len(frames), fps)
            else:
                self._memory_index_ready_event.set()
                captured_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                duration = len(frames) / fps if fps > 0 else 0
                threading.Thread(
                    target=self._enrich_recording_memory,
                    args=(None, filename, len(frames), fps, captured_at, duration),
                    daemon=True,
                ).start()

            print(f"[RecordingPresenter] Saved segment: {filename}")

        except Exception as e:
            self.handle_error(e, "Failed to save video segment")

    def _save_recording(self, frames, audio_file=None):
        """
        Save final recording when user stops recording.

        Args:
            frames: List of video frames
            audio_file: Optional path to audio file to merge
        """
        try:
            print(f"[RecordingPresenter] 🎬 Starting to save recording... ({len(frames)} frames)")

            cv2 = get_cv2()
            if cv2 is None:
                print("[RecordingPresenter] ERROR: cv2 not available for saving recording")
                self.show_error("Video recording is not available")
                return

            if not frames:
                print("[RecordingPresenter] WARNING: No frames to save")
                self.show_info("No frames to save")
                return

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self._build_video_output_path("recording", timestamp)

            print(f"[RecordingPresenter] 📁 Saving to file: {filename}")

            # Save video
            fps = 1.0 / self.interval
            target_w, target_h = self._normalize_video_size(frames[0].shape[1], frames[0].shape[0])
            if target_w != frames[0].shape[1] or target_h != frames[0].shape[0]:
                normalized = []
                for frame in frames:
                    if frame.shape[1] != target_w or frame.shape[0] != target_h:
                        frame = cv2.resize(frame, (target_w, target_h))
                    normalized.append(frame)
                frames = normalized
            out, filename, _used_ext = self._open_video_writer(
                cv2,
                filename,
                fps,
                (target_w, target_h),
            )

            for frame in frames:
                out.write(frame)

            out.release()

            print(f"[RecordingPresenter] ✅ Video file saved: {filename}")

            # Merge audio if provided
            merged_audio = False
            if audio_file and os.path.exists(audio_file):
                merged_filename = self._merge_audio_video(filename, audio_file)
                merged_audio = merged_filename != filename
                filename = merged_filename

            # Get file size
            file_size = os.path.getsize(filename)

            print(f"[RecordingPresenter] 📊 File size: {file_size / 1024 / 1024:.2f} MB")

            # Save to database
            db_audio_file = audio_file if (audio_file and os.path.exists(audio_file)) else None
            if not merged_audio and db_audio_file:
                print("[RecordingPresenter] Audio was recorded but not merged into video.")
            self._save_to_database(filename, len(frames), fps, len(frames) / fps, file_size, db_audio_file)

            # Add to memory system
            if self.memory_system:
                self._add_video_to_memory(filename, len(frames), fps)
            else:
                captured_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                duration = len(frames) / fps if fps > 0 else 0
                threading.Thread(
                    target=self._enrich_recording_memory,
                    args=(None, filename, len(frames), fps, captured_at, duration),
                    daemon=True,
                ).start()

            # Notify view
            if self.view:
                self.view.on_recording_saved(filename, file_size)

            print(f"[RecordingPresenter] ✅ Recording save complete: {filename}")

        except Exception as e:
            print(f"[RecordingPresenter] ❌ ERROR in _save_recording: {e}")
            import traceback
            traceback.print_exc()
            self._memory_index_ready_event.set()
            self.handle_error(e, "Failed to save recording")

    def _normalize_video_size(self, width: int, height: int) -> Tuple[int, int]:
        """
        Ensure output video dimensions are valid for common H264/AAC merge pipelines.
        """
        target_w = max(2, int(width) - (int(width) % 2))
        target_h = max(2, int(height) - (int(height) % 2))
        return target_w, target_h

    def _build_video_output_path(self, prefix: str, timestamp: str) -> str:
        """Build output video path with currently selected container format."""
        ext = self.video_format if self.video_format in SUPPORTED_VIDEO_FORMATS else "mp4"
        return os.path.join(self.output_dir, f"{prefix}_{timestamp}.{ext}")

    def _get_video_fourcc_candidates(self, ext: str) -> List[str]:
        """Return preferred codec candidates for a target container extension."""
        normalized = str(ext or "").strip().lower()
        if normalized == "mov":
            return ["avc1", "mp4v", "MJPG", "XVID"]
        if normalized == "mkv":
            return ["XVID", "MJPG", "mp4v", "avc1"]
        if normalized == "avi":
            return ["XVID", "MJPG", "mp4v"]
        return ["mp4v", "avc1", "XVID", "MJPG"]

    def _open_video_writer(
        self,
        cv2,
        path: str,
        fps: float,
        size: Tuple[int, int],
    ) -> Tuple[Any, str, str]:
        """
        Open a VideoWriter with codec/container fallback.

        Returns:
            (writer, output_path, used_ext)
        """
        target_ext = os.path.splitext(path)[1].lstrip(".").lower() or "mp4"
        codec_candidates = self._get_video_fourcc_candidates(target_ext)
        for codec in codec_candidates:
            writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*codec), fps, size)
            if writer is not None and writer.isOpened():
                return writer, path, target_ext
            if writer is not None:
                writer.release()

        # Container fallback: write MP4 if target format is unsupported on runtime.
        fallback_path = os.path.splitext(path)[0] + ".mp4"
        for codec in self._get_video_fourcc_candidates("mp4"):
            writer = cv2.VideoWriter(
                fallback_path,
                cv2.VideoWriter_fourcc(*codec),
                fps,
                size,
            )
            if writer is not None and writer.isOpened():
                print(
                    "[RecordingPresenter] Video writer fallback to mp4 "
                    f"(requested={target_ext}, codec={codec})"
                )
                return writer, fallback_path, "mp4"
            if writer is not None:
                writer.release()

        raise RuntimeError(
            f"Failed to initialize video writer for formats: {target_ext}, mp4"
        )

    def _resolve_ffmpeg_binary(self) -> Optional[str]:
        """
        Resolve ffmpeg binary path for packaged/runtime environments.
        """
        env_ffmpeg = os.environ.get("MEMSCREEN_FFMPEG_PATH")
        if env_ffmpeg and os.path.exists(env_ffmpeg):
            return env_ffmpeg
        found = shutil.which("ffmpeg")
        if found:
            return found
        try:
            import imageio_ffmpeg  # type: ignore

            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            if ffmpeg_exe and os.path.exists(ffmpeg_exe):
                return ffmpeg_exe
        except Exception:
            pass
        return None

    def _merge_audio_video(self, video_file: str, audio_file: str) -> str:
        """
        Merge audio and video files using moviepy or ffmpeg.

        Args:
            video_file: Path to video file
            audio_file: Path to audio file

        Returns:
            Path to merged video file
        """
        # Generate output filename once and reuse across merge backends.
        base_dir = os.path.dirname(video_file)
        base_name = os.path.splitext(os.path.basename(video_file))[0]
        video_ext = os.path.splitext(video_file)[1].strip().lower() or ".mp4"
        output_file = os.path.join(base_dir, f"{base_name}_with_audio{video_ext}")

        moviepy_codec = "libx264"
        moviepy_audio_codec = "aac"
        ffmpeg_audio_codec = "aac"
        ffmpeg_video_codec = "libx264"
        if video_ext == ".avi":
            moviepy_codec = "mpeg4"
            moviepy_audio_codec = "libmp3lame"
            ffmpeg_audio_codec = "libmp3lame"
            ffmpeg_video_codec = "mpeg4"
        elif video_ext == ".mkv":
            moviepy_codec = "libx264"
            moviepy_audio_codec = "aac"

        try:
            from moviepy.editor import VideoFileClip, AudioFileClip

            video = VideoFileClip(video_file)
            audio = AudioFileClip(audio_file)
            video_with_audio = video.set_audio(audio)
            video_with_audio.write_videofile(
                output_file,
                codec=moviepy_codec,
                audio_codec=moviepy_audio_codec,
                verbose=False,
                logger=None
            )
            video.close()
            audio.close()
            video_with_audio.close()
            os.remove(video_file)
            print(f"[RecordingPresenter] Merged audio and video with moviepy: {output_file}")
            return output_file
        except ImportError:
            print("[RecordingPresenter] moviepy is unavailable, trying ffmpeg merge...")
        except Exception as e:
            print(f"[RecordingPresenter] moviepy merge failed: {e}. Trying ffmpeg merge...")

        ffmpeg_bin = self._resolve_ffmpeg_binary()
        if not ffmpeg_bin:
            print("[RecordingPresenter] ffmpeg not found, skipping audio merge")
            return video_file

        ffmpeg_copy_cmd = [
            ffmpeg_bin, "-y",
            "-i", video_file,
            "-i", audio_file,
            "-c:v", "copy",
            "-c:a", ffmpeg_audio_codec,
            "-shortest",
            output_file,
        ]
        try:
            subprocess.run(ffmpeg_copy_cmd, check=True, capture_output=True, text=True)
            os.remove(video_file)
            print(f"[RecordingPresenter] Merged audio and video with ffmpeg(copy): {output_file}")
            return output_file
        except Exception as e:
            stderr = ""
            if hasattr(e, "stderr") and e.stderr:
                stderr = str(e.stderr).strip().splitlines()[-1]
            print(f"[RecordingPresenter] ffmpeg(copy) merge failed: {e} {stderr}")

        ffmpeg_reencode_cmd = [
            ffmpeg_bin, "-y",
            "-i", video_file,
            "-i", audio_file,
            "-c:v", ffmpeg_video_codec,
            "-c:a", ffmpeg_audio_codec,
            "-shortest",
        ]
        if ffmpeg_video_codec == "libx264":
            ffmpeg_reencode_cmd.extend(["-pix_fmt", "yuv420p"])
        ffmpeg_reencode_cmd.append(output_file)
        try:
            subprocess.run(ffmpeg_reencode_cmd, check=True, capture_output=True, text=True)
            os.remove(video_file)
            print(f"[RecordingPresenter] Merged audio and video with ffmpeg(reencode): {output_file}")
            return output_file
        except Exception as e:
            stderr = ""
            if hasattr(e, "stderr") and e.stderr:
                stderr = str(e.stderr).strip().splitlines()[-1]
            print(f"[RecordingPresenter] ffmpeg(reencode) merge failed: {e} {stderr}")
            return video_file

    def _save_to_database(self, filename, frame_count, fps, duration, file_size, audio_file=None):
        """Save recording metadata to database"""
        try:
            import json

            print(f"[RecordingPresenter] 📝 Saving to database: {filename}")
            print(f"[RecordingPresenter]    - frame_count={frame_count}, fps={fps}, duration={duration:.2f}s, size={file_size}")

            # Use check_same_thread=False for multi-threaded access
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()

            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Prepare metadata
            recording_mode = getattr(self, 'recording_mode', 'fullscreen')
            region_bbox = json.dumps(self.region_bbox) if getattr(self, 'region_bbox', None) else None
            window_title = getattr(self, 'window_title', None)
            content_tags = None
            content_summary = None
            audio_source = self._active_audio_source if self._active_audio_source != AudioSource.NONE else self.audio_source
            audio_source_str = audio_source.value if audio_source != AudioSource.NONE else None

            cursor.execute('''
                INSERT INTO recordings (
                    filename, timestamp, frame_count, fps, duration, file_size,
                    recording_mode, region_bbox, window_title, content_tags, content_summary,
                    audio_file, audio_source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                filename, timestamp, frame_count, fps, duration, file_size,
                recording_mode, region_bbox, window_title, content_tags, content_summary,
                audio_file, audio_source_str
            ))

            conn.commit()

            # Verify the insert was successful
            cursor.execute('SELECT rowid FROM recordings WHERE filename = ? ORDER BY rowid DESC LIMIT 1', (filename,))
            result = cursor.fetchone()
            if result:
                print(f"[RecordingPresenter] ✅ Verified in database: rowid={result[0]}")
            else:
                print(f"[RecordingPresenter] ⚠️ WARNING: Insert may have failed - not found in database")

            conn.close()

            print(f"[RecordingPresenter] ✅ Successfully saved to database: {filename}")

        except Exception as e:
            print(f"[RecordingPresenter] ❌ ERROR saving to database: {e}")
            import traceback
            traceback.print_exc()
            self.handle_error(e, "Failed to save to database")

    def _add_video_to_memory(self, filename, frame_count, fps):
        """
        Add recording to memory in two phases:
        1) fast placeholder entry (immediate, no vision call)
        2) async enrichment with timeline/content analysis
        """
        try:
            if not self.model_capability.can_enrich_memory(self.memory_system):
                self._memory_index_ready_event.set()
                return

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            duration = frame_count / fps if fps > 0 else 0
            base_name = os.path.basename(filename)

            # Fast memory write so chat can immediately reference "when" evidence.
            memory_text = f"""Screen Recording captured at {timestamp}:
- Duration: {duration:.1f} seconds
- Frames: {frame_count}
- File: {filename}

Observed Timeline (when things were seen):
- {timestamp}: Recording finished. Detailed visual analysis is in progress.

This video screen recording shows what was displayed on screen during the recording period.
When users ask about what was on their screen or what they were doing, always reference this timestamp."""

            print(f"[RecordingPresenter] Adding fast recording memory: {filename}")
            print(f"[RecordingPresenter] - Duration: {duration:.1f}s, Frames: {frame_count}, FPS: {fps}")

            result = self.memory_system.add(
                [{"role": "user", "content": memory_text}],
                user_id="default_user",  # Use consistent user_id for chat and recordings
                metadata={
                    "type": "screen_recording",
                    "category": "screen_recording",
                    "tags": "screen_recording,timeline_pending",
                    "filename": filename,
                    "file_basename": base_name,
                    "frame_count": frame_count,
                    "fps": fps,
                    "duration": duration,
                    "timestamp": timestamp,  # human-readable seen time
                    "seen_at": timestamp,
                    "content_description": "Recording saved. Detailed visual analysis is in progress.",
                    "timeline_text": f"+0.00s: recording saved ({base_name})",
                    "frame_details_json": "[]",
                    "suggestions": "Wait a few seconds, then ask what appeared and when. I will answer from the timeline.",
                    "analysis_status": "pending",
                    "ocr_text": base_name,
                },
                infer=False  # Faster update for chat queries; keep raw timeline facts
            )

            memory_id = None
            if isinstance(result, dict):
                rows = result.get("results", []) or []
                if rows and isinstance(rows[0], dict):
                    memory_id = rows[0].get("id")

            print(f"[RecordingPresenter] ✅ Fast memory added: {filename} (id={memory_id})")
            self._memory_index_ready_event.set()

            # Enrich content asynchronously to avoid blocking chat availability.
            enrich_thread = threading.Thread(
                target=self._enrich_recording_memory,
                args=(memory_id, filename, frame_count, fps, timestamp, duration),
                daemon=True,
            )
            enrich_thread.start()

        except Exception as e:
            self._memory_index_ready_event.set()
            if self.model_capability.consume_model_error(
                e, f"memory write for recording {os.path.basename(filename)}"
            ):
                return
            self.handle_error(e, "Failed to add video to memory")

    def _enrich_recording_memory(
        self,
        memory_id: Optional[str],
        filename: str,
        frame_count: int,
        fps: float,
        captured_at: str,
        duration: float,
    ) -> None:
        """Asynchronously enrich recording memory with timeline/details."""
        try:
            content_description, frame_details = self._analyze_video_content(filename, frame_count, fps)
            content_tags = self._generate_content_tags(content_description, frame_details)
            self._save_recording_content_metadata(
                filename=filename,
                content_description=content_description,
                content_tags=content_tags,
            )

            if not self.model_capability.can_enrich_memory(self.memory_system):
                print(f"[RecordingPresenter] Content tags saved without memory_system: {filename} -> {content_tags}")
                return
            timeline_lines, timeline_text = self._build_recording_timeline(captured_at, frame_details)
            suggestions = self._generate_recording_suggestions(content_description, frame_details)
            suggestion_text = "\n".join(f"- {item}" for item in suggestions)
            frame_summary = "\n".join(timeline_lines) if timeline_lines else "No frame analysis available."
            content_tag_text = ", ".join(content_tags) if content_tags else "general"

            enriched_text = f"""Screen Recording captured at {captured_at}:
- Duration: {duration:.1f} seconds
- Frames: {frame_count}
- File: {filename}

Observed Timeline (when things were seen):
{frame_summary}

Content Description: {content_description}

Content Tags: {content_tag_text}

Actionable Suggestions:
{suggestion_text}

This video screen recording shows what was displayed on screen during the recording period.
When users ask about what was on their screen or what they were doing, reference this recording with explicit time points."""

            metadata_updates = {
                "content_description": content_description,
                "timeline_text": timeline_text,
                "frame_details_json": json.dumps(frame_details, ensure_ascii=False),
                "content_tags": ",".join(content_tags),
                "content_tags_json": json.dumps(content_tags, ensure_ascii=False),
                "suggestions": " | ".join(suggestions),
                "analysis_status": "ready",
                "ocr_text": content_description,
                "category": "screen_recording",
                "tags": self._build_recording_memory_tags(content_tags),
            }

            updated = self._update_recording_memory_entry(memory_id, enriched_text, metadata_updates)
            if updated:
                print(f"[RecordingPresenter] ✅ Recording memory enriched: {filename}")
            else:
                # Fallback: add a new enriched entry if direct update is unavailable.
                self.memory_system.add(
                    [{"role": "user", "content": enriched_text}],
                    user_id="default_user",
                    metadata={
                        "type": "screen_recording",
                        "filename": filename,
                        "frame_count": frame_count,
                        "fps": fps,
                        "duration": duration,
                        "timestamp": captured_at,
                        "seen_at": captured_at,
                        **metadata_updates,
                    },
                    infer=False,
                )
                print(f"[RecordingPresenter] ✅ Recording memory enriched via fallback add: {filename}")

        except Exception as e:
            if self.model_capability.consume_model_error(
                e, f"memory enrichment for recording {os.path.basename(filename)}"
            ):
                return
            self.handle_error(e, "Failed to enrich recording memory")

    def _update_recording_memory_entry(
        self,
        memory_id: Optional[str],
        memory_text: str,
        metadata_updates: Dict[str, Any],
    ) -> bool:
        """Update existing memory entry while preserving payload metadata."""
        if not memory_id:
            return False

        try:
            vector_store = getattr(self.memory_system, "vector_store", None)
            embedding_model = getattr(self.memory_system, "embedding_model", None)
            if vector_store is None or embedding_model is None:
                return False

            existing = vector_store.get(vector_id=memory_id)
            if existing is None:
                return False

            payload = dict(getattr(existing, "payload", {}) or {})
            prev_text = payload.get("data")

            payload.update(metadata_updates or {})
            payload["data"] = memory_text
            payload["hash"] = hashlib.md5(memory_text.encode()).hexdigest()
            payload["updated_at"] = datetime.now().isoformat()

            embeddings = embedding_model.embed(memory_text, "update")
            vector_store.update(vector_id=memory_id, vector=embeddings, payload=payload)

            db = getattr(self.memory_system, "db", None)
            if db and hasattr(db, "add_history"):
                db.add_history(
                    memory_id,
                    prev_text,
                    memory_text,
                    "UPDATE",
                    created_at=payload.get("created_at"),
                    updated_at=payload.get("updated_at"),
                    actor_id=payload.get("actor_id"),
                    role=payload.get("role"),
                    immediate=False,
                )

            return True
        except Exception as update_err:
            print(f"[RecordingPresenter] Failed to update memory entry {memory_id}: {update_err}")
            return False

    def _build_recording_timeline(
        self,
        captured_at: str,
        frame_details: List[Dict[str, Any]],
    ) -> Tuple[List[str], str]:
        """Build a compact timeline that can be cited in chat answers."""
        if not frame_details:
            return [], ""

        timeline_lines = []
        compact_entries = []
        for frame_info in frame_details[:5]:
            frame_num = frame_info.get("frame_number", 0)
            frame_time = frame_info.get("timestamp", 0)
            frame_text = frame_info.get("text", "No text detected")
            frame_text = " ".join(str(frame_text).split())
            if len(frame_text) > 180:
                frame_text = frame_text[:180] + "..."

            line = f"- {captured_at} (+{frame_time:.2f}s, frame #{frame_num}): {frame_text}"
            timeline_lines.append(line)
            compact_entries.append(f"+{frame_time:.2f}s:{frame_text}")

        return timeline_lines, " | ".join(compact_entries)

    def _generate_recording_suggestions(
        self,
        content_description: str,
        frame_details: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate simple actionable suggestions from captured content."""
        text_pool = [content_description or ""]
        for frame in frame_details[:5]:
            text_pool.append(str(frame.get("text", "")))

        merged_text = " ".join(text_pool).lower()
        suggestions = []

        if any(k in merged_text for k in ["error", "exception", "failed", "warning", "permission denied"]):
            suggestions.append("An error was detected. Record the key error text first, then check permissions and dependencies.")

        if any(k in merged_text for k in ["todo", "deadline", "meeting", "plan", "task"]):
            suggestions.append("Task/schedule content was detected. Convert key items into todos and add reminders.")

        if any(k in merged_text for k in ["code", "terminal", "vscode", "python", "git"]):
            suggestions.append("A development workflow was detected. Capture the key changes and commit code promptly.")

        if not suggestions:
            suggestions.append("Review key frames in timeline order and confirm the next action.")

        return suggestions[:3]

    def _generate_content_tags(
        self,
        content_description: str,
        frame_details: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Generate content-centric semantic tags from vision-analyzed frame text.
        Tags are derived from frame-level visual descriptions + OCR fallbacks.
        """
        text_pool: List[str] = [content_description or ""]
        for frame in frame_details[:8]:
            text_pool.append(str(frame.get("text", "")))
        merged = " ".join(text_pool).lower()

        tags: List[str] = []

        tag_rules = {
            "coding": ["vscode", "xcode", "pycharm", "intellij", "source code", "coding"],
            "terminal": ["terminal", "shell", "bash", "zsh", "powershell", "command line"],
            "debugging": ["error", "exception", "traceback", "failed", "warning"],
            "meeting": ["zoom", "teams", "meeting", "feishu", "google meet"],
            "browser": ["chrome", "safari", "firefox", "edge", "browser", "web"],
            "research": ["paper", "arxiv", "abstract", "reference", "research"],
            "document": ["doc", "document", "pdf", "notion", "word", "notes"],
            "spreadsheet": ["excel", "spreadsheet", "sheet", "table"],
            "chat": ["slack", "discord", "wechat", "telegram", "chat", "message"],
            "design": ["figma", "sketch", "photoshop", "design", "ui", "canvas"],
            "presentation": ["ppt", "slides", "keynote", "presentation"],
            "dashboard": ["dashboard", "grafana", "datadog", "analytics", "metrics"],
        }

        for tag, keywords in tag_rules.items():
            if any(k in merged for k in keywords):
                tags.append(tag)

        # Fallback + cap
        if not tags:
            tags.append("general")

        # Keep deterministic order (no hard cap on tag count).
        deduped: List[str] = []
        seen = set()
        for tag in tags:
            if tag in seen:
                continue
            seen.add(tag)
            deduped.append(tag)
        return deduped

    def _build_recording_memory_tags(self, content_tags: List[str]) -> str:
        """Build comma-separated tags string for memory payload filtering/ranking."""
        base_tags = ["screen_recording", "timeline_ready", "ocr_enriched"]
        semantic_tags = [f"semantic:{tag}" for tag in content_tags if tag]
        merged = base_tags + semantic_tags
        # Preserve order while deduping
        out: List[str] = []
        seen = set()
        for tag in merged:
            if tag in seen:
                continue
            seen.add(tag)
            out.append(tag)
        return ",".join(out)

    def _save_recording_content_metadata(
        self,
        filename: str,
        content_description: str,
        content_tags: List[str],
    ) -> None:
        """Persist enriched content metadata into recordings DB for video organization."""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE recordings
                SET content_tags = ?, content_summary = ?
                WHERE filename = ?
                """,
                (
                    json.dumps(content_tags, ensure_ascii=False),
                    content_description[:500] if content_description else None,
                    filename,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[RecordingPresenter] Failed to save content metadata for {filename}: {e}")

    def _analyze_video_content(self, filename, total_frames, fps):
        """Analyze video content by sampling frames and using vision model"""
        try:
            cv2 = get_cv2()
            if cv2 is None:
                print("[RecordingPresenter] cv2 not available for video analysis")
                return "Video recording (analysis unavailable)", []

            # Sample frames for analysis
            num_samples = min(3, total_frames)
            sample_indices = [int(i * total_frames / num_samples) for i in range(num_samples)]

            frame_details = []  # Store structured frame information
            all_text_found = []
            cap = cv2.VideoCapture(filename)

            for sample_idx, frame_idx in enumerate(sample_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    # Calculate timestamp for this frame
                    timestamp = frame_idx / fps if fps > 0 else 0

                    # Use vision model only for the first few samples to reduce latency.
                    frame_text = self.model_capability.extract_text_from_frame(
                        frame,
                        use_vision=(sample_idx < 2),
                    )

                    # Store frame details
                    frame_info = {
                        "frame_number": frame_idx,
                        "timestamp": round(timestamp, 2),
                        "text": frame_text
                    }
                    frame_details.append(frame_info)

                    if frame_text:
                        all_text_found.append(frame_text)

            cap.release()

            # Combine all found text for backward compatibility
            combined_text = " | ".join(all_text_found) if all_text_found else "Screen recording captured (no clear text detected)"

            # Return both combined text and detailed frame information
            return combined_text, frame_details

        except Exception as e:
            self.handle_error(e, "Failed to analyze video content")
            return "Screen recording (content analysis unavailable)", []

    def delete_recording(self, filename):
        """Delete a recording file and database entry"""
        try:
            # Delete file
            if os.path.exists(filename):
                os.remove(filename)

            # Delete from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM recordings WHERE filename = ?', (filename,))
            conn.commit()
            conn.close()

            # Notify view
            if self.view:
                self.view.on_recording_deleted(filename)

        except Exception as e:
            self.handle_error(e, f"Failed to delete recording: {filename}")

    def cleanup(self):
        """
        Cleanup method to ensure save operations complete before app exits.
        Call this when shutting down the application.
        """
        print("[RecordingPresenter] 🧹 Cleanup started...")

        # Stop recording if active
        if self.is_recording:
            print("[RecordingPresenter] Stopping active recording...")
            self.stop_recording()

        # Wait for save thread to complete
        if self._save_thread and self._save_thread.is_alive():
            print("[RecordingPresenter] ⏳ Waiting for save thread to complete (max 30s)...")
            self._save_thread.join(timeout=30)
            if self._save_thread.is_alive():
                print("[RecordingPresenter] ⚠️ WARNING: Save thread still running after 30s timeout")
            else:
                print("[RecordingPresenter] ✅ Save thread completed successfully")

        print("[RecordingPresenter] ✅ Cleanup complete")
