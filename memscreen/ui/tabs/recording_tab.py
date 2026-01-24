### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Recording tab for screen capture functionality"""

import os
import time
import threading
import sqlite3
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from PIL import Image, ImageTk, ImageGrab

from .base_tab import BaseTab
from ..components.colors import COLORS, FONTS


class RecordingTab(BaseTab):
    """Screen recording tab"""

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.recording_output_dir = "./db/videos"
        self.duration_var = None
        self.interval_var = None
        self.output_var = None
        self.record_btn = None
        self.recording_status_label = None
        self.recording_info_label = None
        self.preview_canvas = None
        self.preview_image = None

    def create_ui(self):
        """Create recording tab UI"""
        self.frame = tk.Frame(self.parent, bg=COLORS["bg"])

        # Header
        header_frame = tk.Frame(self.frame, bg=COLORS["surface"], height=80)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="🔴 Screen Recording",
            font=FONTS["heading"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(side=tk.LEFT, padx=30, pady=20)

        # Recording status
        self.recording_status_label = tk.Label(
            header_frame,
            text="● Ready to record",
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text_light"]
        )
        self.recording_status_label.pack(side=tk.RIGHT, padx=30, pady=20)

        # Settings section
        self._create_settings_section()

        # Control buttons
        self._create_control_buttons()

        # Preview area
        self._create_preview_area()

        # Recording info
        info_frame = tk.Frame(self.frame, bg=COLORS["surface"])
        info_frame.pack(fill=tk.X)

        self.recording_info_label = tk.Label(
            info_frame,
            text="",
            font=FONTS["small"],
            bg=COLORS["surface"],
            fg=COLORS["text_light"]
        )
        self.recording_info_label.pack(pady=10)

        # Start preview update
        self.update_preview()

    def _create_settings_section(self):
        """Create recording settings section"""
        settings_frame = tk.Frame(self.frame, bg=COLORS["surface"])
        settings_frame.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            settings_frame,
            text="Recording Settings",
            font=FONTS["heading"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(anchor=tk.W, padx=20, pady=(20, 15))

        # Duration setting
        duration_frame = tk.Frame(settings_frame, bg=COLORS["surface"])
        duration_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(
            duration_frame,
            text="Duration (seconds):",
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.duration_var = tk.StringVar(value="60")
        duration_entry = tk.Entry(
            duration_frame,
            textvariable=self.duration_var,
            font=FONTS["body"],
            bg=COLORS["bg"],
            relief=tk.FLAT,
            width=10
        )
        duration_entry.pack(side=tk.LEFT, padx=(0, 20))

        # Interval setting
        interval_frame = tk.Frame(settings_frame, bg=COLORS["surface"])
        interval_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(
            interval_frame,
            text="Screenshot Interval (seconds):",
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.interval_var = tk.StringVar(value="2.0")
        interval_entry = tk.Entry(
            interval_frame,
            textvariable=self.interval_var,
            font=FONTS["body"],
            bg=COLORS["bg"],
            relief=tk.FLAT,
            width=10
        )
        interval_entry.pack(side=tk.LEFT)

        # Output directory setting
        output_frame = tk.Frame(settings_frame, bg=COLORS["surface"])
        output_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        tk.Label(
            output_frame,
            text="Output Directory:",
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.output_var = tk.StringVar(value=self.recording_output_dir)
        output_entry = tk.Entry(
            output_frame,
            textvariable=self.output_var,
            font=FONTS["body"],
            bg=COLORS["bg"],
            relief=tk.FLAT
        )
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        tk.Button(
            output_frame,
            text="Browse...",
            font=FONTS["small"],
            bg=COLORS["bg"],
            relief=tk.FLAT,
            command=self.browse_output_dir
        ).pack(side=tk.LEFT)

    def _create_control_buttons(self):
        """Create recording control buttons"""
        control_frame = tk.Frame(self.frame, bg=COLORS["surface"])
        control_frame.pack(fill=tk.X, pady=(0, 20))

        self.record_btn = tk.Button(
            control_frame,
            text="🔴 Start Recording",
            font=(FONTS["body"][0], FONTS["body"][1], "bold"),
            bg=COLORS["error"],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=30,
            pady=15,
            borderwidth=0,
            highlightthickness=0,
            command=self.toggle_recording
        )
        self.record_btn.pack(side=tk.LEFT, padx=20, pady=20)

    def _create_preview_area(self):
        """Create screen preview area"""
        preview_frame = tk.Frame(self.frame, bg=COLORS["surface"])
        preview_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            preview_frame,
            text="Screen Preview",
            font=FONTS["heading"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(anchor=tk.W, padx=20, pady=(20, 10))

        self.preview_canvas = tk.Canvas(
            preview_frame,
            bg="black",
            highlightthickness=2,
            highlightbackground=COLORS["border"]
        )
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

    def browse_output_dir(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(initialdir=self.recording_output_dir)
        if directory:
            self.output_var.set(directory)
            self.recording_output_dir = directory

    def update_preview(self):
        """Update screen preview"""
        try:
            # Capture screen
            img = ImageGrab.grab()

            # Convert to RGB
            img_rgb = img.convert('RGB')

            # Get canvas size
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1:
                # Calculate aspect ratio
                img_width, img_height = img_rgb.size
                ratio = min(canvas_width / img_width, canvas_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)

                # Resize image
                img_resized = img_rgb.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Convert to PhotoImage
                self.preview_image = ImageTk.PhotoImage(img_resized)

                # Update canvas
                self.preview_canvas.delete("all")
                x_offset = (canvas_width - new_width) // 2
                y_offset = (canvas_height - new_height) // 2
                self.preview_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.preview_image)
        except Exception as e:
            print(f"Preview update error: {e}")

        # Schedule next update
        if self.frame.winfo_exists():
            self.root.after(1000, self.update_preview)

    def toggle_recording(self):
        """Toggle recording state"""
        if not self.app.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start screen recording"""
        try:
            # Get settings
            self.app.recording_duration = int(self.duration_var.get())
            self.app.recording_interval = float(self.interval_var.get())
            self.app.recording_output_dir = self.output_var.get()

            # Create output directory if needed
            os.makedirs(self.app.recording_output_dir, exist_ok=True)

            # Update state
            self.app.is_recording = True
            self.app.recording_frames = []
            self.app.recording_start_time = time.time()

            # Update UI
            self.record_btn.config(text="⏹️ Stop Recording", bg=COLORS["warning"])
            self.recording_status_label.config(text="● Recording...", fg=COLORS["error"])

            # Start recording thread
            self.app.recording_thread = threading.Thread(target=self.record_screen, daemon=True)
            self.app.recording_thread.start()

            # Start status update
            self.update_recording_status()

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid settings: {e}")

    def stop_recording(self):
        """Stop screen recording and save video"""
        if not self.app.is_recording:
            return

        self.app.is_recording = False

        # Update UI
        self.record_btn.config(text="🔴 Start Recording", bg=COLORS["error"])
        self.recording_status_label.config(text="● Saving video...", fg=COLORS["warning"])

        # Save video in background thread
        threading.Thread(target=self.save_recording, daemon=True).start()

    def record_screen(self):
        """Record screen in background thread"""
        start_time = time.time()
        last_screenshot_time = start_time

        try:
            while self.app.is_recording:
                current_time = time.time()
                elapsed = current_time - start_time

                # Check if duration reached
                if elapsed >= self.app.recording_duration:
                    self.root.after(0, self.stop_recording)
                    break

                # Capture screenshot at interval
                if current_time - last_screenshot_time >= self.app.recording_interval:
                    try:
                        img = ImageGrab.grab()
                        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                        self.app.recording_frames.append(frame)
                        last_screenshot_time = current_time
                    except Exception as e:
                        print(f"Capture error: {e}")

                time.sleep(0.1)

        except Exception as e:
            print(f"Recording error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Recording failed: {e}"))
            self.root.after(0, self.stop_recording)

    def save_recording(self):
        """Save recorded frames as video"""
        DB_NAME = "./db/screen_capture.db"

        try:
            if not self.app.recording_frames:
                self.root.after(0, lambda: self.recording_status_label.config(
                    text="● No frames recorded", fg=COLORS["text_light"]))
                return

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.app.recording_output_dir, f"recording_{timestamp}.mp4")

            # Save video
            height, width = self.app.recording_frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = 1.0 / self.app.recording_interval
            video = cv2.VideoWriter(filename, fourcc, fps, (width, height))

            for frame in self.app.recording_frames:
                video.write(frame)
            video.release()

            # Save to database
            self.save_to_database(DB_NAME, filename, len(self.app.recording_frames), fps)

            # Update UI
            self.root.after(0, lambda: self.recording_status_label.config(
                text="● Saved!", fg=COLORS["success"]))
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Recording saved:\n{filename}"))

            # Refresh video list if Videos tab exists
            if hasattr(self.app, 'video_listbox'):
                self.root.after(0, self.app.load_video_list)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to save: {e}"))
            self.root.after(0, lambda: self.recording_status_label.config(
                text="● Save failed", fg=COLORS["error"]))
        finally:
            self.app.recording_frames = []

    def save_to_database(self, db_name, filename, frame_count, fps):
        """Save recording info to database"""
        try:
            # Create db directory if needed
            os.makedirs(os.path.dirname(db_name), exist_ok=True)

            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()

            # Create tables if not exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    duration REAL,
                    fps REAL,
                    frame_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert video record
            start_time = datetime.fromtimestamp(self.app.recording_start_time).strftime("%Y-%m-%d %H:%M:%S.%f")
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            duration = time.time() - self.app.recording_start_time

            cursor.execute(
                "INSERT INTO videos (filename, start_time, end_time, duration, fps, frame_count) VALUES (?, ?, ?, ?, ?, ?)",
                (filename, start_time, end_time, duration, fps, frame_count)
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Database error: {e}")

    def update_recording_status(self):
        """Update recording status in real-time"""
        if self.app.is_recording and self.app.recording_start_time:
            elapsed = time.time() - self.app.recording_start_time
            remaining = max(0, self.app.recording_duration - elapsed)
            frame_count = len(self.app.recording_frames)

            status_text = f"Recording: {int(elapsed)}s | Remaining: {int(remaining)}s | Frames: {frame_count}"
            self.recording_info_label.config(text=status_text)

            # Schedule next update
            if self.frame.winfo_exists():
                self.root.after(100, self.update_recording_status)


__all__ = ["RecordingTab"]
