### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Search tab for searching screen memory"""

import tkinter as tk
from tkinter import scrolledtext

from .base_tab import BaseTab
from ..components.colors import COLORS, FONTS


class SearchTab(BaseTab):
    """Search screen memory tab"""

    def __init__(self, parent, app, mem):
        super().__init__(parent, app)
        self.mem = mem
        self.search_input = None
        self.search_results = None

    def create_ui(self):
        """Create search tab UI"""
        self.frame = tk.Frame(self.parent, bg=COLORS["bg"])

        # Search bar
        search_bar = tk.Frame(self.frame, bg=COLORS["surface"], height=80)
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
            font=("Helvetica", 14, "normal"),  # Larger font
            bg=COLORS["input_bg"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief=tk.SOLID,
            bd=3,
            highlightthickness=3,
            highlightbackground=COLORS["primary"],
            highlightcolor=COLORS["primary"]
        )
        self.search_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), pady=10, ipady=15)
        self.search_input.bind("<Return>", lambda e: self.perform_search())
        self.search_input.focus_set()  # Auto-focus for easy input

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
        results_frame = tk.Frame(self.frame, bg=COLORS["surface"])
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
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief=tk.FLAT,
            padx=20,
            pady=20
        )
        self.search_results.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        self.search_results.insert(tk.END, "Enter a search query above to find content in your screen recordings...")
        self.search_results.config(state=tk.DISABLED)

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
        results = self.mem.search(query=query, user_id="screenshot")

        self.search_results.config(state=tk.NORMAL)
        if results and 'results' in results and len(results['results']) > 0:
            for i, result in enumerate(results['results'][:10], 1):
                self.search_results.insert(tk.END, f"{i}. {result.get('memory', 'No memory')}\n\n")
        else:
            self.search_results.insert(tk.END, "No results found.\n")
        self.search_results.config(state=tk.DISABLED)


__all__ = ["SearchTab"]
