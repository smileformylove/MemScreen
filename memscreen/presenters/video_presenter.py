### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""Presenter for Video Playback functionality (MVP Pattern)"""

import os
import sqlite3
import threading
import json
import hashlib
import shutil
import subprocess
from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    import cv2

from .base_presenter import BasePresenter


class VideoInfo:
    """Information about a video recording"""

    def __init__(self, filename: str, timestamp: str, frame_count: int, fps: float,
                 duration: float, file_size: int, recording_mode: str = "fullscreen",
                 window_title: Optional[str] = None, audio_source: Optional[str] = None,
                 content_tags: Optional[List[str]] = None, content_summary: Optional[str] = None):
        self.filename = filename
        self.timestamp = timestamp
        self.frame_count = frame_count
        self.fps = fps
        self.duration = duration
        self.file_size = file_size
        self.recording_mode = recording_mode or "fullscreen"
        self.window_title = window_title
        self.audio_source = audio_source
        self.content_tags = content_tags or []
        self.content_summary = content_summary

    def to_dict(self) -> Dict[str, Any]:
        app_name = self._extract_app_name()
        tags = self._build_tags(app_name)
        return {
            "filename": self.filename,
            "timestamp": self.timestamp,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "duration": self.duration,
            "file_size": self.file_size,
            "recording_mode": self.recording_mode,
            "window_title": self.window_title,
            "audio_source": self.audio_source,
            "app_name": app_name,
            "tags": tags,
            "content_tags": self.content_tags,
            "content_summary": self.content_summary,
        }

    def _extract_app_name(self) -> str:
        title = (self.window_title or "").strip()
        if not title:
            if self.recording_mode == "fullscreen-single":
                return "single-screen"
            if self.recording_mode == "region":
                return "region-capture"
            return "all-screens"
        if title.startswith("Window: "):
            body = title[len("Window: "):]
            sep = body.find(" · ")
            return body[:sep].strip() if sep > 0 else body.strip()
        sep = title.find(" · ")
        return title[:sep].strip() if sep > 0 else title

    def _build_tags(self, app_name: str) -> List[str]:
        tags: List[str] = []

        # Mode
        mode_map = {
            "fullscreen": "mode:full",
            "fullscreen-single": "mode:single-screen",
            "region": "mode:region-window",
        }
        tags.append(mode_map.get(self.recording_mode, "mode:unknown"))

        # App/source
        tags.append(f"app:{app_name.lower()}")

        # Purpose heuristic
        lower = f"{app_name} {(self.window_title or '')}".lower()
        if any(x in lower for x in ["zoom", "teams", "meeting", "feishu"]):
            tags.append("purpose:meeting")
        if any(x in lower for x in ["code", "vscode", "xcode", "pycharm", "terminal", "intellij"]):
            tags.append("purpose:coding")
        if any(x in lower for x in ["chrome", "safari", "firefox", "edge", "browser"]):
            tags.append("purpose:research")
        if any(x in lower for x in ["figma", "sketch", "photoshop", "design"]):
            tags.append("purpose:design")
        if any(x in lower for x in ["slack", "discord", "wechat", "dingtalk", "telegram"]):
            tags.append("purpose:communication")

        # Content-centric tags from vision/OCR enrichment (high priority).
        for tag in self.content_tags:
            clean = str(tag).strip().lower()
            if not clean:
                continue
            if clean.startswith("topic:"):
                tags.append(clean)
            else:
                tags.append(f"topic:{clean}")

        # Duration bucket
        duration = float(self.duration or 0.0)
        if duration < 30:
            tags.append("length:short")
        elif duration < 180:
            tags.append("length:medium")
        else:
            tags.append("length:long")

        # Time bucket + weekday from timestamp
        hour = None
        weekday = None
        try:
            dt = datetime.strptime(self.timestamp, "%Y-%m-%d %H:%M:%S")
            hour = dt.hour
            weekday = dt.strftime("%a").lower()
        except Exception:
            pass
        if weekday:
            tags.append(f"weekday:{weekday}")
        if hour is not None:
            if 6 <= hour < 12:
                tags.append("time:morning")
            elif 12 <= hour < 18:
                tags.append("time:afternoon")
            elif 18 <= hour < 24:
                tags.append("time:evening")
            else:
                tags.append("time:night")

        # Audio
        if self.audio_source:
            tags.append(f"audio:{self.audio_source}")
        else:
            tags.append("audio:none")

        # Dedupe but keep order
        seen = set()
        out: List[str] = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                out.append(tag)
        return out


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

            try:
                cursor.execute('''
                    SELECT filename, timestamp, frame_count, fps, duration, file_size,
                           recording_mode, window_title, audio_source, content_tags, content_summary
                    FROM recordings
                    ORDER BY timestamp DESC
                ''')
            except sqlite3.OperationalError:
                # Backward compatibility for older DB schema.
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
                        file_size=row[5] or 0,
                        recording_mode=row[6] if len(row) > 6 else "fullscreen",
                        window_title=row[7] if len(row) > 7 else None,
                        audio_source=row[8] if len(row) > 8 else None,
                        content_tags=self._parse_content_tags(row[9] if len(row) > 9 else None),
                        content_summary=row[10] if len(row) > 10 else None,
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

    def resolve_playable_path(self, filename: str) -> str:
        """
        Return a local path that is playable by AVFoundation/video_player.

        On macOS, `video_player` (AVFoundation backend) has poor support for
        MKV/AVI containers. For those formats we lazily transcode once to an
        MP4 cache file and reuse it for subsequent playback.
        """
        source = str(filename or "").strip()
        if not source:
            raise ValueError("filename is required")
        if not os.path.exists(source):
            raise FileNotFoundError(f"Video file not found: {source}")

        ext = os.path.splitext(source)[1].lower()
        if ext not in {".mkv", ".avi"}:
            return source

        ffmpeg_bin = self._resolve_ffmpeg_binary()
        if not ffmpeg_bin:
            print("[VideoPresenter] ffmpeg not found; fallback to original file for playback.")
            return source

        source_abs = os.path.abspath(source)
        source_stat = os.stat(source_abs)
        key_raw = f"{source_abs}|{int(source_stat.st_mtime_ns)}|{int(source_stat.st_size)}"
        cache_key = hashlib.sha1(key_raw.encode("utf-8", "ignore")).hexdigest()[:16]

        source_dir = os.path.dirname(source_abs)
        source_name = os.path.splitext(os.path.basename(source_abs))[0]
        cache_dir = os.path.join(source_dir, ".playable_cache")
        os.makedirs(cache_dir, exist_ok=True)
        playable_path = os.path.join(cache_dir, f"{source_name}_{cache_key}.mp4")
        tmp_path = os.path.join(cache_dir, f"{source_name}_{cache_key}.tmp.mp4")

        if os.path.exists(playable_path) and os.path.getsize(playable_path) > 0:
            return playable_path

        for stale in (tmp_path, playable_path):
            try:
                if os.path.exists(stale):
                    os.remove(stale)
            except Exception:
                pass

        transcode_cmd = [
            ffmpeg_bin,
            "-y",
            "-i",
            source_abs,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            tmp_path,
        ]
        copy_video_cmd = [
            ffmpeg_bin,
            "-y",
            "-i",
            source_abs,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            tmp_path,
        ]

        for cmd in (transcode_cmd, copy_video_cmd):
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                    os.replace(tmp_path, playable_path)
                    print(
                        "[VideoPresenter] Generated playable cache for "
                        f"{os.path.basename(source_abs)} -> {os.path.basename(playable_path)}"
                    )
                    return playable_path
            except Exception as e:
                stderr = ""
                if hasattr(e, "stderr") and e.stderr:
                    stderr = str(e.stderr).strip().splitlines()[-1]
                print(f"[VideoPresenter] playable transcode failed: {e} {stderr}")
            finally:
                try:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except Exception:
                    pass

        return source

    # ==================== Private Methods ====================

    def _init_database(self):
        """Initialize database connection"""
        # Database is created by RecordingPresenter
        # Just verify it exists
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")

    def _parse_content_tags(self, raw: Any) -> List[str]:
        """Parse serialized content tags from DB."""
        if raw is None:
            return []
        if isinstance(raw, list):
            return [str(x).strip().lower() for x in raw if str(x).strip()]
        raw_text = str(raw).strip()
        if not raw_text:
            return []
        try:
            arr = json.loads(raw_text)
            if isinstance(arr, list):
                return [str(x).strip().lower() for x in arr if str(x).strip()]
        except Exception:
            pass
        # Fallback: CSV text
        out = []
        for part in raw_text.split(","):
            p = part.strip().lower()
            if p:
                out.append(p)
        return out

    def _resolve_ffmpeg_binary(self) -> Optional[str]:
        """
        Resolve ffmpeg binary for packaged/runtime environments.
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

    def _get_video_info(self, filename: str) -> Optional[VideoInfo]:
        """Get video info from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            try:
                cursor.execute('''
                    SELECT filename, timestamp, frame_count, fps, duration, file_size,
                           recording_mode, window_title, audio_source, content_tags, content_summary
                    FROM recordings
                    WHERE filename = ?
                ''', (filename,))
            except sqlite3.OperationalError:
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
                    file_size=row[5] or 0,
                    recording_mode=row[6] if len(row) > 6 else "fullscreen",
                    window_title=row[7] if len(row) > 7 else None,
                    audio_source=row[8] if len(row) > 8 else None,
                    content_tags=self._parse_content_tags(row[9] if len(row) > 9 else None),
                    content_summary=row[10] if len(row) > 10 else None,
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
