### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Color constants for MemScreen UI"""

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

__all__ = ["COLORS", "FONTS"]
