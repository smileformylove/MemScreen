### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""Presenter for Video Playback functionality (MVP Pattern)"""

import os
import sqlite3
import threading
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    import cv2

from kivy.clock import Clock
from .base_presenter import BasePresenter


class VideoInfo:
    """Information about a video recording"""

    def __init__(self, filename: str, timestamp: str, frame_count: int, fps: float,
                 duration: float, file_size: int):
        self.filename = filename
        self.timestamp = timestamp
        self.frame_count = frame_count
        self.fps = fps
        self.duration = duration
        self.file_size = file_size

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "timestamp": self.timestamp,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "duration": self.duration,
            "file_size": self.file_size
        }


class VideoPresenter(BasePresenter):
    """
    Presenter for Video Playback functionality.

    Responsibilities:
    - Load and manage video list
    - Play/pause/stop video playback
    - Seek to specific frame
    - Delete videos
    - Update playback statistics

    View (VideoTab) responsibilities:
    - Display video list
    - Show video canvas
    - Display playback controls
    - Show video info
    """

    def __init__(self, view=None, db_path: str = "./db/screen_capture.db"):
        """
        Initialize video presenter.

        Args:
            view: VideoTab view instance
            db_path: Path to SQLite database
        """
        super().__init__(view)
        self.db_path = db_path

        # Video playback state
        self.current_video: Optional[VideoInfo] = None
        self.video_capture: Optional[cv2.VideoCapture] = None
        self.is_playing = False
        self.current_frame_number = 0
        self.total_frames = 0
        self.fps = 30.0

        # Playback thread
        self.playback_thread: Optional[threading.Thread] = None
        self.stop_playback_flag = False

        # Thread lock for video capture access
        self._capture_lock = threading.Lock()

        self._is_initialized = False

    def initialize(self):
        """Initialize presenter"""
        try:
            self._init_database()
            self._is_initialized = True
            print("[VideoPresenter] Initialized successfully")
        except Exception as e:
            self.handle_error(e, "Failed to initialize VideoPresenter")
            raise

    def cleanup(self):
        """Clean up resources"""
        self.stop_playback()

        with self._capture_lock:
            if self.video_capture:
                self.video_capture.release()
                self.video_capture = None

        self._is_initialized = False

    # ==================== Public API for View ====================

    def get_video_list(self) -> List[VideoInfo]:
        """
        Get list of all videos.

        Returns:
            List of VideoInfo objects
        """
        try:
            print(f"[VideoPresenter] 📋 Loading video list from database: {self.db_path}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT filename, timestamp, frame_count, fps, duration, file_size
                FROM recordings
                ORDER BY timestamp DESC
            ''')

            all_rows = cursor.fetchall()
            print(f"[VideoPresenter] 📊 Found {len(all_rows)} total records in database")

            videos = []
            for row in all_rows:
                filename = row[0]
                # Only include videos that actually exist
                if os.path.exists(filename):
                    video = VideoInfo(
                        filename=filename,
                        timestamp=row[1],
                        frame_count=row[2],
                        fps=row[3] or 30.0,
                        duration=row[4] or 0.0,
                        file_size=row[5] or 0
                    )
                    videos.append(video)
                    print(f"[VideoPresenter] ✅ Video exists: {os.path.basename(filename)}")
                else:
                    # Clean up database records for deleted files
                    print(f"[VideoPresenter] 🗑️ Cleaning up database record for missing file: {filename}")
                    cursor.execute('DELETE FROM recordings WHERE filename = ?', (filename,))
                    conn.commit()

            conn.close()
            print(f"[VideoPresenter] 📤 Returning {len(videos)} valid videos")
            return videos

        except Exception as e:
            print(f"[VideoPresenter] ❌ ERROR getting video list: {e}")
            import traceback
            traceback.print_exc()
            self.handle_error(e, "Failed to get video list")
            return []

    def delete_video(self, filename: str) -> bool:
        """
        Delete a video from database.

        Args:
            filename: Path to video file

        Returns:
            True if deleted successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM recordings WHERE filename = ?', (filename,))
            conn.commit()

            deleted = cursor.rowcount > 0
            conn.close()

            if deleted:
                print(f"[VideoPresenter] Deleted video record from database: {filename}")

            return deleted

        except Exception as e:
            self.handle_error(e, "Failed to delete video from database")
            return False

    def load_video(self, filename: str) -> bool:
        """
        Load a video for playback.

        Args:
            filename: Path to video file

        Returns:
            True if video loaded successfully
        """
        try:
            import cv2  # Lazy import to avoid PyInstaller recursion
            print(f"[VideoPresenter] load_video called: {filename}")
            # Stop current playback
            self.stop_playback()

            with self._capture_lock:
                # Release old capture if exists
                if self.video_capture:
                    self.video_capture.release()
                    self.video_capture = None

                # Check if file exists
                if not os.path.exists(filename):
                    self.show_error(f"Video file not found: {filename}")
                    return False

                # Open video capture
                self.video_capture = cv2.VideoCapture(filename)

                if not self.video_capture.isOpened():
                    self.show_error("Failed to open video file")
                    self.video_capture = None
                    return False

                # Get video properties
                self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
                self.fps = self.video_capture.get(cv2.CAP_PROP_FPS) or 30.0
                self.current_frame_number = 0

            print(f"[VideoPresenter] Video loaded: {self.total_frames} frames at {self.fps} FPS")

            # Get video info from database
            video_info = self._get_video_info(filename)
            if video_info:
                self.current_video = video_info

            # Notify view
            if self.view:
                self.view.on_video_loaded(filename, self.total_frames, self.fps)

            return True

        except Exception as e:
            print(f"[VideoPresenter] Error loading video: {e}")
            import traceback
            traceback.print_exc()
            self.handle_error(e, f"Failed to load video: {filename}")
            return False

    def play_video(self) -> bool:
        """
        Start or resume video playback.

        Returns:
            True if playback started
        """
        import cv2  # Lazy import to avoid PyInstaller recursion
        print(f"[VideoPresenter] play_video called, is_playing={self.is_playing}")
        if not self.video_capture:
            print("[VideoPresenter] Error: No video loaded")
            self.show_error("No video loaded")
            return False

        if self.is_playing:
            print("[VideoPresenter] Already playing")
            return True  # Already playing

        try:
            # Reset to beginning if at end
            with self._capture_lock:
                if self.current_frame_number >= self.total_frames - 1:
                    print(f"[VideoPresenter] Resetting to beginning (was at frame {self.current_frame_number})")
                    self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.current_frame_number = 0

            self.is_playing = True
            self.stop_playback_flag = False

            print(f"[VideoPresenter] Starting playback thread...")
            # Start playback thread
            self.playback_thread = threading.Thread(
                target=self._playback_loop,
                daemon=True
            )
            self.playback_thread.start()

            # Don't notify view here - will be done via Clock in Kivy thread
            print(f"[VideoPresenter] Playback started successfully")
            return True

        except Exception as e:
            print(f"[VideoPresenter] Error starting playback: {e}")
            import traceback
            traceback.print_exc()
            self.handle_error(e, "Failed to start playback")
            self.is_playing = False
            return False

    def pause_video(self) -> bool:
        """
        Pause video playback.

        Returns:
            True if paused successfully
        """
        if not self.is_playing:
            return False

        self.is_playing = False

        if self.view:
            self.view.on_playback_paused()

        return True

    def stop_video(self) -> bool:
        """
        Alias for stop_playback for compatibility with UI.

        Returns:
            True if stopped successfully
        """
        return self.stop_playback()

    def stop_playback(self) -> bool:
        """
        Stop video playback and reset to beginning.

        Returns:
            True if stopped successfully
        """
        import cv2  # Lazy import to avoid PyInstaller recursion
        self.is_playing = False
        self.stop_playback_flag = True

        # Wait for playback thread to finish
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=2)

        # Reset to beginning
        with self._capture_lock:
            if self.video_capture:
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.current_frame_number = 0

        if self.view:
            # Use on_playback_finished if on_playback_stopped doesn't exist
            if hasattr(self.view, 'on_playback_stopped'):
                self.view.on_playback_stopped()
            elif hasattr(self.view, 'on_playback_finished'):
                self.view.on_playback_finished()

        return True

    def seek_to_frame(self, frame_number: int) -> bool:
        """Seek to specific frame and display it"""
        import cv2  # Lazy import to avoid PyInstaller recursion
        if not self.video_capture:
            return False

        try:
            frame_number = max(0, min(frame_number, self.total_frames - 1))

            with self._capture_lock:
                # Set position
                self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                self.current_frame_number = frame_number

                # Read the frame
                ret, frame = self.video_capture.read()

                if ret and frame is not None:
                    # Display the frame via callback
                    if self.view:
                        self.view.on_frame_changed(frame, frame_number)
                    # Reset position for next read
                    self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

            return True

        except Exception as e:
            self.handle_error(e, "Failed to seek video")
            return False

    def delete_video(self, filename: str) -> bool:
        """
        Delete a video file and database entry.

        Args:
            filename: Path to video file

        Returns:
            True if deleted successfully
        """
        try:
            # Stop playback if this video is playing
            if self.current_video and self.current_video.filename == filename:
                self.stop_playback()
                with self._capture_lock:
                    if self.video_capture:
                        self.video_capture.release()
                        self.video_capture = None
                self.current_video = None

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
                self.view.on_video_deleted(filename)

            return True

        except Exception as e:
            self.handle_error(e, f"Failed to delete video: {filename}")
            return False

    def get_video_info(self, filename: str) -> Optional[VideoInfo]:
        """
        Get information about a video.

        Args:
            filename: Path to video file

        Returns:
            VideoInfo object or None
        """
        return self._get_video_info(filename)

    # ==================== Private Methods ====================

    def _init_database(self):
        """Initialize database connection"""
        # Database is created by RecordingPresenter
        # Just verify it exists
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")

    def _get_video_info(self, filename: str) -> Optional[VideoInfo]:
        """Get video info from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT filename, timestamp, frame_count, fps, duration, file_size
                FROM recordings
                WHERE filename = ?
            ''', (filename,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return VideoInfo(
                    filename=row[0],
                    timestamp=row[1],
                    frame_count=row[2],
                    fps=row[3] or 30.0,
                    duration=row[4] or 0.0,
                    file_size=row[5] or 0
                )

            return None

        except Exception as e:
            print(f"[VideoPresenter] Failed to get video info: {e}")
            return None

    def _playback_loop(self):
        """Video playback loop (runs in background thread)"""
        reached_end = False
        try:
            while self.is_playing and not self.stop_playback_flag:
                # Check if we've reached the end
                if self.current_frame_number >= self.total_frames:
                    print(f"[VideoPresenter] End of video reached (frame {self.current_frame_number}/{self.total_frames})")
                    reached_end = True
                    break

                # Read next frame with lock
                with self._capture_lock:
                    if not self.video_capture or not self.video_capture.isOpened():
                        print("[VideoPresenter] Video capture not available")
                        break

                    ret, frame = self.video_capture.read()

                    if not ret or frame is None:
                        print("[VideoPresenter] Failed to read frame")
                        break

                self.current_frame_number += 1

                # Notify view with new frame (outside lock to avoid deadlock)
                try:
                    if self.view:
                        self.view.on_playback_frame(frame, self.current_frame_number)
                except Exception as view_err:
                    print(f"[VideoPresenter] Error notifying view: {view_err}")
                    break

                # Control playback speed
                delay = int(1000 / self.fps)
                threading.Event().wait(delay / 1000.0)

        except Exception as e:
            print(f"[VideoPresenter] Playback error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.is_playing = False

            # Only notify playback finished if we reached the end naturally
            # Don't call it if user paused (is_playing was set to False externally)
            if reached_end and self.view:
                try:
                    self.view.on_playback_finished()
                except Exception as e:
                    print(f"[VideoPresenter] Error notifying playback finished: {e}")
