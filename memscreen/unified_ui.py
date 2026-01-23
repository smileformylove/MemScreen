### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

import os
import sqlite3
import cv2
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
from PIL import Image, ImageTk, ImageGrab
import requests
import json
import threading
import queue
import time
import numpy as np
from ttkthemes import ThemedTk

from .memory import Memory
from .prompts import MEMORY_ANSWER_PROMPT

# Configuration
config = {
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "qwen3:1.7b",
            "temperature": 0.8,
            "max_tokens": 2000,
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "mllm": {
        "provider": "ollama",
        "config": {
            "model": "qwen2.5vl:3b",
            "enable_vision": True,
            "temperature": 0.8,
            "max_tokens": 2000,
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "test",
            "path": "db",
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "mxbai-embed-large",
            "ollama_base_url": "http://localhost:11434",
        },
    },
}

mem = Memory.from_config(config)
DB_NAME = "./db/screen_capture.db"

# Modern, friendly color scheme (warm and inviting)
COLORS = {
    "primary": "#4F46E5",           # Warm indigo/purple blue
    "primary_dark": "#4338CA",      # Darker indigo
    "primary_light": "#818CF8",     # Light indigo
    "secondary": "#0891B2",         # Cyan/teal
    "accent": "#F59E0B",            # Warm amber
    "bg": "#FFFBF0",                # Warm cream background
    "surface": "#FFFFFF",           # White surface
    "surface_alt": "#F3F4F6",       # Light gray surface
    "text": "#1F2937",              # Dark gray text (softer than black)
    "text_light": "#6B7280",        # Medium gray text
    "text_muted": "#9CA3AF",        # Light gray text
    "border": "#E5E7EB",            # Subtle border
    "border_light": "#F3F4F6",      # Very light border
    "chat_user_bg": "#EEF2FF",      # Soft blue for user
    "chat_ai_bg": "#F0FDFA",        # Soft teal for AI
    "success": "#10B981",           # Emerald green
    "warning": "#F59E0B",           # Amber
    "error": "#EF4444",             # Soft red
    "info": "#3B82F6",              # Blue
}

# Font settings
FONTS = {
    "title": ("Segoe UI", 24, "bold"),
    "heading": ("Segoe UI", 16, "bold"),
    "body": ("Segoe UI", 11),
    "small": ("Segoe UI", 9),
    "code": ("Consolas", 10),
}


