### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Modern button component for MemScreen UI"""

import tkinter as tk
import time
from .colors import COLORS, FONTS, HOVER_COLORS, SHADOW_PRESETS, GRADIENTS


class ModernButton(tk.Canvas):
    """Custom modern button with gradient effect and animations"""

    def __init__(self, parent, text, command=None, icon=None, style="primary",
                 enabled=True, loading=False, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self.text = text
        self.command = command
        self.icon = icon
        self.style = style
        self.enabled = enabled
        self.loading = loading
        self.hovered = False
        self.pressed = False
        self.animation_progress = 0.0
        self.ripples = []
        self.shadow_offset = 2

        # Set colors based on style with hover states
        if style in HOVER_COLORS:
            color_scheme = HOVER_COLORS[style]
            self.default_color = color_scheme["default"]
            self.hover_color = color_scheme["hover"]
            self.active_color = color_scheme["active"]
            self.disabled_color = color_scheme["disabled"]
        else:
            self.default_color = COLORS.get(style, COLORS["primary"])
            self.hover_color = COLORS.get(f"{style}_dark", self.default_color)
            self.active_color = self.default_color
            self.disabled_color = COLORS["border"]

        self.bg_color = self.default_color if self.enabled else self.disabled_color
        self.text_color = "white" if style in ["primary", "secondary", "success", "error", "warning"] else COLORS["text"]

        # Get gradient colors
        self.gradient_colors = GRADIENTS.get(style, [self.default_color])

        # Configure shadow
        shadow = SHADOW_PRESETS.get("button", SHADOW_PRESETS["card"])
        self.shadow_config = shadow

        self.configure(bg=parent.cget("bg"))

        # Bind events
        if self.enabled:
            self.bind("<Enter>", self.on_enter)
            self.bind("<Leave>", self.on_leave)
            self.bind("<Button-1>", self.on_press)
            self.bind("<ButtonRelease-1>", self.on_release)

        # Initial draw
        self.after(100, self.draw_button)

    def draw_button(self):
        """Draw the button with all effects"""
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 1 or height <= 1:
            self.after(100, self.draw_button)
            return

        # Apply pressed effect
        y_offset = self.shadow_offset if self.pressed else 0
        shadow_y_offset = self.shadow_config["offset"][1] if not self.pressed else 1

        # Draw shadow
        shadow_alpha = int(self.shadow_config["alpha"] * 255)
        shadow_color = f"#{shadow_alpha:02x}{shadow_alpha:02x}{shadow_alpha:02x}"

        # Simulated shadow (darker rectangle offset)
        if not self.pressed:
            shadow_y = shadow_y_offset + 2
            self.create_rounded_rect(
                2, shadow_y, width + 2, height + shadow_y,
                radius=8, fill="#E5E7EB", outline=""
            )

        # Draw main button with gradient effect
        self._draw_gradient_button(0, y_offset, width, height - y_offset)

        # Draw ripple effects
        self._draw_ripples()

        # Draw loading spinner if loading
        if self.loading:
            self._draw_loading_spinner(width, height)

        # Draw text or icon
        if not self.loading:
            text_color = self.text_color if self.enabled else COLORS["text_muted"]
            self.create_text(
                width/2, (height - y_offset)/2 + y_offset,
                text=self.text,
                fill=text_color,
                font=FONTS["body"]
            )

    def _draw_gradient_button(self, x, y, width, height):
        """Draw button with gradient effect"""
        # For simplicity, we'll use the current color based on state
        current_color = self.bg_color

        # Add hover shine effect
        if self.hovered and not self.pressed and self.enabled:
            shine_y = y + height * 0.3
            self.create_rounded_rect(
                x, y, width, height,
                radius=8,
                fill=current_color,
                outline=""
            )
            # Add shine
            self.create_rounded_rect(
                x + 2, shine_y, width - 2, shine_y + height * 0.2,
                radius=4,
                fill="white",
                outline="",
                stipple="gray25"
            )
        else:
            self.create_rounded_rect(
                x, y, width, height,
                radius=8,
                fill=current_color,
                outline=""
            )

    def _draw_ripples(self):
        """Draw all active ripple effects"""
        current_time = time.time()

        # Update and draw ripples
        active_ripples = []
        for ripple in self.ripples:
            ripple_x, ripple_y, start_time = ripple
            elapsed = current_time - start_time
            duration = 0.6  # 600ms

            if elapsed < duration:
                progress = elapsed / duration
                max_radius = max(self.winfo_width(), self.winfo_height()) * 0.8
                radius = int(max_radius * progress)
                alpha = int(255 * (1 - progress))

                # Draw ripple circle
                self.create_oval(
                    ripple_x - radius, ripple_y - radius,
                    ripple_x + radius, ripple_y + radius,
                    outline="white",
                    width=2
                )
                active_ripples.append(ripple)

        self.ripples = active_ripples

        # Schedule next update if there are ripples
        if self.ripples:
            self.after(30, self.draw_button)

    def _draw_loading_spinner(self, width, height):
        """Draw animated loading spinner"""
        import math

        center_x = width / 2
        center_y = (height - self.shadow_offset) / 2 + self.shadow_offset
        radius = 10
        num_dots = 8

        # Animate rotation
        self.animation_progress = (self.animation_progress + 0.15) % (2 * math.pi)

        for i in range(num_dots):
            angle = (2 * math.pi * i / num_dots) + self.animation_progress
            dot_x = center_x + radius * math.cos(angle)
            dot_y = center_y + radius * math.sin(angle)

            # Calculate opacity based on position
            progress = (i / num_dots + self.animation_progress / (2 * math.pi)) % 1.0
            gray_value = int(200 + 55 * (1 - progress))
            color = f"#{gray_value:02x}{gray_value:02x}{gray_value:02x}"

            self.create_oval(
                dot_x - 2, dot_y - 2,
                dot_x + 2, dot_y + 2,
                fill=color,
                outline=""
            )

        # Schedule next frame
        self.after(50, self.draw_button)

    def create_rounded_rect(self, x1, y1, x2, y2, radius=8, **kwargs):
        """Create a rounded rectangle"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, **kwargs, smooth=True)

    def on_enter(self, event):
        """Handle mouse enter with smooth color transition"""
        if not self.enabled or self.loading:
            return

        self.hovered = True
        self._animate_color_transition(self.bg_color, self.hover_color, 150)

    def on_leave(self, event):
        """Handle mouse leave"""
        if not self.enabled or self.loading:
            return

        self.hovered = False
        self.pressed = False
        self._animate_color_transition(self.bg_color, self.default_color, 150)

    def on_press(self, event):
        """Handle button press"""
        if not self.enabled or self.loading:
            return

        self.pressed = True
        self.bg_color = self.active_color

        # Add ripple effect
        self.ripples.append((event.x, event.y, time.time()))

        self.draw_button()

    def on_release(self, event):
        """Handle button release"""
        if not self.enabled or self.loading:
            return

        self.pressed = False
        self.bg_color = self.hover_color if self.hovered else self.default_color

        self.draw_button()

        # Execute command
        if self.command:
            self.command()

    def _animate_color_transition(self, from_color, to_color, duration_ms):
        """Animate color transition"""
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)

        from_rgb = hex_to_rgb(from_color)
        to_rgb = hex_to_rgb(to_color)

        start_time = time.time()

        def animate():
            elapsed = time.time() - start_time
            progress = min(elapsed / (duration_ms / 1000.0), 1.0)

            # Ease out cubic
            eased = 1 - pow(1 - progress, 3)

            current_rgb = tuple(
                int(from_rgb[i] + (to_rgb[i] - from_rgb[i]) * eased)
                for i in range(3)
            )
            self.bg_color = rgb_to_hex(current_rgb)
            self.draw_button()

            if progress < 1.0:
                self.after(16, animate)

        animate()

    def set_loading(self, loading: bool):
        """Set loading state"""
        self.loading = loading
        self.enabled = not loading
        self.draw_button()

    def set_enabled(self, enabled: bool):
        """Enable or disable button"""
        self.enabled = enabled
        self.bg_color = self.default_color if enabled else self.disabled_color
        self.draw_button()

    def set_text(self, text: str):
        """Update button text"""
        self.text = text
        self.draw_button()


class IconButton(tk.Canvas):
    """Icon-only button with hover effects"""

    def __init__(self, parent, icon, command=None, size=32, tooltip=None, **kwargs):
        super().__init__(parent, width=size, height=size, highlightthickness=0, **kwargs)
        self.icon = icon
        self.command = command
        self.size = size
        self.tooltip = tooltip
        self.hovered = False

        self.configure(bg=parent.cget("bg"))
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

        self.after(100, self.draw_button)

    def draw_button(self):
        self.delete("all")

        # Draw background circle on hover
        if self.hovered:
            padding = 4
            self.create_oval(
                padding, padding,
                self.size - padding, self.size - padding,
                fill=COLORS["surface_alt"],
                outline=""
            )

        # Draw icon text
        self.create_text(
            self.size / 2, self.size / 2,
            text=self.icon,
            fill=COLORS["text"],
            font=("Segoe UI", int(self.size * 0.4))
        )

    def on_enter(self, event):
        self.hovered = True
        self.draw_button()

        # Show tooltip if available
        if self.tooltip:
            self._show_tooltip()

    def on_leave(self, event):
        self.hovered = False
        self.draw_button()

        # Hide tooltip
        self._hide_tooltip()

    def on_click(self, event):
        if self.command:
            self.command()

    def _show_tooltip(self):
        """Show tooltip popup"""
        if not hasattr(self, '_tooltip_window'):
            self._tooltip_window = tk.Toplevel(self)
            self._tooltip_window.wm_overrideredirect(True)
            self._tooltip_window.wm_geometry(f"+{self.winfo_rootx() + self.size + 5}+{self.winfo_rooty()}")

            label = tk.Label(
                self._tooltip_window,
                text=self.tooltip,
                font=FONTS["small"],
                bg=COLORS["text"],
                fg="white",
                padx=8,
                pady=4
            )
            label.pack()

    def _hide_tooltip(self):
        """Hide tooltip popup"""
        if hasattr(self, '_tooltip_window'):
            self._tooltip_window.destroy()
            delattr(self, '_tooltip_window')


__all__ = ["ModernButton", "IconButton"]
