### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Settings tab for configuration"""

import tkinter as tk

from .base_tab import BaseTab
from ..components.colors import COLORS, FONTS


class SettingsTab(BaseTab):
    """Settings tab"""

    def __init__(self, parent, app, db_name):
        super().__init__(parent, app)
        self.db_name = db_name

    def create_ui(self):
        """Create settings tab UI"""
        self.frame = tk.Frame(self.parent, bg=COLORS["bg"])

        settings_content = tk.Frame(self.frame, bg=COLORS["surface"])
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
            ("🤖 AI Models", "Configure Ollama models",
             ["qwen3:1.7b - Fast & efficient", "qwen2.5vl:3b - Vision capable", "mxbai-embed-large - Embeddings"]),
            ("💾 Storage", "Database location", [self.db_name]),
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


__all__ = ["SettingsTab"]
