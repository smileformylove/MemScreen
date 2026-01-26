### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Presenter for Video Playback functionality (MVP Pattern)"""

import os
import sqlite3
import cv2
import threading
from typing import Optional, List, Dict, Any

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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT filename, timestamp, frame_count, fps, duration, file_size
                FROM recordings
                ORDER BY timestamp DESC
            ''')

            videos = []
            for row in cursor.fetchall():
                video = VideoInfo(
                    filename=row[0],
                    timestamp=row[1],
                    frame_count=row[2],
                    fps=row[3] or 30.0,
                    duration=row[4] or 0.0,
                    file_size=row[5] or 0
                )
                videos.append(video)

            conn.close()
            return videos

        except Exception as e:
            self.handle_error(e, "Failed to get video list")
            return []

    def load_video(self, filename: str) -> bool:
        """
        Load a video for playback.

        Args:
            filename: Path to video file

        Returns:
            True if video loaded successfully
        """
        try:
            # Stop current playback
            self.stop_playback()

            # Check if file exists
            if not os.path.exists(filename):
                self.show_error(f"Video file not found: {filename}")
                return False

            # Open video capture
            self.video_capture = cv2.VideoCapture(filename)

            if not self.video_capture.isOpened():
                self.show_error("Failed to open video file")
                return False

            # Get video properties
            self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS) or 30.0
            self.current_frame_number = 0

            # Get video info from database
            video_info = self._get_video_info(filename)
            if video_info:
                self.current_video = video_info

            # Notify view
            if self.view:
                self.view.on_video_loaded(filename, self.total_frames, self.fps)

            return True

        except Exception as e:
            self.handle_error(e, f"Failed to load video: {filename}")
            return False

    def play_video(self) -> bool:
        """
        Start or resume video playback.

        Returns:
            True if playback started
        """
        if not self.video_capture:
            self.show_error("No video loaded")
            return False

        if self.is_playing:
            return True  # Already playing

        try:
            self.is_playing = True
            self.stop_playback_flag = False

            # Start playback thread
            self.playback_thread = threading.Thread(
                target=self._playback_loop,
                daemon=True
            )
            self.playback_thread.start()

            # Notify view
            if self.view:
                self.view.on_playback_started()

            return True

        except Exception as e:
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

    def stop_playback(self) -> bool:
        """
        Stop video playback and reset to beginning.

        Returns:
            True if stopped successfully
        """
        self.is_playing = False
        self.stop_playback_flag = True

        # Wait for playback thread to finish
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=2)

        # Reset to beginning
        if self.video_capture:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame_number = 0

        if self.view:
            self.view.on_playback_stopped()

        return True

    def seek_to_frame(self, frame_number: int) -> bool:
        """
        Seek to specific frame.

        Args:
            frame_number: Frame number to seek to

        Returns:
            True if seek successful
        """
        if not self.video_capture:
            return False

        try:
            # Clamp frame number
            frame_number = max(0, min(frame_number, self.total_frames - 1))

            # Set position
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame_number = frame_number

            # Get and display frame
            ret, frame = self.video_capture.read()
            if ret:
                if self.view:
                    self.view.on_frame_changed(frame, frame_number)

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
        try:
            while self.is_playing and not self.stop_playback_flag:
                if self.current_frame_number >= self.total_frames:
                    # End of video
                    break

                # Read next frame
                ret, frame = self.video_capture.read()

                if not ret:
                    break

                self.current_frame_number += 1

                # Notify view with new frame
                if self.view:
                    self.view.on_playback_frame(frame, self.current_frame_number)

                # Control playback speed
                delay = int(1000 / self.fps)
                threading.Event().wait(delay / 1000.0)

        except Exception as e:
            print(f"[VideoPresenter] Playback error: {e}")

        finally:
            self.is_playing = False

            # Notify view of playback completion
            if self.view:
                self.view.on_playback_finished()
