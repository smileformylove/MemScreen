### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Main MemScreen application orchestration"""

import tkinter as tk
from tkinter import ttk
import cv2

from .components.colors import COLORS, FONTS
from .tabs.recording_tab import RecordingTab
from .tabs.chat_tab import ChatTab
from .tabs.video_tab import VideoTab
# SearchTab removed - functionality merged into ChatTab
from .tabs.settings_tab import SettingsTab
from .tabs.process_mining_tab import ProcessMiningTab
from memscreen.input_tracker import InputTracker


class MemScreenApp:
    """Unified MemScreen Application with Chat and Video Browser"""

    def __init__(self, root, mem, db_name="./db/screen_capture.db"):
        self.root = root
        self.root.title("MemScreen - Ask Screen Anything")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        # CRITICAL: Force global color palette for all buttons
        # Use light background + dark text for maximum contrast
        self.root.tk_setPalette(
            background="#1F2937",
            foreground="#FFFFFF",
            activeBackground="#E5E7EB",
            activeForeground="#000000",
            highlightBackground="#4B5563",
            highlightColor="#E5E7EB"
        )

        # Video variables
        self.cap = None
        self.is_playing = False

        # Recording variables
        self.is_recording = False
        self.recording_thread = None
        self.recording_frames = []
        self.recording_start_time = None
        self.recording_duration = 60
        self.recording_interval = 2.0
        self.recording_output_dir = "./db/videos"

        # Store mem and db_name
        self.mem = mem
        self.db_name = db_name

        # Initialize InputTracker for process mining
        self.input_tracker = InputTracker(db_path="./db/input_events.db")

        # Setup UI
        self.setup_styles()
        self.create_header()
        self.create_navigation()
        self.create_main_content()

        # Load initial data
        if hasattr(self, 'chat_tab'):
            self.chat_tab.load_models()
        if hasattr(self, 'video_tab'):
            self.video_tab.load_video_list()

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
            ("💬", "AI Chat", "chat"),  # Renamed to emphasize AI
            ("🎬", "Videos", "videos"),
            ("📊", "Process", "process"),  # NEW: Process Mining tab
            ("⚙️", "Settings", "settings")
        ]

        for icon, text, tab_id in tabs:
            btn = tk.Button(
                nav_container,
                text=f"{icon} {text}",
                font=("Helvetica", 14, "bold"),
                bg="#E5E7EB",  # Light gray background
                fg="#000000",  # Black text
                activebackground="#D1D5DB",  # Slightly darker when active
                activeforeground="#000000",
                relief=tk.RAISED,
                bd=3,
                padx=25,
                pady=12,
                cursor="hand2",
                borderwidth=3,
                highlightthickness=0,
                command=lambda t=tab_id: self.switch_tab(t)
            )
            btn.pack(side=tk.LEFT, padx=3)
            self.nav_buttons[tab_id] = btn

        # Set initial active state
        self.set_active_tab("record")

    def set_active_tab(self, tab_id):
        """Update active tab styling with high contrast"""
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                # Active tab: darker gray with black text
                btn.configure(
                    bg="#D1D5DB",  # Darker light gray
                    fg="#000000",  # Black text
                    font=("Helvetica", 14, "bold"),
                    relief=tk.SUNKEN,
                    bd=4,
                    highlightthickness=0,
                    padx=25,
                    pady=12
                )
            else:
                # Inactive tab: light gray with black text
                btn.configure(
                    bg="#E5E7EB",  # Light gray
                    fg="#000000",  # Black text
                    font=("Helvetica", 14, "bold"),
                    relief=tk.RAISED,
                    bd=3,
                    highlightthickness=0,
                    padx=25,
                    pady=12
                )

        self.current_tab = tab_id

    def switch_tab(self, tab_id):
        """Switch between tabs"""
        self.set_active_tab(tab_id)

        # Hide all content frames
        for tab in [self.record_tab, self.chat_tab, self.video_tab, self.process_tab, self.settings_tab]:
            tab.get_frame().pack_forget()

        # Show selected frame
        if tab_id == "record":
            self.record_tab.get_frame().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        elif tab_id == "chat":
            self.chat_tab.get_frame().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        elif tab_id == "videos":
            self.video_tab.get_frame().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        elif tab_id == "process":
            self.process_tab.get_frame().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        elif tab_id == "settings":
            self.settings_tab.get_frame().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def create_main_content(self):
        """Create main content area"""
        self.content_frame = tk.Frame(self.root, bg=COLORS["bg"])
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Create all tab content
        self.record_tab = RecordingTab(self.content_frame, self)
        self.record_tab.create_ui()

        self.chat_tab = ChatTab(self.content_frame, self, self.mem)
        self.chat_tab.create_ui()

        self.video_tab = VideoTab(self.content_frame, self, self.db_name)
        self.video_tab.create_ui()

        self.process_tab = ProcessMiningTab(self.content_frame, self, db_name="./db/input_events.db")
        self.process_tab.create_ui()

        self.settings_tab = SettingsTab(self.content_frame, self, self.db_name)
        self.settings_tab.create_ui()

        # Show record by default
        self.record_tab.get_frame().pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def load_video_list(self):
        """Load video list - delegate to video tab"""
        if hasattr(self, 'video_tab'):
            self.video_tab.load_video_list()


__all__ = ["MemScreenApp"]
