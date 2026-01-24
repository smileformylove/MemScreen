### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Video browser tab for viewing recordings"""

import os
import sqlite3
import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from PIL import Image, ImageTk

from .base_tab import BaseTab
from ..components.colors import COLORS, FONTS, STATUS_COLORS


class VideoTab(BaseTab):
    """Video browser tab"""

    def __init__(self, parent, app, db_name):
        super().__init__(parent, app)
        self.db_name = db_name
        self.video_listbox = None
        self.video_canvas = None
        self.video_info = None
        self.timeline = None
        self.timecode_label = None
        self.play_btn = None
        self.volume_slider = None
        self.current_video_path = None
        self.current_video_id = None
        self.video_paths = []
        self.video_ids = []
        self.thumbnails = {}
        self.is_playing = False
        self.playback_speed = 1.0

    def create_ui(self):
        """Create video tab UI"""
        self.frame = tk.Frame(self.parent, bg=COLORS["bg"])

        # Left panel - video list
        left_panel = tk.Frame(self.frame, bg=COLORS["surface"], width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        # Header
        tk.Label(
            left_panel,
            text="📹 Recordings",
            font=FONTS["heading"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(fill=tk.X, padx=15, pady=(15, 10))

        # Controls
        controls_frame = tk.Frame(left_panel, bg=COLORS["surface"])
        controls_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        tk.Button(
            controls_frame,
            text="🔄 Refresh",
            font=FONTS["small"],
            bg=COLORS["bg"],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.load_video_list
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            controls_frame,
            text="🗑️ Delete",
            font=FONTS["small"],
            bg=COLORS["bg"],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.delete_video
        ).pack(side=tk.LEFT)

        # Video list with thumbnails
        list_container = tk.Frame(left_panel, bg=COLORS["surface"])
        list_container.pack(fill=tk.BOTH, expand=True, padx=15)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Enhanced listbox with thumbnails support
        self.video_listbox = tk.Listbox(
            list_container,
            font=FONTS["small"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            highlightthickness=0,
            borderwidth=0
        )
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.video_listbox.yview)

        # Bind selection event with animation
        self.video_listbox.bind('<<ListboxSelect>>', self.on_video_select)

        # Right panel - video player
        right_panel = tk.Frame(self.frame, bg=COLORS["surface"])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Video canvas
        video_container = tk.Frame(right_panel, bg="black", bd=2, relief=tk.SUNKEN)
        video_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.video_canvas = tk.Canvas(video_container, bg="black", highlightthickness=0)
        self.video_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Video info
        self.video_info = tk.Label(
            right_panel,
            text="Select a video to play",
            font=FONTS["small"],
            bg=COLORS["surface"],
            fg=COLORS["text_light"],
            height=3
        )
        self.video_info.pack(fill=tk.X, pady=(0, 10))

        # Controls with enhanced layout
        controls_panel = tk.Frame(right_panel, bg=COLORS["surface"], height=60)
        controls_panel.pack(fill=tk.X, pady=(10, 0))
        controls_panel.pack_propagate(False)

        # Main control row
        main_controls = tk.Frame(controls_panel, bg=COLORS["surface"])
        main_controls.pack(fill=tk.X, pady=10)

        # Play/Pause button with enhanced styling
        self.play_btn = tk.Button(
            main_controls,
            text="▶️",
            font=("Segoe UI", 16),
            bg=COLORS["primary"],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            width=3,
            command=self.toggle_play,
            highlightthickness=0,
            borderwidth=0
        )
        self.play_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Timeline slider with smooth scrubbing
        timeline_frame = tk.Frame(main_controls, bg=COLORS["surface"])
        timeline_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.timeline = ttk.Scale(
            timeline_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self.on_timeline_drag
        )
        self.timeline.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.timeline.bind("<ButtonRelease-1>", self.on_timeline_change)

        # Timecode display
        self.timecode_label = tk.Label(
            main_controls,
            text="00:00:00",
            font=FONTS["code"],
            bg=COLORS["surface"],
            fg=COLORS["text"],
            width=8
        )
        self.timecode_label.pack(side=tk.LEFT, padx=(0, 10))

        # Volume control
        volume_frame = tk.Frame(main_controls, bg=COLORS["surface"])
        volume_frame.pack(side=tk.LEFT)

        tk.Label(
            volume_frame,
            text="🔊",
            font=FONTS["body"],
            bg=COLORS["surface"]
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.volume_slider = ttk.Scale(
            volume_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            length=80,
            value=50
        )
        self.volume_slider.pack(side=tk.LEFT)

    def load_video_list(self):
        """Load video list from database"""
        self.video_listbox.delete(0, tk.END)
        self.video_paths.clear()
        self.video_ids.clear()

        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT id, filename, start_time, duration FROM videos ORDER BY start_time DESC")
            videos = cursor.fetchall()
            conn.close()

            for video in videos:
                video_id, filename, start_time, duration = video
                start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S.%f")
                formatted_time = start_dt.strftime("%Y-%m-%d %H:%M")
                minutes, seconds = divmod(int(duration), 60)
                display_text = f"{formatted_time} - {minutes:02d}:{seconds:02d}"

                self.video_listbox.insert(tk.END, display_text)
                self.video_paths.append(filename)
                self.video_ids.append(video_id)

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load videos: {e}")

    def on_video_select(self, event):
        """Handle video selection"""
        selection = self.video_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        self.current_video_path = self.video_paths[index]
        self.current_video_id = self.video_ids[index]

        if self.app.cap and self.app.cap.isOpened():
            self.app.cap.release()

        self.app.cap = cv2.VideoCapture(self.current_video_path)
        if self.app.cap.isOpened():
            total_frames = int(self.app.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = self.app.cap.get(cv2.CAP_PROP_FPS) or 10
            duration = total_frames / fps

            self.timeline.config(to=duration)
            self.show_frame(0)

            # Update info
            file_size = os.path.getsize(self.current_video_path)
            size_mb = file_size / (1024 * 1024)
            self.video_info.config(text=f"📁 {os.path.basename(self.current_video_path)}\n⏱️ {duration:.1f}s | 📊 {size_mb:.1f} MB")

    def show_frame(self, frame_pos):
        """Show specific frame"""
        if not self.app.cap or not self.app.cap.isOpened():
            return

        self.app.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        ret, frame = self.app.cap.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1:
                img_height, img_width = rgb_image.shape[:2]
                ratio = min(canvas_width / img_width, canvas_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)

                resized = cv2.resize(rgb_image, (new_width, new_height))
                pil_image = Image.fromarray(resized)
                self.app.tk_image = ImageTk.PhotoImage(image=pil_image)

                self.video_canvas.delete("all")
                x = (canvas_width - new_width) // 2
                y = (canvas_height - new_height) // 2
                self.video_canvas.create_image(x, y, anchor=tk.NW, image=self.app.tk_image)

    def on_timeline_drag(self, value):
        """Handle timeline dragging for smooth scrubbing"""
        if not self.app.cap or not self.app.cap.isOpened():
            return

        seek_time = float(value)
        fps = self.app.cap.get(cv2.CAP_PROP_FPS) or 10
        frame_pos = int(seek_time * fps)

        # Show frame while dragging
        self.show_frame(frame_pos)

        # Update timecode
        minutes, seconds = divmod(int(seek_time), 60)
        hours, minutes = divmod(minutes, 60)
        self.timecode_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def on_timeline_change(self, event):
        """Handle timeline release"""
        # Playback continues from new position
        pass

    def toggle_play(self):
        """Toggle play/pause with button animation"""
        if not self.app.cap or not self.app.cap.isOpened():
            return

        self.app.is_playing = not self.app.is_playing

        if self.app.is_playing:
            # Update button to pause with animation
            self.play_btn.config(text="⏸️", bg=COLORS["warning"])
            self.play_video()
        else:
            # Update button to play with animation
            self.play_btn.config(text="▶️", bg=COLORS["primary"])

    def play_video(self):
        """Play video"""
        if not self.app.is_playing or not self.app.cap or not self.app.cap.isOpened():
            return

        ret, frame = self.app.cap.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1:
                img_height, img_width = rgb_image.shape[:2]
                ratio = min(canvas_width / img_width, canvas_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)

                resized = cv2.resize(rgb_image, (new_width, new_height))
                pil_image = Image.fromarray(resized)
                self.app.tk_image = ImageTk.PhotoImage(image=pil_image)

                self.video_canvas.delete("all")
                x = (canvas_width - new_width) // 2
                y = (canvas_height - new_height) // 2
                self.video_canvas.create_image(x, y, anchor=tk.NW, image=self.app.tk_image)

            # Update timeline
            current_pos = self.app.cap.get(cv2.CAP_PROP_POS_FRAMES)
            fps = self.app.cap.get(cv2.CAP_PROP_FPS) or 10
            current_time = current_pos / fps
            self.timeline.set(current_time)

            minutes, seconds = divmod(int(current_time), 60)
            hours, minutes = divmod(minutes, 60)
            self.timecode_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            # Schedule next frame
            delay = int(1000 / fps)
            self.root.after(delay, self.play_video)
        else:
            # Video ended - reset play button
            self.app.is_playing = False
            self.play_btn.config(text="▶️", bg=COLORS["primary"])

            # Reset to beginning
            if self.app.cap:
                self.app.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.timeline.set(0)
                self.show_frame(0)

    def delete_video(self):
        """Delete selected video"""
        selection = self.video_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a video first")
            return

        index = selection[0]
        video_id = self.video_ids[index]
        video_path = self.video_paths[index]

        if messagebox.askyesno("Confirm Delete", f"Delete this video?\n\n{os.path.basename(video_path)}"):
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)

                conn = sqlite3.connect(self.db_name)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
                conn.commit()
                conn.close()

                self.load_video_list()
                messagebox.showinfo("Success", "Video deleted")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {e}")


__all__ = ["VideoTab"]
