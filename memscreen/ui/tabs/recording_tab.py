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
from ..components.colors import COLORS, FONTS, STATUS_COLORS, ANIMATION_COLORS
from ..components.animations import ProgressAnimation, CounterAnimation, ScrollAnimator


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

        # Animation components
        self.pulsing_indicator = None
        self.progress_canvas = None
        self.progress_bg_id = None
        self.progress_bar_id = None
        self.countdown_label = None
        self.frame_counter_label = None
        self.countdown_animation = None

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

        # Animated recording status with pulsing indicator canvas
        status_container = tk.Frame(header_frame, bg=COLORS["surface"])
        status_container.pack(side=tk.RIGHT, padx=30, pady=20)

        # Create canvas for pulsing indicator
        self.pulsing_indicator = tk.Canvas(status_container, width=30, height=30,
                                           bg=COLORS["surface"], highlightthickness=0)
        self.pulsing_indicator.pack(side=tk.LEFT, padx=(0, 10))

        # Recording status label
        self.recording_status_label = tk.Label(
            status_container,
            text="Ready to record",
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text_light"]
        )
        self.recording_status_label.pack(side=tk.LEFT)

        # Settings section
        self._create_settings_section()

        # Control buttons
        self._create_control_buttons()

        # Preview area
        self._create_preview_area()

        # Recording info with progress bar and counters
        info_frame = tk.Frame(self.frame, bg=COLORS["surface"])
        info_frame.pack(fill=tk.X)

        # Progress bar canvas
        progress_container = tk.Frame(info_frame, bg=COLORS["surface"])
        progress_container.pack(fill=tk.X, padx=20, pady=(10, 5))

        self.progress_canvas = tk.Canvas(progress_container, height=8, bg=COLORS["bg"],
                                         highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X)

        # Create progress bar elements
        self.progress_bg_id = self.progress_canvas.create_rectangle(
            0, 0, 1000, 8, fill=COLORS["border"], outline=""
        )
        self.progress_bar_id = self.progress_canvas.create_rectangle(
            0, 0, 0, 8, fill=COLORS["success"], outline=""
        )

        # Counters display
        counters_frame = tk.Frame(info_frame, bg=COLORS["surface"])
        counters_frame.pack(fill=tk.X, padx=20, pady=(5, 10))

        # Countdown timer
        countdown_container = tk.Frame(counters_frame, bg=COLORS["surface"])
        countdown_container.pack(side=tk.LEFT, padx=(0, 30))

        tk.Label(
            countdown_container,
            text="⏱️ Time Remaining:",
            font=FONTS["small"],
            bg=COLORS["surface"],
            fg=COLORS["text_light"]
        ).pack(side=tk.LEFT)

        self.countdown_label = tk.Label(
            countdown_container,
            text="00:00",
            font=FONTS["code"],
            bg=COLORS["surface"],
            fg=COLORS["text"],
            width=8
        )
        self.countdown_label.pack(side=tk.LEFT, padx=(5, 0))

        # Frame counter
        frame_container = tk.Frame(counters_frame, bg=COLORS["surface"])
        frame_container.pack(side=tk.LEFT)

        tk.Label(
            frame_container,
            text="🎞️ Frames:",
            font=FONTS["small"],
            bg=COLORS["surface"],
            fg=COLORS["text_light"]
        ).pack(side=tk.LEFT)

        self.frame_counter_label = tk.Label(
            frame_container,
            text="0",
            font=FONTS["code"],
            bg=COLORS["surface"],
            fg=COLORS["text"],
            width=6
        )
        self.frame_counter_label.pack(side=tk.LEFT, padx=(5, 0))

        # Original recording info label (hidden by default)
        self.recording_info_label = tk.Label(
            info_frame,
            text="",
            font=FONTS["small"],
            bg=COLORS["surface"],
            fg=COLORS["text_light"]
        )

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
            self.recording_status_label.config(
                text="Recording...",
                fg=STATUS_COLORS["recording"]["text"]
            )

            # Start pulsing indicator animation
            self._start_pulsing_indicator()

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
        self.recording_status_label.config(
            text="Saving video...",
            fg=STATUS_COLORS["processing"]["text"]
        )

        # Stop pulsing indicator
        self._stop_pulsing_indicator()

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
        """Update recording status in real-time with animations"""
        if self.app.is_recording and self.app.recording_start_time:
            elapsed = time.time() - self.app.recording_start_time
            remaining = max(0, self.app.recording_duration - elapsed)
            frame_count = len(self.app.recording_frames)

            # Update progress bar
            progress = elapsed / self.app.recording_duration
            self._update_progress_bar(progress)

            # Update countdown timer
            self._update_countdown(int(remaining))

            # Update frame counter with animation
            self._update_frame_counter(frame_count)

            # Schedule next update
            if self.frame.winfo_exists():
                self.root.after(100, self.update_recording_status)

    def _start_pulsing_indicator(self):
        """Start pulsing red dot animation"""
        if not self.pulsing_indicator:
            return

        self.pulsing_indicator.delete("all")

        # Create pulsing animation
        def animate_pulse():
            if not self.app.is_recording:
                return

            import math
            current_time = time.time()
            pulse_phase = (current_time * 3) % (2 * math.pi)  # 3 pulses per second

            # Base red circle
            center_x, center_y = 15, 15
            base_radius = 6

            self.pulsing_indicator.delete("all")

            # Draw pulsing rings
            for i in range(3):
                phase_offset = i * 0.5
                pulse_value = (math.sin(pulse_phase + phase_offset) + 1) / 2
                ring_radius = base_radius + 8 * pulse_value

                # Calculate alpha by varying color intensity
                intensity = int(255 * (1 - pulse_value * 0.5))
                color = f"#{intensity:02x}0000"

                self.pulsing_indicator.create_oval(
                    center_x - ring_radius, center_y - ring_radius,
                    center_x + ring_radius, center_y + ring_radius,
                    outline=color,
                    width=2
                )

            # Draw solid center circle
            self.pulsing_indicator.create_oval(
                center_x - base_radius, center_y - base_radius,
                center_x + base_radius, center_y + base_radius,
                fill=COLORS["error"],
                outline=COLORS["error"]
            )

            # Schedule next frame
            if self.app.is_recording and self.pulsing_indicator.winfo_exists():
                self.pulsing_indicator.after(30, animate_pulse)

        animate_pulse()

    def _stop_pulsing_indicator(self):
        """Stop pulsing animation and show static indicator"""
        if not self.pulsing_indicator:
            return

        self.pulsing_indicator.delete("all")

        # Draw static indicator
        center_x, center_y = 15, 15
        radius = 6

        self.pulsing_indicator.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            fill=COLORS["success"],
            outline=COLORS["success"]
        )

    def _update_progress_bar(self, progress: float):
        """Update progress bar with smooth animation"""
        if not self.progress_canvas:
            return

        self.progress_canvas.update()

        canvas_width = self.progress_canvas.winfo_width()
        if canvas_width > 1:
            bar_width = int(canvas_width * progress)
            self.progress_canvas.coords(
                self.progress_bar_id,
                0, 0, bar_width, 8
            )

            # Change color based on progress
            if progress < 0.3:
                color = COLORS["success"]
            elif progress < 0.7:
                color = COLORS["warning"]
            else:
                color = COLORS["error"]

            self.progress_canvas.itemconfig(self.progress_bar_id, fill=color)

    def _update_countdown(self, remaining_seconds: int):
        """Update countdown timer display"""
        if not self.countdown_label:
            return

        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        time_str = f"{minutes:02d}:{seconds:02d}"

        self.countdown_label.config(text=time_str)

        # Change color when time is running out
        if remaining_seconds <= 10:
            self.countdown_label.config(fg=COLORS["error"])
        elif remaining_seconds <= 30:
            self.countdown_label.config(fg=COLORS["warning"])
        else:
            self.countdown_label.config(fg=COLORS["text"])

    def _update_frame_counter(self, frame_count: int):
        """Update frame counter with animation"""
        if not self.frame_counter_label:
            return

        self.frame_counter_label.config(text=str(frame_count))


__all__ = ["RecordingTab"]