class ModernButton(tk.Canvas):
    """Custom modern button with gradient effect"""
    def __init__(self, parent, text, command=None, icon=None, style="primary", **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.text = text
        self.command = command
        self.icon = icon
        self.style = style
        self.hovered = False

        # Set colors based on style
        if style == "primary":
            self.bg_color = COLORS["primary"]
            self.hover_color = COLORS["primary_dark"]
        elif style == "secondary":
            self.bg_color = COLORS["secondary"]
            self.hover_color = COLORS["primary_dark"]
        elif style == "success":
            self.bg_color = COLORS["success"]
            self.hover_color = "#38a169"
        else:
            self.bg_color = COLORS["bg"]
            self.hover_color = COLORS["border"]

        self.configure(bg=self.bg_color)

        # Bind events
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

        self.draw_button()

    def draw_button(self):
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()

        if width > 1 and height > 1:
            # Draw rounded rectangle
            self.create_rounded_rect(0, 0, width, height, radius=8, fill=self.bg_color)
            # Draw text
            text_color = "white" if self.style in ["primary", "secondary", "success"] else COLORS["text"]
            self.create_text(width/2, height/2, text=self.text, fill=text_color, font=FONTS["body"])

    def create_rounded_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1,
                  x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius,
                  x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2,
                  x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius,
                  x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    def on_enter(self, event):
        self.hovered = True
        self.bg_color = self.hover_color
        self.draw_button()

    def on_leave(self, event):
        self.hovered = False
        if self.style == "primary":
            self.bg_color = COLORS["primary"]
        elif self.style == "secondary":
            self.bg_color = COLORS["secondary"]
        elif self.style == "success":
            self.bg_color = COLORS["success"]
        else:
            self.bg_color = COLORS["bg"]
        self.draw_button()

    def on_click(self, event):
        if self.command:
            self.command()


class MemScreenApp:
    """Unified MemScreen Application with Chat and Video Browser"""

    def __init__(self, root):
        self.root = root
        self.root.title("MemScreen - Ask Screen Anything")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # Chat variables
        self.conversation_history = []
        self.current_model = "qwen3:1.7b"

        # Video variables
        self.current_video_path = None
        self.current_video_id = None
        self.cap = None
        self.is_playing = False
        self.video_paths = []
        self.video_ids = []

        # Recording variables
        self.is_recording = False
        self.recording_thread = None
        self.recording_frames = []
        self.recording_start_time = None
        self.recording_duration = 60
        self.recording_interval = 2.0
        self.recording_output_dir = "./db/videos"

        # Setup UI
        self.setup_styles()
        self.create_header()
        self.create_navigation()
        self.create_main_content()

        # Load initial data
        self.load_models()
        self.load_video_list()

    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure styles
        style.configure("Header.TLabel", font=FONTS["title"], foreground=COLORS["primary"], background=COLORS["bg"])
        style.configure("Heading.TLabel", font=FONTS["heading"], foreground=COLORS["text"], background=COLORS["surface"])
        style.configure("Body.TLabel", font=FONTS["body"], foreground=COLORS["text"], background=COLORS["surface"])
        style.configure("Card.TFrame", background=COLORS["surface"], relief=tk.FLAT)
        style.configure("Nav.TButton", font=FONTS["body"], background=COLORS["bg"])

    def create_header(self):
        """Create application header"""
        header_frame = tk.Frame(self.root, bg=COLORS["primary"], height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        # Logo/Title
        title_label = tk.Label(
            header_frame,
            text="🖥️ MemScreen",
            font=FONTS["title"],
            bg=COLORS["primary"],
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=30, pady=20)

        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Ask Screen Anything",
            font=FONTS["body"],
            bg=COLORS["primary"],
            fg="#e2e8f0"
        )
        subtitle_label.pack(side=tk.LEFT, padx=(0, 30), pady=20)

        # Status indicator
        self.status_label = tk.Label(
            header_frame,
            text="● Online",
            font=FONTS["small"],
            bg=COLORS["primary"],
            fg=COLORS["success"]
        )
        self.status_label.pack(side=tk.RIGHT, padx=30, pady=20)

    def create_navigation(self):
        """Create navigation tabs"""
        nav_frame = tk.Frame(self.root, bg=COLORS["bg"], height=60)
        nav_frame.pack(fill=tk.X, side=tk.TOP)
        nav_frame.pack_propagate(False)

        nav_container = tk.Frame(nav_frame, bg=COLORS["bg"])
        nav_container.pack(expand=True)

        self.nav_buttons = {}
        tabs = [
            ("🔴", "Record", "record"),
            ("💬", "Chat", "chat"),
            ("🎬", "Videos", "videos"),
            ("🔍", "Search", "search"),
            ("⚙️", "Settings", "settings")
        ]

        for icon, text, tab_id in tabs:
            btn = tk.Button(
                nav_container,
                text=f"{icon} {text}",
                font=FONTS["body"],
                bg=COLORS["surface_alt"],
                fg=COLORS["text_light"],
                activebackground=COLORS["primary"],
                activeforeground="white",
                relief=tk.FLAT,
                padx=25,
                pady=12,
                cursor="hand2",
                borderwidth=0,
                highlightthickness=0,
                command=lambda t=tab_id: self.switch_tab(t)
            )
            btn.pack(side=tk.LEFT, padx=3)
            self.nav_buttons[tab_id] = btn

        # Set initial active state
        self.set_active_tab("record")

    def set_active_tab(self, tab_id):
        """Update active tab styling with modern pill design"""
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                # Active tab: primary color with white text
                btn.configure(
                    bg=COLORS["primary"],
                    fg="white",
                    font=(FONTS["body"][0], FONTS["body"][1], "bold"),
                    relief=tk.FLAT,
                    padx=25,
                    pady=12
                )
            else:
                # Inactive tab: subtle gray
                btn.configure(
                    bg=COLORS["surface_alt"],
                    fg=COLORS["text_light"],
                    font=FONTS["body"],
                    relief=tk.FLAT,
                    padx=25,
                    pady=12
                )

        self.current_tab = tab_id

    def switch_tab(self, tab_id):
        """Switch between tabs"""
        self.set_active_tab(tab_id)

        # Hide all content frames
        for frame in [self.record_frame, self.chat_frame, self.videos_frame, self.search_frame, self.settings_frame]:
            frame.pack_forget()

        # Show selected frame
        if tab_id == "record":
            self.record_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        elif tab_id == "chat":
            self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        elif tab_id == "videos":
            self.videos_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        elif tab_id == "search":
            self.search_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        elif tab_id == "settings":
            self.settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def create_main_content(self):
        """Create main content area"""
        self.content_frame = tk.Frame(self.root, bg=COLORS["bg"])
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Create all tab content
        self.create_record_tab()
        self.create_chat_tab()
        self.create_videos_tab()
        self.create_search_tab()
        self.create_settings_tab()

        # Show record by default
        self.record_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def create_record_tab(self):
        """Create screen recording interface"""
        self.record_frame = tk.Frame(self.content_frame, bg=COLORS["bg"])

        # Header
        header_frame = tk.Frame(self.record_frame, bg=COLORS["surface"], height=80)
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
        settings_frame = tk.Frame(self.record_frame, bg=COLORS["surface"])
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

        # Control buttons
        control_frame = tk.Frame(self.record_frame, bg=COLORS["surface"])
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

        # Preview area
        preview_frame = tk.Frame(self.record_frame, bg=COLORS["surface"])
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

        # Recording info
        info_frame = tk.Frame(self.record_frame, bg=COLORS["surface"])
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

    def create_chat_tab(self):
        """Create chat interface"""
        self.chat_frame = tk.Frame(self.content_frame, bg=COLORS["bg"])

        # Model selector
        model_bar = tk.Frame(self.chat_frame, bg=COLORS["surface"], height=50)
        model_bar.pack(fill=tk.X, pady=(0, 10))
        model_bar.pack_propagate(False)

        tk.Label(
            model_bar,
            text="Model:",
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text_light"]
        ).pack(side=tk.LEFT, padx=15)

        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            model_bar,
            textvariable=self.model_var,
            state="readonly",
            font=FONTS["body"],
            width=20
        )
        self.model_combo.pack(side=tk.LEFT, padx=10)
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_change)

        refresh_btn = tk.Button(
            model_bar,
            text="🔄 Refresh",
            font=FONTS["small"],
            bg=COLORS["bg"],
            relief=tk.FLAT,
            cursor="hand2",
            command=self.load_models
        )
        refresh_btn.pack(side=tk.LEFT, padx=10)

        # Chat history
        chat_container = tk.Frame(self.chat_frame, bg=COLORS["surface"])
        chat_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.chat_history = scrolledtext.ScrolledText(
            chat_container,
            wrap=tk.WORD,
            font=FONTS["body"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
            relief=tk.FLAT,
            padx=20,
            pady=20
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True)

        # Configure tags
        self.chat_history.tag_configure("user", foreground=COLORS["primary"], font=(FONTS["body"][0], FONTS["body"][1], "bold"))
        self.chat_history.tag_configure("ai", foreground=COLORS["secondary"], font=(FONTS["body"][0], FONTS["body"][1], "bold"))
        self.chat_history.tag_configure("user_msg", background=COLORS["chat_user_bg"], lmargin1=10, lmargin2=10, rmargin=10, spacing1=5, spacing3=5)
        self.chat_history.tag_configure("ai_msg", background=COLORS["chat_ai_bg"], lmargin1=10, lmargin2=10, rmargin=10, spacing1=5, spacing3=5)

        # Input area
        input_frame = tk.Frame(self.chat_frame, bg=COLORS["surface"], height=100)
        input_frame.pack(fill=tk.X)
        input_frame.pack_propagate(False)

        self.chat_input = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=FONTS["body"],
            bg=COLORS["bg"],
            relief=tk.FLAT,
            padx=15,
            pady=10,
            height=3
        )
        self.chat_input.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.chat_input.bind("<Return>", self.on_chat_enter)

        # Send button
        send_btn = tk.Button(
            input_frame,
            text="Send ➤",
            font=FONTS["body"],
            bg=COLORS["primary"],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.send_chat_message
        )
        send_btn.place(relx=0.95, rely=0.5, anchor=tk.E)

        self.thinking_label = tk.Label(
            input_frame,
            text="AI is thinking...",
            font=FONTS["small"],
            bg=COLORS["surface"],
            fg=COLORS["text_light"]
        )

    def create_videos_tab(self):
        """Create videos browser"""
        self.videos_frame = tk.Frame(self.content_frame, bg=COLORS["bg"])

        # Left panel - video list
        left_panel = tk.Frame(self.videos_frame, bg=COLORS["surface"], width=300)
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

        # Video list
        list_container = tk.Frame(left_panel, bg=COLORS["surface"])
        list_container.pack(fill=tk.BOTH, expand=True, padx=15)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.video_listbox = tk.Listbox(
            list_container,
            font=FONTS["small"],
            bg=COLORS["bg"],
            fg=COLORS["text"],
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set
        )
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.video_listbox.yview)
        self.video_listbox.bind('<<ListboxSelect>>', self.on_video_select)

        # Right panel - video player
        right_panel = tk.Frame(self.videos_frame, bg=COLORS["surface"])
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

        # Controls
        controls_panel = tk.Frame(right_panel, bg=COLORS["surface"])
        controls_panel.pack(fill=tk.X)

        # Timeline
        self.timeline = ttk.Scale(controls_panel, from_=0, to=100, orient=tk.HORIZONTAL)
        self.timeline.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.timeline.bind("<ButtonRelease-1>", self.on_timeline_change)

        # Timecode
        self.timecode_label = tk.Label(
            controls_panel,
            text="00:00:00",
            font=FONTS["code"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        )
        self.timecode_label.pack(side=tk.LEFT, padx=(0, 10))

        # Play/Pause
        self.play_btn = tk.Button(
            controls_panel,
            text="▶️ Play",
            font=FONTS["small"],
            bg=COLORS["primary"],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_play
        )
        self.play_btn.pack(side=tk.LEFT)

    def create_search_tab(self):
        """Create search interface"""
        self.search_frame = tk.Frame(self.content_frame, bg=COLORS["bg"])

        # Search bar
        search_bar = tk.Frame(self.search_frame, bg=COLORS["surface"], height=80)
        search_bar.pack(fill=tk.X, pady=(0, 20))
        search_bar.pack_propagate(False)

        tk.Label(
            search_bar,
            text="🔍 Search Your Screen Memory",
            font=FONTS["heading"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(pady=15)

        search_input_frame = tk.Frame(search_bar, bg=COLORS["surface"])
        search_input_frame.pack(fill=tk.X, padx=20)

        self.search_input = tk.Entry(
            search_input_frame,
            font=FONTS["body"],
            bg=COLORS["bg"],
            relief=tk.FLAT
        )
        self.search_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), pady=10)
        self.search_input.bind("<Return>", lambda e: self.perform_search())

        tk.Button(
            search_input_frame,
            text="Search",
            font=FONTS["body"],
            bg=COLORS["primary"],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.perform_search
        ).pack(side=tk.LEFT)

        # Results area
        results_frame = tk.Frame(self.search_frame, bg=COLORS["surface"])
        results_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            results_frame,
            text="Search Results",
            font=FONTS["heading"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(fill=tk.X, padx=20, pady=(20, 10))

        self.search_results = scrolledtext.ScrolledText(
            results_frame,
            wrap=tk.WORD,
            font=FONTS["body"],
            bg=COLORS["bg"],
            relief=tk.FLAT,
            padx=20,
            pady=20
        )
        self.search_results.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        self.search_results.insert(tk.END, "Enter a search query above to find content in your screen recordings...")
        self.search_results.config(state=tk.DISABLED)

    def create_settings_tab(self):
        """Create settings interface"""
        self.settings_frame = tk.Frame(self.content_frame, bg=COLORS["bg"])

        settings_content = tk.Frame(self.settings_frame, bg=COLORS["surface"])
        settings_content.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        tk.Label(
            settings_content,
            text="⚙️ Settings",
            font=FONTS["title"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(fill=tk.X, pady=(0, 30))

        # Settings sections
        settings_sections = [
            ("🤖 AI Models", "Configure Ollama models", ["qwen3:1.7b - Fast & efficient", "qwen2.5vl:3b - Vision capable", "mxbai-embed-large - Embeddings"]),
            ("💾 Storage", "Database location", [DB_NAME]),
            ("🎨 Appearance", "Theme settings", ["Arc theme (default)"]),
            ("📊 Statistics", "Usage statistics", ["Videos recorded: 0", "Total duration: 0:00:00"]),
        ]

        for title, subtitle, items in settings_sections:
            section = tk.Frame(settings_content, bg=COLORS["bg"], pady=15)
            section.pack(fill=tk.X, pady=(0, 15))

            tk.Label(
                section,
                text=title,
                font=FONTS["heading"],
                bg=COLORS["bg"],
                fg=COLORS["text"]
            ).pack(anchor=tk.W, padx=15, pady=(15, 5))

            tk.Label(
                section,
                text=subtitle,
                font=FONTS["small"],
                bg=COLORS["bg"],
                fg=COLORS["text_light"]
            ).pack(anchor=tk.W, padx=15, pady=(0, 10))

            for item in items:
                tk.Label(
                    section,
                    text=f"  • {item}",
                    font=FONTS["body"],
                    bg=COLORS["bg"],
                    fg=COLORS["text"]
                ).pack(anchor=tk.W, padx=15)

    # Chat methods
    def load_models(self):
        """Load available Ollama models"""
        try:
            response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
            response.raise_for_status()
            models_data = response.json()

            models = [model['name'] for model in models_data.get('models', [])]
            self.model_combo['values'] = models

            if models:
                self.model_combo.current(0)
                self.current_model = models[0]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load models: {e}")

    def on_model_change(self, event):
        """Handle model selection change"""
        self.current_model = self.model_var.get()

    def on_chat_enter(self, event):
        """Handle Enter key in chat input"""
        if event.state & 0x4:  # Ctrl+Enter for new line
            return "continue"
        self.send_chat_message()
        return "break"

    def send_chat_message(self):
        """Send chat message to AI"""
        user_input = self.chat_input.get("1.0", tk.END).strip()
        if not user_input:
            return

        # Add screen memory context
        enhanced_input = MEMORY_ANSWER_PROMPT + "\n\n" + user_input
        related_memories = mem.search(query=enhanced_input, user_id="screenshot")
        if related_memories and 'results' in related_memories and len(related_memories['results']) > 0:
            enhanced_input = related_memories['results'][0]['memory'] + '\n\n' + enhanced_input

        self.chat_input.delete("1.0", tk.END)

        # Add user message to chat
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, "You:\n", "user")
        self.chat_history.insert(tk.END, f"{user_input}\n\n", "user_msg")
        self.chat_history.config(state=tk.DISABLED)
        self.chat_history.see(tk.END)

        # Add thinking indicator
        self.thinking_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Send to AI in background thread
        message_queue = queue.Queue()
        thread = threading.Thread(
            target=self.send_to_ollama,
            args=(enhanced_input, self.current_model, message_queue),
            daemon=True
        )
        thread.start()

        # Update UI with response
        self.process_ai_response(message_queue, thread)

    def send_to_ollama(self, prompt, model_name, message_queue):
        """Send request to Ollama"""
        url = "http://127.0.0.1:11434/api/chat"
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True
        }

        try:
            response = requests.post(url, json=payload, stream=True, timeout=60)
            response.raise_for_status()

            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data_str = line.decode('utf-8').replace("data: ", "", 1)
                        if data_str == "[DONE]":
                            break

                        data = json.loads(data_str)
                        if "message" in data and "content" in data["message"]:
                            chunk = data["message"]["content"]
                            full_response += chunk
                            message_queue.put(("chunk", chunk))
                    except (json.JSONDecodeError, KeyError):
                        pass

            message_queue.put(("done", full_response))

        except Exception as e:
            message_queue.put(("error", str(e)))

    def process_ai_response(self, message_queue, thread):
        """Process AI response and update UI"""
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, "AI:\n", "ai")

        def update():
            try:
                item = message_queue.get_nowait()
                if item[0] == "chunk":
                    self.chat_history.insert(tk.END, item[1])
                    self.chat_history.see(tk.END)
                    self.root.after(10, update)
                elif item[0] == "done":
                    self.chat_history.insert(tk.END, "\n\n", "ai_msg")
                    self.chat_history.config(state=tk.DISABLED)
                    self.thinking_label.place_forget()

                    # Save to conversation history
                    self.conversation_history.append({"role": "assistant", "content": item[1]})
                elif item[0] == "error":
                    self.chat_history.insert(tk.END, f"\nError: {item[1]}\n\n", "ai_msg")
                    self.chat_history.config(state=tk.DISABLED)
                    self.thinking_label.place_forget()
            except queue.Empty:
                if thread.is_alive():
                    self.root.after(10, update)
                else:
                    self.chat_history.config(state=tk.DISABLED)
                    self.thinking_label.place_forget()

        update()

    # Video methods
    def load_video_list(self):
        """Load video list from database"""
        self.video_listbox.delete(0, tk.END)
        self.video_paths.clear()
        self.video_ids.clear()

        try:
            conn = sqlite3.connect(DB_NAME)
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

        if self.cap and self.cap.isOpened():
            self.cap.release()

        self.cap = cv2.VideoCapture(self.current_video_path)
        if self.cap.isOpened():
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = self.cap.get(cv2.CAP_PROP_FPS) or 10
            duration = total_frames / fps

            self.timeline.config(to=duration)
            self.show_frame(0)

            # Update info
            file_size = os.path.getsize(self.current_video_path)
            size_mb = file_size / (1024 * 1024)
            self.video_info.config(text=f"📁 {os.path.basename(self.current_video_path)}\n⏱️ {duration:.1f}s | 📊 {size_mb:.1f} MB")

    def show_frame(self, frame_pos):
        """Show specific frame"""
        if not self.cap or not self.cap.isOpened():
            return

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        ret, frame = self.cap.read()
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
                self.tk_image = ImageTk.PhotoImage(image=pil_image)

                self.video_canvas.delete("all")
                x = (canvas_width - new_width) // 2
                y = (canvas_height - new_height) // 2
                self.video_canvas.create_image(x, y, anchor=tk.NW, image=self.tk_image)

    def on_timeline_change(self, event):
        """Handle timeline scrubbing"""
        if not self.cap or not self.cap.isOpened():
            return

        seek_time = self.timeline.get()
        fps = self.cap.get(cv2.CAP_PROP_FPS) or 10
        frame_pos = int(seek_time * fps)
        self.show_frame(frame_pos)

        # Update timecode
        minutes, seconds = divmod(int(seek_time), 60)
        hours, minutes = divmod(minutes, 60)
        self.timecode_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def toggle_play(self):
        """Toggle play/pause"""
        if not self.cap or not self.cap.isOpened():
            return

        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_btn.config(text="⏸️ Pause")
            self.play_video()
        else:
            self.play_btn.config(text="▶️ Play")

    def play_video(self):
        """Play video"""
        if not self.is_playing or not self.cap or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
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
                self.tk_image = ImageTk.PhotoImage(image=pil_image)

                self.video_canvas.delete("all")
                x = (canvas_width - new_width) // 2
                y = (canvas_height - new_height) // 2
                self.video_canvas.create_image(x, y, anchor=tk.NW, image=self.tk_image)

            # Update timeline
            current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            fps = self.cap.get(cv2.CAP_PROP_FPS) or 10
            current_time = current_pos / fps
            self.timeline.set(current_time)

            minutes, seconds = divmod(int(current_time), 60)
            hours, minutes = divmod(minutes, 60)
            self.timecode_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            # Schedule next frame
            delay = int(1000 / fps)
            self.root.after(delay, self.play_video)
        else:
            self.is_playing = False
            self.play_btn.config(text="▶️ Play")

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

                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
                conn.commit()
                conn.close()

                self.load_video_list()
                messagebox.showinfo("Success", "Video deleted")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {e}")

    # Search methods
    def perform_search(self):
        """Perform search in screen memory"""
        query = self.search_input.get().strip()
        if not query:
            return

        self.search_results.config(state=tk.NORMAL)
        self.search_results.delete(1.0, tk.END)
        self.search_results.insert(tk.END, f"🔍 Searching for: {query}\n\n")
        self.search_results.config(state=tk.DISABLED)

        # Search using memory system
        results = mem.search(query=query, user_id="screenshot")

        self.search_results.config(state=tk.NORMAL)
        if results and 'results' in results and len(results['results']) > 0:
            for i, result in enumerate(results['results'][:10], 1):
                self.search_results.insert(tk.END, f"{i}. {result.get('memory', 'No memory')}\n\n")
        else:
            self.search_results.insert(tk.END, "No results found.\n")
        self.search_results.config(state=tk.DISABLED)

    # Recording methods
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
        if self.record_frame.winfo_exists():
            self.root.after(1000, self.update_preview)

    def toggle_recording(self):
        """Toggle recording state"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start screen recording"""
        try:
            # Get settings
            self.recording_duration = int(self.duration_var.get())
            self.recording_interval = float(self.interval_var.get())
            self.recording_output_dir = self.output_var.get()

            # Create output directory if needed
            os.makedirs(self.recording_output_dir, exist_ok=True)

            # Update state
            self.is_recording = True
            self.recording_frames = []
            self.recording_start_time = time.time()

            # Update UI
            self.record_btn.config(text="⏹️ Stop Recording", bg=COLORS["warning"])
            self.recording_status_label.config(text="● Recording...", fg=COLORS["error"])

            # Start recording thread
            self.recording_thread = threading.Thread(target=self.record_screen, daemon=True)
            self.recording_thread.start()

            # Start status update
            self.update_recording_status()

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid settings: {e}")

    def stop_recording(self):
        """Stop screen recording and save video"""
        if not self.is_recording:
            return

        self.is_recording = False

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
            while self.is_recording:
                current_time = time.time()
                elapsed = current_time - start_time

                # Check if duration reached
                if elapsed >= self.recording_duration:
                    self.root.after(0, self.stop_recording)
                    break

                # Capture screenshot at interval
                if current_time - last_screenshot_time >= self.recording_interval:
                    try:
                        img = ImageGrab.grab()
                        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                        self.recording_frames.append(frame)
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
        try:
            if not self.recording_frames:
                self.root.after(0, lambda: self.recording_status_label.config(text="● No frames recorded", fg=COLORS["text_light"]))
                return

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.recording_output_dir, f"recording_{timestamp}.mp4")

            # Save video
            height, width = self.recording_frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = 1.0 / self.recording_interval
            video = cv2.VideoWriter(filename, fourcc, fps, (width, height))

            for frame in self.recording_frames:
                video.write(frame)
            video.release()

            # Save to database
            self.save_to_database(filename, len(self.recording_frames), fps)

            # Update UI
            self.root.after(0, lambda: self.recording_status_label.config(text="● Saved!", fg=COLORS["success"]))
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Recording saved:\n{filename}"))

            # Refresh video list if Videos tab exists
            if hasattr(self, 'video_listbox'):
                self.root.after(0, self.load_video_list)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to save: {e}"))
            self.root.after(0, lambda: self.recording_status_label.config(text="● Save failed", fg=COLORS["error"]))
        finally:
            self.recording_frames = []

    def save_to_database(self, filename, frame_count, fps):
        """Save recording info to database"""
        try:
            # Create db directory if needed
            os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)

            conn = sqlite3.connect(DB_NAME)
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
            start_time = datetime.fromtimestamp(self.recording_start_time).strftime("%Y-%m-%d %H:%M:%S.%f")
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            duration = time.time() - self.recording_start_time

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
        if self.is_recording and self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            remaining = max(0, self.recording_duration - elapsed)
            frame_count = len(self.recording_frames)

            status_text = f"Recording: {int(elapsed)}s | Remaining: {int(remaining)}s | Frames: {frame_count}"
            self.recording_info_label.config(text=status_text)

            # Schedule next update
            if self.record_frame.winfo_exists():
                self.root.after(100, self.update_recording_status)


def main():
    """Main entry point"""
    root = ThemedTk(theme="arc")
    app = MemScreenApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
