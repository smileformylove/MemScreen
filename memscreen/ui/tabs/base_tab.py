### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Base class for tab components"""

import tkinter as tk
from ..components.colors import COLORS, FONTS


class BaseTab:
    """Base class for all tabs"""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.root = app.root
        self.frame = None

    def create_ui(self):
        """Create the tab UI - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement create_ui()")

    def get_frame(self):
        """Return the main frame for this tab"""
        return self.frame

    def on_show(self):
        """Called when tab is shown"""
        pass

    def on_hide(self):
        """Called when tab is hidden"""
        pass


__all__ = ["BaseTab"]
