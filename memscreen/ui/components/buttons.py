### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Modern button component for MemScreen UI"""

import tkinter as tk
from .colors import COLORS, FONTS


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


__all__ = ["ModernButton"]
