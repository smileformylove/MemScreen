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

# Gradient definitions for modern UI
GRADIENTS = {
    "primary": ["#4F46E5", "#818CF8", "#A5B4FC"],           # Indigo gradient
    "secondary": ["#0891B2", "#06B6D4", "#22D3EE"],          # Cyan gradient
    "success": ["#10B981", "#34D399", "#6EE7B7"],            # Green gradient
    "warning": ["#F59E0B", "#FBBF24", "#FCD34D"],            # Amber gradient
    "error": ["#EF4444", "#F87171", "#FCA5A5"],              # Red gradient
    "info": ["#3B82F6", "#60A5FA", "#93C5FD"],               # Blue gradient
    "sunset": ["#4F46E5", "#EC4899", "#F59E0B"],             # Sunset gradient
    "ocean": ["#0891B2", "#3B82F6", "#6366F1"],              # Ocean gradient
    "forest": ["#059669", "#10B981", "#34D399"],             # Forest gradient
    "purple": ["#7C3AED", "#8B5CF6", "#A78BFA"],             # Purple gradient
}

# Animation color schemes
ANIMATION_COLORS = {
    "pulse": ["#EF4444", "#F87171", "#FCA5A5", "#FECACA"],   # For pulsing indicators
    "typing": ["#6B7280", "#9CA3AF", "#D1D5DB"],             # For typing indicator
    "loading": ["#4F46E5", "#818CF8", "#A5B4FC"],            # For loading spinners
    "progress": ["#10B981", "#34D399", "#6EE7B7"],           # For progress bars
    "shimmer": ["#F3F4F6", "#E5E7EB", "#D1D5DB", "#E5E7EB", "#F3F4F6"],  # For shimmer effect
}

# Status color variations
STATUS_COLORS = {
    "idle": {
        "bg": "#F3F4F6",
        "text": "#6B7280",
        "border": "#E5E7EB",
        "icon": "#9CA3AF",
    },
    "active": {
        "bg": "#EEF2FF",
        "text": "#4F46E5",
        "border": "#818CF8",
        "icon": "#4F46E5",
    },
    "busy": {
        "bg": "#FEF2F2",
        "text": "#EF4444",
        "border": "#FCA5A5",
        "icon": "#EF4444",
    },
    "success": {
        "bg": "#ECFDF5",
        "text": "#10B981",
        "border": "#6EE7B7",
        "icon": "#10B981",
    },
    "warning": {
        "bg": "#FFFBEB",
        "text": "#F59E0B",
        "border": "#FCD34D",
        "icon": "#F59E0B",
    },
    "error": {
        "bg": "#FEF2F2",
        "text": "#EF4444",
        "border": "#FCA5A5",
        "icon": "#EF4444",
    },
    "recording": {
        "bg": "#FEF2F2",
        "text": "#DC2626",
        "border": "#F87171",
        "icon": "#DC2626",
    },
    "processing": {
        "bg": "#EEF2FF",
        "text": "#4F46E5",
        "border": "#818CF8",
        "icon": "#4F46E5",
    },
}

# Shadow colors for depth effects
SHADOWS = {
    "sm": {
        "color": "#000000",
        "alpha": 0.05,
        "offset": (0, 1),
        "blur": 2,
    },
    "md": {
        "color": "#000000",
        "alpha": 0.1,
        "offset": (0, 4),
        "blur": 6,
    },
    "lg": {
        "color": "#000000",
        "alpha": 0.15,
        "offset": (0, 10),
        "blur": 15,
    },
    "xl": {
        "color": "#000000",
        "alpha": 0.2,
        "offset": (0, 20),
        "blur": 25,
    },
    "inner": {
        "color": "#000000",
        "alpha": 0.1,
        "offset": (0, 2),
        "blur": 4,
        "inset": True,
    },
}

# Shadow presets for common UI elements
SHADOW_PRESETS = {
    "button": SHADOWS["sm"],
    "card": SHADOWS["md"],
    "modal": SHADOWS["xl"],
    "dropdown": SHADOWS["lg"],
    "tooltip": SHADOWS["md"],
    "input": SHADOWS["sm"],
}

# Hover state color transitions
HOVER_COLORS = {
    "primary": {
        "default": COLORS["primary"],
        "hover": "#4338CA",
        "active": "#3730A3",
        "disabled": "#A5B4FC",
    },
    "secondary": {
        "default": COLORS["secondary"],
        "hover": "#0E7490",
        "active": "#155E75",
        "disabled": "#67E8F9",
    },
    "success": {
        "default": COLORS["success"],
        "hover": "#059669",
        "active": "#047857",
        "disabled": "#6EE7B7",
    },
    "warning": {
        "default": COLORS["warning"],
        "hover": "#D97706",
        "active": "#B45309",
        "disabled": "#FCD34D",
    },
    "error": {
        "default": COLORS["error"],
        "hover": "#DC2626",
        "active": "#B91C1C",
        "disabled": "#FCA5A5",
    },
}

# Overlay colors
OVERLAYS = {
    "light": "rgba(255, 255, 255, 0.8)",
    "medium": "rgba(255, 255, 255, 0.5)",
    "dark": "rgba(0, 0, 0, 0.5)",
    "darker": "rgba(0, 0, 0, 0.7)",
}

# Border radius presets
BORDER_RADIUS = {
    "none": 0,
    "sm": 4,
    "md": 8,
    "lg": 12,
    "xl": 16,
    "full": 9999,
}

# Spacing presets
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
    "2xl": 48,
    "3xl": 64,
}

# Font settings
FONTS = {
    "title": ("Segoe UI", 24, "bold"),
    "heading": ("Segoe UI", 16, "bold"),
    "body": ("Segoe UI", 11),
    "small": ("Segoe UI", 9),
    "code": ("Consolas", 10),
}

__all__ = [
    "COLORS",
    "GRADIENTS",
    "ANIMATION_COLORS",
    "STATUS_COLORS",
    "SHADOWS",
    "SHADOW_PRESETS",
    "HOVER_COLORS",
    "OVERLAYS",
    "BORDER_RADIUS",
    "SPACING",
    "FONTS",
]
