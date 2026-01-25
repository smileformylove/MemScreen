### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT               ###

"""Color constants for MemScreen UI - Dark Theme for Better Contrast"""

# Dark theme for better contrast and easier viewing
COLORS = {
    "primary": "#6366F1",           # Indigo
    "primary_dark": "#4F46E5",      # Darker indigo
    "primary_light": "#818CF8",     # Light indigo
    "secondary": "#0891B2",         # Cyan
    "accent": "#F59E0B",            # Amber
    "bg": "#1F2937",               # Dark gray background (main)
    "surface": "#374151",           # Medium gray surface (panels)
    "surface_alt": "#4B5563",       # Lighter gray surface (hover)
    "text": "#F9FAFB",              # Off-white text (high contrast)
    "text_light": "#D1D5DB",        # Light gray text
    "text_muted": "#9CA3AF",        # Muted gray text
    "border": "#4B5563",            # Border
    "border_light": "#6B7280",      # Light border
    "chat_user_bg": "#1E3A8A",      # Dark blue for user
    "chat_ai_bg": "#064E3B",        # Dark teal for AI
    "success": "#10B981",           # Green
    "warning": "#F59E0B",           # Amber
    "error": "#EF4444",             # Red
    "info": "#3B82F6",              # Blue
    "input_bg": "#111827",          # Very dark for input fields
    "input_focus": "#374151",       # Input focus state
}

# Font definitions
FONTS = {
    "heading": ("Helvetica", 16, "bold"),
    "subheading": ("Helvetica", 14, "bold"),
    "body": ("Helvetica", 11, "normal"),
    "small": ("Helvetica", 10, "normal"),
    "mono": ("Consolas", 10, "normal"),
}

# Gradient definitions for modern UI
GRADIENTS = {
    "primary": ["#6366F1", "#818CF8", "#A5B4FC"],           # Indigo gradient
    "secondary": ["#0891B2", "#06B6D4", "#22D3EE"],          # Cyan gradient
    "success": ["#10B981", "#34D399", "#6EE7B7"],            # Green gradient
    "warning": ["#F59E0B", "#FBBF24", "#FCD34D"],            # Amber gradient
    "error": ["#EF4444", "#F87171", "#FCA5A5"],              # Red gradient
    "info": ["#3B82F6", "#60A5FA", "#93C5FD"],               # Blue gradient
}

# Status color themes
STATUS_COLORS = {
    "idle":      {"bg": "#374151", "text": "#9CA3AF"},
    "active":    {"bg": "#1E3A8A", "text": "#93C5FD"},
    "busy":      {"bg": "#78350F", "text": "#FCD34D"},
    "success":   {"bg": "#064E3B", "text": "#6EE7B7"},
    "warning":   {"bg": "#78350F", "text": "#FCD34D"},
    "error":     {"bg": "#7F1D1D", "text": "#FCA5A5"},
    "recording": {"bg": "#7F1D1D", "text": "#FCA5A5"},
    "processing": {"bg": "#1E3A8A", "text": "#93C5FD"},
}

# Shadow presets
SHADOWS = {
    "sm":   {"alpha": 0.1, "offset": (1, 1), "blur": 2},
    "md":   {"alpha": 0.15, "offset": (2, 2), "blur": 4},
    "lg":   {"alpha": 0.2, "offset": (4, 4), "blur": 8},
    "xl":   {"alpha": 0.25, "offset": (6, 6), "blur": 12},
}

SHADOW_PRESETS = {
    "button": {"shadow": SHADOWS["md"]},
    "card": {"shadow": SHADOWS["lg"]},
}

# Hover colors for interactive elements
HOVER_COLORS = {
    "primary": {"bg": "#4F46E5", "text": "white"},
    "secondary": {"bg": "#06B6D4", "text": "white"},
    "success": {"bg": "#10B981", "text": "white"},
    "warning": {"bg": "#F59E0B", "text": "white"},
    "error": {"bg": "#EF4444", "text": "white"},
}

# Animation color schemes
ANIMATION_COLORS = {
    "pulse": ["#EF4444", "#F87171", "#FCA5A5", "#FECACA"],   # For pulsing indicators
    "typing": ["#6B7280", "#9CA3AF", "#D1D5DB"],             # For typing indicator
    "loading": ["#6366F1", "#818CF8", "#A5B4FC"],            # For loading spinners
    "progress": ["#10B981", "#34D399", "#6EE7B7"],            # For progress bars
    "shimmer": ["#374151", "#4B5563", "#6B7280"],              # For skeleton loading
}
