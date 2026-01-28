### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Presenter for Screen Recording functionality (MVP Pattern)"""

import os
import time
import threading
import sqlite3
import cv2
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any

from .base_presenter import BasePresenter


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

    def __init__(self, view=None, memory_system=None, db_path="./db/screen_capture.db"):
        """
        Initialize recording presenter.

        Args:
            view: RecordingTab view instance
            memory_system: Memory system for storing recordings
            db_path: Path to SQLite database
        """
        super().__init__(view, memory_system)
        self.db_path = db_path
        self.memory_system = memory_system

        # Recording state
        self.is_recording = False
        self.recording_thread = None
        self.recording_frames = []
        self.recording_start_time = None

        # Recording settings (with defaults)
        self.duration = 60  # seconds per segment
        self.interval = 2.0  # seconds between screenshots
        self.output_dir = "./db/videos"

        # Statistics
        self.frame_count = 0
        self.current_file = None

        self._is_initialized = False

    def initialize(self):
        """Initialize presenter and create output directory"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)

            # Initialize database
            self._init_database()

            self._is_initialized = True
            print("[RecordingPresenter] Initialized successfully")
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

        self._is_initialized = False

    def _init_database(self):
        """Initialize SQLite database for recording metadata"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recordings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    frame_count INTEGER,
                    fps REAL,
                    duration REAL,
                    file_size INTEGER
                )
            ''')

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

        try:
            self.duration = duration
            self.interval = interval
            self.is_recording = True
            self.recording_frames = []
            self.recording_start_time = time.time()
            self.frame_count = 0

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

            # Wait for recording thread to finish
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=10)

            # Save the recording
            if self.recording_frames:
                # Save in background thread
                save_thread = threading.Thread(
                    target=self._save_recording,
                    args=(self.recording_frames,),
                    daemon=True
                )
                save_thread.start()

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

    def get_preview_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame for preview.

        Returns:
            numpy array of the frame or None if capture failed
        """
        try:
            from PIL import ImageGrab

            # Capture screen
            screenshot = ImageGrab.grab()
            # Convert to numpy array and ensure proper format
            frame_array = np.array(screenshot)
            # Ensure uint8 format
            if frame_array.dtype != np.uint8:
                frame_array = frame_array.astype(np.uint8)
            # Convert RGB to BGR
            frame = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)

            return frame

        except Exception as e:
            self.handle_error(e, "Failed to capture preview frame")
            return None

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

    # ==================== Private Methods ====================

    def _record_screen(self):
        """
        Record screen in background thread.
        This method runs in a separate thread.
        """
        last_screenshot_time = time.time()
        last_save_time = time.time()

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
                        # Capture screen
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

                    except Exception as e:
                        print(f"[Recording] Error capturing frame: {e}")
                        import traceback
                        traceback.print_exc()
                        # Continue recording even if one frame fails

                    # Update view with frame count
                    if self.view and self.frame_count % 10 == 0:
                        self.view.on_frame_captured(self.frame_count, elapsed)

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

            print(f"[RecordingPresenter] Saved segment: {filename}")

        except Exception as e:
            self.handle_error(e, "Failed to save video segment")

    def _save_recording(self, frames):
        """
        Save final recording when user stops recording.

        Args:
            frames: List of video frames
        """
        try:
            if not frames:
                self.show_info("No frames to save")
                return

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.output_dir, f"recording_{timestamp}.mp4")

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

            # Notify view
            if self.view:
                self.view.on_recording_saved(filename, file_size)

            print(f"[RecordingPresenter] Saved recording: {filename}")

        except Exception as e:
            self.handle_error(e, "Failed to save recording")

    def _save_to_database(self, filename, frame_count, fps, duration, file_size):
        """Save recording metadata to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute('''
                INSERT INTO recordings (filename, timestamp, frame_count, fps, duration, file_size)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (filename, timestamp, frame_count, fps, duration, file_size))

            conn.commit()
            conn.close()

        except Exception as e:
            self.handle_error(e, "Failed to save to database")

    def _add_video_to_memory(self, filename, frame_count, fps):
        """Add video recording to memory system"""
        try:
            if not self.memory_system:
                return

            # Analyze video content
            content_description = self._analyze_video_content(filename, frame_count)

            # Create memory entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            duration = frame_count / fps if fps > 0 else 0

            memory_text = f"""Screen Recording captured at {timestamp}:
- Duration: {duration:.1f} seconds
- Frames: {frame_count}
- File: {filename}

Content Summary:
{content_description}

This video screen recording shows what was displayed on screen during the recording period.
When users ask about what was on their screen or what they were doing, reference this recording."""

            # Add to memory
            result = self.memory_system.add(
                [{"role": "user", "content": memory_text}],
                user_id="screenshot",
                metadata={
                    "type": "screen_recording",
                    "filename": filename,
                    "frame_count": frame_count,
                    "fps": fps,
                    "duration": duration,
                    "timestamp": timestamp,
                    "content_description": content_description
                },
                infer=False
            )

            print(f"[RecordingPresenter] Added to memory: {filename}")

        except Exception as e:
            self.handle_error(e, "Failed to add video to memory")

    def _analyze_video_content(self, filename, total_frames):
        """Analyze video content by sampling frames and using OCR"""
        try:
            # Sample frames
            num_samples = min(5, total_frames)
            sample_indices = [int(i * total_frames / num_samples) for i in range(num_samples)]

            all_text_found = []
            cap = cv2.VideoCapture(filename)

            for idx, frame_idx in enumerate(sample_indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    frame_text = self._extract_text_from_frame(frame)
                    if frame_text:
                        all_text_found.append(frame_text)

            cap.release()

            # Combine all found text
            combined_text = " | ".join(all_text_found) if all_text_found else "Screen recording captured (no clear text detected)"
            return combined_text

        except Exception as e:
            self.handle_error(e, "Failed to analyze video content")
            return "Screen recording (content analysis unavailable)"

    def _extract_text_from_frame(self, frame):
        """Extract text from a single frame using OCR - OPTIMIZED for speed"""
        try:
            import requests
            import base64

            # Encode frame to base64
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            img_str = base64.b64encode(buffer).decode('utf-8')

            # Send to Ollama vision API - OPTIMIZED with faster model
            response = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": "qwen3:1.7b",  # OPTIMIZED: 2x faster than qwen2.5vl:3b
                    "prompt": "Extract and list all visible text from this image. Return only the text, nothing else.",
                    "images": [img_str],
                    "stream": False,
                    "options": {
                        "num_predict": 256,  # OPTIMIZED: Limit output length for speed
                        "temperature": 0.3,    # OPTIMIZED: Faster convergence
                        "top_p": 0.8,           # OPTIMIZED: Faster sampling
                    }
                },
                timeout=30  # OPTIMIZED: Reduced from 60s to 30s
            )

            if response.status_code == 200:
                result = response.json()
                text = result.get("response", "").strip()
                if text and text.lower() not in ["no text", "none", "no text found", "no text in image"]:
                    return f"Detected text on screen: {text}"

        except requests.exceptions.Timeout:
            print("[DEBUG] Ollama vision API timed out")
        except Exception as e:
            print(f"[DEBUG] OCR failed: {e}")

        # Fallback to basic analysis
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            text_density = np.sum(gray > 200) / gray.size

            if text_density > 0.3:
                return "Screen contains light colored content (possibly text or UI elements)"
            else:
                return "Screen captured (dark or graphical content)"
        except:
            return "Screen content captured (text extraction failed)"

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
