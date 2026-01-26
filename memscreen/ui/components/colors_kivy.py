### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Color scheme for MemScreen Kivy UI (Modern Material Design)"""

# Primary colors (Material Design)
PRIMARY_COLOR = [0.26, 0.63, 0.28, 1.0]      # Green - #42A071
SECONDARY_COLOR = [0.13, 0.59, 0.95, 1.0]    # Blue - #2296F2

# Background colors
BG_COLOR = [0.98, 0.98, 0.98, 1.0]           # Light gray background
SURFACE_COLOR = [1.0, 1.0, 1.0, 1.0]         # White surface
INPUT_BG_COLOR = [0.95, 0.95, 0.95, 1.0]     # Input background

# Text colors
TEXT_COLOR = [0.13, 0.13, 0.13, 1.0]         # Dark text
TEXT_LIGHT = [0.53, 0.53, 0.53, 1.0]         # Light gray text
TEXT_MUTED = [0.70, 0.70, 0.70, 1.0]         # Muted text

# Status colors
SUCCESS_COLOR = [0.24, 0.71, 0.54, 1.0]      # Green
WARNING_COLOR = [0.95, 0.64, 0.27, 1.0]      # Orange/Amber
ERROR_COLOR = [0.91, 0.30, 0.24, 1.0]        # Red
INFO_COLOR = [0.25, 0.64, 0.87, 1.0]         # Light blue

# Button colors
BUTTON_PRIMARY = [0.42, 0.76, 0.87, 1.0]     # Blue button
BUTTON_SUCCESS = [0.53, 0.93, 0.42, 1.0]     # Green button
BUTTON_DANGER = [0.92, 0.65, 0.65, 1.0]      # Red button
BUTTON_WARNING = [0.93, 0.84, 0.30, 1.0]     # Yellow button
BUTTON_TEXT_COLOR = [0.0, 0.0, 0.0, 1.0]     # Black text on buttons

# Process mining colors
PROCESSING_TEXT = [0.13, 0.59, 0.95, 1.0]    # Blue for processing status

# Chat colors
CHAT_USER_BG = [0.22, 0.22, 0.22, 1.0]       # User message bg
CHAT_AI_BG = [0.17, 0.17, 0.17, 1.0]         # AI message bg

# Keep old aliases for compatibility
PRIMARY = (0.13, 0.59, 0.95)
SECONDARY = (0.91, 0.30, 0.24)
BG_DARK = (0.12, 0.12, 0.12, 1.0)
BG_CARD = (0.17, 0.17, 0.17, 1.0)
BG_SURFACE = (0.22, 0.22, 0.22, 1.0)
BG_INPUT = (0.25, 0.25, 0.25, 1.0)
TEXT_PRIMARY = (1.0, 1.0, 1.0, 1.0)
TEXT_SECONDARY = (0.7, 0.7, 0.7, 1.0)
TEXT_DISABLED = (0.5, 0.5, 0.5, 1.0)
TEXT_HINT = (0.4, 0.4, 0.4, 1.0)
SUCCESS = (0.13, 0.77, 0.28, 1.0)
WARNING = (0.93, 0.68, 0.13, 1.0)
ERROR = (0.91, 0.30, 0.24, 1.0)
INFO = (0.25, 0.64, 0.87, 1.0)
RECORDING_ACTIVE = (0.91, 0.30, 0.24, 1.0)
RECORDING_IDLE = (0.13, 0.77, 0.28, 1.0)
USER_MESSAGE_BG = (0.22, 0.22, 0.22, 1.0)
AI_MESSAGE_BG = (0.17, 0.17, 0.17, 1.0)
USER_TEXT = (0.13, 0.59, 0.95, 1.0)
AI_TEXT = (0.91, 0.30, 0.24, 1.0)
BUTTON_GREEN = (0.53, 0.93, 0.42, 1.0)
BUTTON_RED = (0.92, 0.65, 0.65, 1.0)
BUTTON_BLUE = (0.42, 0.76, 0.87, 1.0)
BUTTON_YELLOW = (0.93, 0.84, 0.30, 1.0)
BUTTON_GRAY = (0.74, 0.74, 0.74, 1.0)
ACCENT_PURPLE = (0.61, 0.35, 0.71, 1.0)
ACCENT_TEAL = (0.26, 0.74, 0.83, 1.0)
ACCENT_ORANGE = (1.0, 0.6, 0.0, 1.0)
NAV_ACTIVE = (0.82, 0.84, 0.84, 1.0)
NAV_INACTIVE = (0.9, 0.9, 0.9, 1.0)
NAV_HOVER = (0.95, 0.95, 0.95, 1.0)
OVERLAY_DARK = (0.0, 0.0, 0.0, 0.7)
OVERLAY_LIGHT = (1.0, 1.0, 1.0, 0.1)
PROCESS_KEYBOARD = (0.23, 0.51, 0.96, 1.0)
PROCESS_MOUSE = (0.06, 0.69, 0.53, 1.0)
PROCESS_TIMESTAMP = (0.42, 0.42, 0.42, 1.0)
GRADIENT_START = (0.13, 0.59, 0.95, 1.0)
GRADIENT_END = (0.09, 0.45, 0.72, 1.0)
BORDER_LIGHT = (1.0, 1.0, 1.0, 0.2)
BORDER_DARK = (0.0, 0.0, 0.0, 0.1)
SHADOW_LIGHT = (0.0, 0.0, 0.0, 0.05)
SHADOW_DARK = (0.0, 0.0, 0.0, 0.2)

# Helper functions
def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return (
        int(hex_color[0:2], 16) / 255.0,
        int(hex_color[2:4], 16) / 255.0,
        int(hex_color[4:6], 16) / 255.0,
        1.0
    )

def rgba(r, g, b, a=1.0):
    """Create RGBA tuple"""
    return (r/255.0, g/255.0, b/255.0, a)
