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
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from .base_presenter import BasePresenter
from memscreen.audio import AudioRecorder, AudioSource
from memscreen.cv2_loader import get_cv2, is_cv2_available


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

    def __init__(self, view=None, memory_system=None, db_path=None, output_dir=None, audio_dir=None):
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

        # Audio recording
        self.audio_recorder = AudioRecorder(output_dir=audio_dir)
        self.audio_source = AudioSource.NONE  # none, microphone, system_audio

        # Statistics
        self.frame_count = 0
        self.current_file = None

        # Recording mode support
        self.recording_mode = 'fullscreen'  # fullscreen, region
        self.region_bbox = None  # (left, top, right, bottom) or None
        self.screen_index = None  # Index of screen to record (None = all screens/primary)
        self.window_title = None  # Optional window/app label for region-window mode
        self.content_tags: List[str] = []
        self.content_summary: Optional[str] = None

        # Services (lazy loaded)
        self.region_config = None

        self._is_initialized = False
        self._easyocr_reader = None

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
            source: AudioSource enum (MICROPHONE, SYSTEM_AUDIO, NONE)
        """
        self.audio_source = source
        self.audio_recorder.set_audio_source(source)
        print(f"[RecordingPresenter] Audio source set to: {source.value}")

    def get_audio_sources(self) -> list:
        """
        Get list of available audio sources.

        Returns:
            List of available AudioSource values
        """
        return [AudioSource.NONE, AudioSource.MICROPHONE, AudioSource.SYSTEM_AUDIO]

    def start_recording(self, duration: int = 60, interval: float = 2.0) -> bool:
        """
        Start screen recording.

        Args:
            duration: Duration in seconds per video segment
            interval: Interval in seconds between frame captures

        Returns:
            True if recording started successfully
        """
        if self.is_recording:
            self.show_error("Recording is already in progress")
            return False

        # Check if cv2 is available
        if not self.cv2_available:
            error_msg = "Video recording requires opencv-python (cv2), but it's not available. "
            error_msg += "This is likely due to missing SDL2 dependencies. "
            error_msg += "Please check the console for details."
            self.show_error(error_msg)
            print("[RecordingPresenter] ERROR: Cannot start recording - cv2 not available")
            return False

        # Reset permission denied flag - user is explicitly trying to record
        self._preview_permission_denied = False

        # Pre-flight permission check - test permission BEFORE starting recording thread
        # This prevents repeated permission dialogs during recording loop
        print("[RecordingPresenter] Performing pre-flight permission check...")
        try:
            from PIL import ImageGrab
            # Try to capture a tiny region to test permission
            test_img = ImageGrab.grab(bbox=(0, 0, 1, 1))
            print("[RecordingPresenter] ✓ Pre-flight permission check passed")
            # If we get here without exception, permission is granted
            del test_img  # Discard test image
        except Exception as test_error:
            error_msg = str(test_error).lower()
            if "permission" in error_msg or "denied" in error_msg or "screen" in error_msg:
                print(f"[RecordingPresenter] ✗ Pre-flight permission check failed: {test_error}")
                self._preview_permission_denied = True
                self.show_error("Screen recording permission is required. Please grant permission in System Settings > Privacy & Security > Screen Recording, then restart the app.")
                return False
            # If it's some other error, log but continue
            print(f"[RecordingPresenter] Warning: Pre-flight check had non-permission error: {test_error}")

        try:
            self.duration = duration
            self.interval = interval
            self.is_recording = True
            self.recording_frames = []
            self.recording_start_time = time.time()
            self.frame_count = 0

            # Start audio recording if audio source is set
            if self.audio_source != AudioSource.NONE:
                self.audio_recorder.start_recording(self.audio_source)

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
            if self.audio_source != AudioSource.NONE:
                audio_file = self.audio_recorder.stop_recording()

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
            mode: 'fullscreen', 'fullscreen-single', or 'region'
            **kwargs:
                - bbox: region bbox tuple (for 'region' mode)
                - screen_index: screen index (for 'fullscreen-single' or screen-local 'region' mode)

        Returns:
            True if mode set successfully
        """
        try:
            self.recording_mode = mode
            window_title = kwargs.get('window_title')
            self.window_title = window_title.strip() if isinstance(window_title, str) and window_title.strip() else None

            if mode == 'fullscreen':
                # Capture all screens combined
                self.region_bbox = None
                self.screen_index = None
                self.window_title = None
                print("[RecordingPresenter] Mode set to: Full Screen (all screens)")

            elif mode == 'fullscreen-single':
                # Capture a specific screen
                screen_index = kwargs.get('screen_index')
                if screen_index is not None:
                    self.screen_index = int(screen_index)
                    self.region_bbox = None
                    self.window_title = None
                    print(f"[RecordingPresenter] Mode set to: Full Screen {self.screen_index + 1}")
                else:
                    raise ValueError("screen_index is required for fullscreen-single mode")

            elif mode == 'region':
                bbox = kwargs.get('bbox')
                if bbox and len(bbox) == 4:
                    # Ensure bbox elements are integers for PIL ImageGrab.
                    local_bbox = tuple(int(x) for x in bbox)
                    screen_index = kwargs.get('screen_index')
                    if screen_index is not None:
                        from memscreen.utils import get_screen_by_index
                        resolved_screen_index = int(screen_index)
                        screen_info = get_screen_by_index(resolved_screen_index)
                        if not screen_info:
                            raise ValueError(f"Invalid screen_index for region mode: {resolved_screen_index}")

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
                    else:
                        # Backward-compatible path: treat bbox as global coordinates.
                        self.region_bbox = local_bbox
                        self.screen_index = None
                    if self.window_title:
                        print(f"[RecordingPresenter] Mode set to: Window Region {self.region_bbox} ({self.window_title})")
                    else:
                        print(f"[RecordingPresenter] Mode set to: Custom Region {self.region_bbox}")
                else:
                    raise ValueError("Invalid bbox for region mode")

            else:
                raise ValueError(f"Invalid recording mode: {mode}")

            return True

        except Exception as e:
            self.handle_error(e, f"Failed to set recording mode to {mode}")
            return False

    def get_recording_mode(self) -> Dict[str, Any]:
        """
        Get current recording mode information.

        Returns:
            Dict with mode, bbox, and screen_index
        """
        return {
            'mode': self.recording_mode,
            'bbox': self.region_bbox,
            'screen_index': self.screen_index
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
                    'is_primary': screen.is_primary
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
            if self.memory_system:
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
        last_screenshot_time = time.time()
        last_save_time = time.time()

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
                        # Capture screen with region and screen selection support
                        if self.region_bbox:
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
                            screenshot = ImageGrab.grab()

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

                        # Add to frames list
                        self.recording_frames.append(frame)
                        self.frame_count += 1
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
                            # Continue to next iteration
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
            filename = os.path.join(self.output_dir, f"segment_{timestamp}.mp4")

            # Save video
            fps = 1.0 / self.interval
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(filename, fourcc, fps, (frames[0].shape[1], frames[0].shape[0]))

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
            filename = os.path.join(self.output_dir, f"recording_{timestamp}.mp4")

            print(f"[RecordingPresenter] 📁 Saving to file: {filename}")

            # Save video
            fps = 1.0 / self.interval
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(filename, fourcc, fps, (frames[0].shape[1], frames[0].shape[0]))

            for frame in frames:
                out.write(frame)

            out.release()

            print(f"[RecordingPresenter] ✅ Video file saved: {filename}")

            # Merge audio if provided
            if audio_file and os.path.exists(audio_file):
                filename = self._merge_audio_video(filename, audio_file)

            # Get file size
            file_size = os.path.getsize(filename)

            print(f"[RecordingPresenter] 📊 File size: {file_size / 1024 / 1024:.2f} MB")

            # Save to database
            self._save_to_database(filename, len(frames), fps, len(frames) / fps, file_size, audio_file)

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

    def _merge_audio_video(self, video_file: str, audio_file: str) -> str:
        """
        Merge audio and video files using moviepy or ffmpeg.

        Args:
            video_file: Path to video file
            audio_file: Path to audio file

        Returns:
            Path to merged video file
        """
        try:
            from moviepy.editor import VideoFileClip, AudioFileClip

            # Load video and audio
            video = VideoFileClip(video_file)
            audio = AudioFileClip(audio_file)

            # Set audio to video
            video_with_audio = video.set_audio(audio)

            # Generate output filename
            import os
            base_dir = os.path.dirname(video_file)
            base_name = os.path.splitext(os.path.basename(video_file))[0]
            output_file = os.path.join(base_dir, f"{base_name}_with_audio.mp4")

            # Write video with audio
            video_with_audio.write_videofile(
                output_file,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )

            # Close clips
            video.close()
            audio.close()
            video_with_audio.close()

            # Remove original video file
            os.remove(video_file)

            print(f"[RecordingPresenter] Merged audio and video: {output_file}")
            return output_file

        except ImportError:
            print("[RecordingPresenter] moviepy not installed, skipping audio merge")
            print("[RecordingPresenter] Install with: pip install moviepy")
            return video_file
        except Exception as e:
            print(f"[RecordingPresenter] Failed to merge audio/video: {e}")
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
            audio_source_str = self.audio_source.value if self.audio_source != AudioSource.NONE else None

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
            if not self.memory_system:
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
                    "content_description": "录屏已完成，详细画面分析进行中。",
                    "timeline_text": f"+0.00s: recording saved ({base_name})",
                    "frame_details_json": "[]",
                    "suggestions": "等待几秒后再问我“什么时候看到什么”，我会基于时间线回答。",
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

            if not self.memory_system:
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
            suggestions.append("你刚刚遇到错误信息，建议先记录报错关键词并优先排查权限/依赖问题。")

        if any(k in merged_text for k in ["todo", "deadline", "meeting", "plan", "task"]):
            suggestions.append("检测到任务/日程相关内容，建议把关键事项整理成待办并设置提醒。")

        if any(k in merged_text for k in ["code", "terminal", "vscode", "python", "git"]):
            suggestions.append("检测到开发工作流，建议记录本次改动要点并及时提交代码。")

        if not suggestions:
            suggestions.append("建议按时间线回顾关键画面，确认下一步要执行的操作。")

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
            "coding": ["vscode", "xcode", "pycharm", "intellij", "source code", "代码", "编程"],
            "terminal": ["terminal", "shell", "bash", "zsh", "powershell", "命令行"],
            "debugging": ["error", "exception", "traceback", "failed", "warning", "报错", "异常", "失败"],
            "meeting": ["zoom", "teams", "meeting", "会议", "腾讯会议", "飞书会议", "google meet"],
            "browser": ["chrome", "safari", "firefox", "edge", "browser", "网页", "浏览器"],
            "research": ["paper", "arxiv", "abstract", "reference", "论文", "文献", "研究"],
            "document": ["doc", "document", "pdf", "notion", "word", "文档", "笔记"],
            "spreadsheet": ["excel", "spreadsheet", "sheet", "表格"],
            "chat": ["slack", "discord", "wechat", "telegram", "chat", "message", "消息", "聊天"],
            "design": ["figma", "sketch", "photoshop", "design", "ui", "画板", "设计"],
            "presentation": ["ppt", "slides", "keynote", "演示", "汇报"],
            "dashboard": ["dashboard", "grafana", "datadog", "analytics", "统计", "看板"],
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
                    frame_text = self._extract_text_from_frame(
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

    def _get_easyocr_reader(self):
        """Lazy-init easyocr reader for local OCR fallback."""
        if self._easyocr_reader is not None:
            return self._easyocr_reader
        try:
            import easyocr  # type: ignore

            self._easyocr_reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
            return self._easyocr_reader
        except Exception as e:
            print(f"[RecordingPresenter] easyocr unavailable: {e}")
            self._easyocr_reader = False
            return None

    def _extract_text_with_easyocr(self, frame) -> str:
        """Extract meaningful text using easyocr as a robust local fallback."""
        try:
            cv2 = get_cv2()
            if cv2 is None:
                return ""

            reader = self._get_easyocr_reader()
            if not reader:
                return ""

            h, w = frame.shape[:2]
            img = frame
            if w > 1600:
                new_w = 1600
                new_h = int(h * (new_w / w))
                img = cv2.resize(frame, (new_w, new_h))

            try:
                results = reader.readtext(img, detail=0, paragraph=True)
            except Exception:
                results = []

            clean_items = []
            for item in results:
                text = " ".join(str(item).split())
                if len(text) >= 5:
                    clean_items.append(text)
                if len(clean_items) >= 6:
                    break

            if not clean_items:
                return ""
            return " | ".join(clean_items)
        except Exception as e:
            print(f"[RecordingPresenter] easyocr fallback failed: {e}")
            return ""

    def _extract_text_from_frame(self, frame, use_vision: bool = True):
        """Extract text and understand scene context from frame"""
        try:
            cv2 = get_cv2()
            if cv2 is None:
                return "Screen captured (analysis unavailable: cv2 not available)"

            if use_vision:
                import requests
                import base64

                # Encode frame to base64
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                img_str = base64.b64encode(buffer).decode('utf-8')

                # Keep prompt/response compact for faster timeline availability.
                prompt = (
                    "Describe this screenshot briefly for memory timeline.\n"
                    "Return one line with: App, Key text, Main action."
                )

                response = requests.post(
                    "http://127.0.0.1:11434/api/generate",
                    json={
                        "model": "qwen2.5vl:3b",
                        "prompt": prompt,
                        "images": [img_str],
                        "stream": False,
                        "options": {
                            "num_predict": 160,
                            "temperature": 0.2,
                            "top_p": 0.8,
                        }
                    },
                    timeout=6,
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result.get("response", "").strip()
                    if content and content.lower() not in ["no text", "none", "no text found"]:
                        return content

        except Exception as e:
            if "timed out" in str(e).lower():
                print("[Recording] Vision API timeout (6s), using fallback")
            else:
                print(f"[Recording] Vision API error: {e}")

        # Local OCR fallback (more informative than heuristic density-only fallback).
        ocr_text = self._extract_text_with_easyocr(frame)
        if ocr_text:
            return f"OCR detected: {ocr_text}"

        # Enhanced fallback analysis
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Analyze image characteristics
            text_density = np.sum(gray > 200) / gray.size
            brightness = np.mean(gray)

            # Determine content type
            if brightness > 200:
                lighting = "light theme"
            elif brightness < 80:
                lighting = "dark theme"
            else:
                lighting = "mixed theme"

            if text_density > 0.4:
                content = "text-heavy content (code, document, or terminal)"
            elif text_density > 0.2:
                content = "mixed content (text and graphics)"
            else:
                content = "graphical content (images, video, or design)"

            return f"Screen capture showing {content} with {lighting}"

        except Exception as e:
            return f"Screen captured (analysis unavailable: {str(e)[:30]})"

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
