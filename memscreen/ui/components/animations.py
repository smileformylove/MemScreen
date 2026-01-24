### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT               ###

"""Animation utilities for MemScreen UI components"""

import tkinter as tk
import time
import math
from typing import Callable, Optional, Tuple, List, Any


# Animation timing constants (in milliseconds)
TIMING = {
    "instant": 50,
    "fast": 150,
    "normal": 300,
    "slow": 500,
    "slower": 750,
    "slowest": 1000,
}

# Easing functions for smooth animations
class Easing:
    """Easing functions for natural animation curves"""

    @staticmethod
    def linear(t: float) -> float:
        """Linear interpolation (no easing)"""
        return t

    @staticmethod
    def ease_in_quad(t: float) -> float:
        """Quadratic ease in (accelerating)"""
        return t * t

    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Quadratic ease out (decelerating)"""
        return t * (2 - t)

    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease in and out"""
        return 2 * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 2) / 2

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Cubic ease in"""
        return t * t * t

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease out"""
        return 1 - math.pow(1 - t, 3)

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease in and out"""
        return 4 * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 3) / 2

    @staticmethod
    def ease_out_elastic(t: float) -> float:
        """Elastic ease out with bounce effect"""
        c4 = (2 * math.pi) / 3
        return 0 if t == 0 else 1 if t == 1 else math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

    @staticmethod
    def ease_out_bounce(t: float) -> float:
        """Bounce ease out"""
        n1 = 7.5625
        d1 = 2.75

        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375


class ColorTransition:
    """Smooth color transition utilities"""

    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    @staticmethod
    def interpolate_color(color1: str, color2: str, progress: float) -> str:
        """Interpolate between two colors"""
        rgb1 = ColorTransition.hex_to_rgb(color1)
        rgb2 = ColorTransition.hex_to_rgb(color2)

        interpolated = tuple(
            int(rgb1[i] + (rgb2[i] - rgb1[i]) * progress)
            for i in range(3)
        )

        return ColorTransition.rgb_to_hex(interpolated)

    @staticmethod
    def get_gradient_colors(start_color: str, end_color: str, steps: int) -> List[str]:
        """Generate a list of gradient colors"""
        return [
            ColorTransition.interpolate_color(start_color, end_color, i / (steps - 1))
            for i in range(steps)
        ]


class Animator:
    """Main animation controller for UI components"""

    def __init__(self, widget: tk.Widget):
        """Initialize animator for a specific widget"""
        self.widget = widget
        self.active_animations = []
        self.animation_queue = []

    def fade_in(self, duration: int = TIMING["normal"], callback: Optional[Callable] = None):
        """Fade in animation"""
        if not hasattr(self.widget, 'alpha'):
            # Widget doesn't support alpha, simulate with color
            return

        def animate(start_time: float):
            elapsed = time.time() - start_time
            progress = min(elapsed / (duration / 1000.0), 1.0)
            eased_progress = Easing.ease_out_cubic(progress)

            try:
                self.widget.alpha(int(255 * eased_progress))
                if progress < 1.0:
                    self.widget.after(16, lambda: animate(start_time))
                else:
                    if callback:
                        callback()
            except:
                pass

        animate(time.time())

    def fade_out(self, duration: int = TIMING["normal"], callback: Optional[Callable] = None):
        """Fade out animation"""
        if not hasattr(self.widget, 'alpha'):
            return

        def animate(start_time: float):
            elapsed = time.time() - start_time
            progress = min(elapsed / (duration / 1000.0), 1.0)
            eased_progress = 1 - Easing.ease_in_cubic(progress)

            try:
                self.widget.alpha(int(255 * eased_progress))
                if progress < 1.0:
                    self.widget.after(16, lambda: animate(start_time))
                else:
                    if callback:
                        callback()
            except:
                pass

        animate(time.time())

    def slide_in(self, direction: str = "left", distance: int = 100, duration: int = TIMING["normal"],
                callback: Optional[Callable] = None):
        """Slide in animation from specified direction"""
        widget_width = self.widget.winfo_width()
        widget_height = self.widget.winfo_height()

        # Set initial position
        if direction == "left":
            start_x = -widget_width
            start_y = 0
        elif direction == "right":
            start_x = distance
            start_y = 0
        elif direction == "top":
            start_x = 0
            start_y = -widget_height
        elif direction == "bottom":
            start_x = 0
            start_y = distance
        else:
            start_x = 0
            start_y = 0

        def animate_step(progress: float):
            try:
                # For canvas-based widgets, we can use offsets
                if hasattr(self.widget, 'xview'):
                    offset_x = int(start_x * (1 - progress))
                    offset_y = int(start_y * (1 - progress))
                    self.widget.xview_moveto(offset_x / 1000)

                # For place geometry
                if self.widget.winfo_manager() == 'place':
                    current_x = int(start_x * (1 - progress))
                    current_y = int(start_y * (1 - progress))
                    self.widget.place(x=current_x, y=current_y)
            except:
                pass

        def animate(start_time: float):
            elapsed = time.time() - start_time
            progress = min(elapsed / (duration / 1000.0), 1.0)
            eased_progress = Easing.ease_out_cubic(progress)

            animate_step(eased_progress)

            if progress < 1.0:
                self.widget.after(16, lambda: animate(start_time))
            else:
                if callback:
                    callback()

        animate(time.time())

    def scale(self, from_scale: float, to_scale: float, duration: int = TIMING["normal"],
              callback: Optional[Callable] = None):
        """Scale animation (works with canvas-based widgets)"""
        if not isinstance(self.widget, tk.Canvas):
            return

        def animate(start_time: float):
            elapsed = time.time() - start_time
            progress = min(elapsed / (duration / 1000.0), 1.0)
            eased_progress = Easing.ease_out_elastic(progress)

            current_scale = from_scale + (to_scale - from_scale) * eased_progress

            # Redraw with new scale
            if hasattr(self.widget, 'redraw_with_scale'):
                self.widget.redraw_with_scale(current_scale)

            if progress < 1.0:
                self.widget.after(16, lambda: animate(start_time))
            else:
                if callback:
                    callback()

        animate(time.time())

    def color_transition(self, from_color: str, to_color: str, duration: int = TIMING["normal"],
                        callback: Optional[Callable] = None):
        """Smooth color transition animation"""
        def animate(start_time: float):
            elapsed = time.time() - start_time
            progress = min(elapsed / (duration / 1000.0), 1.0)
            eased_progress = Easing.ease_in_out_quad(progress)

            current_color = ColorTransition.interpolate_color(from_color, to_color, eased_progress)

            try:
                if hasattr(self.widget, 'config'):
                    # Try to configure background
                    try:
                        self.widget.config(bg=current_color)
                    except:
                        pass

                    # Try to configure foreground
                    try:
                        self.widget.config(fg=current_color)
                    except:
                        pass

                # Special handling for Canvas
                if isinstance(self.widget, tk.Canvas) and hasattr(self.widget, 'update_animation_color'):
                    self.widget.update_animation_color(current_color)

            except:
                pass

            if progress < 1.0:
                self.widget.after(16, lambda: animate(start_time))
            else:
                if callback:
                    callback()

        animate(time.time())

    def pulse(self, scale_factor: float = 1.05, duration: int = TIMING["normal"]):
        """Pulse animation (scale up and down)"""
        def animate_pulse():
            # Scale up
            self.scale(1.0, scale_factor, duration // 2, lambda: None)
            # Scale down
            self.widget.after(duration // 2, lambda: self.scale(scale_factor, 1.0, duration // 2))

        animate_pulse()

    def shake(self, intensity: int = 5, duration: int = TIMING["fast"]):
        """Shake animation for error feedback"""
        original_x = self.widget.winfo_x()
        shakes = 4

        def animate_shake(shake_count: int):
            if shake_count >= shakes:
                # Return to original position
                try:
                    if self.widget.winfo_manager() == 'place':
                        self.widget.place(x=original_x)
                except:
                    pass
                return

            offset = intensity if shake_count % 2 == 0 else -intensity
            try:
                if self.widget.winfo_manager() == 'place':
                    self.widget.place(x=original_x + offset)
            except:
                pass

            delay = duration // shakes
            self.widget.after(delay, lambda: animate_shake(shake_count + 1))

        animate_shake(0)

    def stop_all(self):
        """Stop all active animations"""
        for animation in self.active_animations:
            if hasattr(animation, 'cancel'):
                animation.cancel()
        self.active_animations.clear()


class RippleEffect:
    """Material Design ripple effect for buttons"""

    @staticmethod
    def create_ripple(canvas: tk.Canvas, x: int, y: int, color: str, max_radius: int = 100,
                      duration: int = TIMING["normal"]):
        """Create a ripple effect on canvas"""
        ripple_id = canvas.create_oval(x, y, x, y, outline=color, width=2)

        def animate_ripple(start_time: float, current_radius: int = 0):
            elapsed = time.time() - start_time
            progress = min(elapsed / (duration / 1000.0), 1.0)
            eased_progress = Easing.ease_out_quad(progress)

            new_radius = int(current_radius + (max_radius - current_radius) * eased_progress)

            try:
                canvas.coords(ripple_id, x - new_radius, y - new_radius,
                            x + new_radius, y + new_radius)

                # Fade out by reducing width
                new_width = int(2 * (1 - eased_progress))
                canvas.itemconfig(ripple_id, width=max(1, new_width))

                if progress < 1.0:
                    canvas.after(16, lambda: animate_ripple(start_time, new_radius))
                else:
                    canvas.delete(ripple_id)
            except:
                try:
                    canvas.delete(ripple_id)
                except:
                    pass

        animate_ripple(time.time())


class ProgressAnimation:
    """Animated progress bars and indicators"""

    @staticmethod
    def create_pulsing_indicator(canvas: tk.Canvas, x: int, y: int, base_radius: int = 5,
                                  max_radius: int = 15, color: str = "#FF0000"):
        """Create a pulsing indicator (for recording status)"""
        # Create base circle
        base_id = canvas.create_oval(x - base_radius, y - base_radius,
                                     x + base_radius, y + base_radius,
                                     fill=color, outline=color)

        # Create pulsing rings
        rings = []

        def create_pulse_ring():
            ring_id = canvas.create_oval(x - base_radius, y - base_radius,
                                        x + base_radius, y + base_radius,
                                        outline=color, width=2)
            rings.append(ring_id)
            animate_ring(ring_id, time.time())

        def animate_ring(ring_id: int, start_time: float):
            try:
                elapsed = time.time() - start_time
                progress = elapsed / 1.5  # 1.5 seconds per pulse

                if progress >= 1.0:
                    canvas.delete(ring_id)
                    if ring_id in rings:
                        rings.remove(ring_id)
                    return

                current_radius = base_radius + (max_radius - base_radius) * progress
                alpha_factor = 1 - progress

                canvas.coords(ring_id, x - current_radius, y - current_radius,
                             x + current_radius, y + current_radius)

                # Schedule next frame
                canvas.after(30, lambda: animate_ring(ring_id, start_time))
            except:
                try:
                    canvas.delete(ring_id)
                except:
                    pass

        # Start creating rings periodically
        def pulse_loop():
            if canvas.winfo_exists():
                create_pulse_ring()
                canvas.after(500, pulse_loop)

        pulse_loop()

        return base_id

    @staticmethod
    def create_animated_progress(canvas: tk.Canvas, x: int, y: int, width: int, height: int,
                                  color: str = "#4F46E5", bg_color: str = "#E5E7EB"):
        """Create an animated progress bar"""
        # Background
        bg_id = canvas.create_rectangle(x, y, x + width, y + height,
                                       fill=bg_color, outline=bg_color)

        # Progress bar
        progress_id = canvas.create_rectangle(x, y, x, y + height,
                                             fill=color, outline=color)

        def update_progress(progress: float):
            """Update progress (0.0 to 1.0)"""
            try:
                canvas.coords(progress_id, x, y, x + int(width * progress), y + height)
            except:
                pass

        return bg_id, progress_id, update_progress


class TypingIndicator:
    """Animated typing indicator (three bouncing dots)"""

    @staticmethod
    def create(canvas: tk.Canvas, x: int, y: int, color: str = "#6B7280", dot_radius: int = 3):
        """Create typing indicator with 3 bouncing dots"""
        dots = []
        spacing = 12

        for i in range(3):
            dot_x = x + i * spacing
            dot_id = canvas.create_oval(dot_x - dot_radius, y - dot_radius,
                                       dot_x + dot_radius, y + dot_radius,
                                       fill=color, outline=color)
            dots.append(dot_id)

        def animate_dots():
            try:
                import math

                def update_dot(dot_index: int, start_time: float):
                    if not canvas.winfo_exists():
                        return

                    elapsed = time.time() - start_time
                    # Offset animation for each dot
                    offset = dot_index * 0.15
                    adjusted_time = elapsed + offset

                    # Bounce animation using sine
                    bounce = math.sin(adjusted_time * 4) * 3  # 3 pixel bounce

                    dot_x = x + dot_index * spacing
                    canvas.coords(dots[dot_index],
                                 dot_x - dot_radius, y - dot_radius - bounce,
                                 dot_x + dot_radius, y + dot_radius - bounce)

                    canvas.after(30, lambda: update_dot(dot_index, start_time))

                for i in range(3):
                    update_dot(i, time.time())

            except:
                pass

        animate_dots()

        return dots


class CounterAnimation:
    """Animated number counter"""

    @staticmethod
    def animate_count(label: tk.Label, from_value: int, to_value: int,
                      duration: int = TIMING["normal"], callback: Optional[Callable] = None):
        """Animate a number counter"""
        def animate(start_time: float):
            elapsed = time.time() - start_time
            progress = min(elapsed / (duration / 1000.0), 1.0)
            eased_progress = Easing.ease_out_quad(progress)

            current_value = int(from_value + (to_value - from_value) * eased_progress)

            try:
                label.config(text=str(current_value))
            except:
                pass

            if progress < 1.0:
                label.after(16, lambda: animate(start_time))
            else:
                try:
                    label.config(text=str(to_value))
                except:
                    pass
                if callback:
                    callback()

        animate(time.time())


class ScrollAnimator:
    """Smooth scroll animations"""

    @staticmethod
    def smooth_scroll(widget, target_position: float, duration: int = TIMING["normal"]):
        """Smoothly scroll to target position"""
        if not hasattr(widget, 'yview'):
            return

        start_position = widget.yview()[0]

        def animate(start_time: float):
            elapsed = time.time() - start_time
            progress = min(elapsed / (duration / 1000.0), 1.0)
            eased_progress = Easing.ease_out_cubic(progress)

            current_position = start_position + (target_position - start_position) * eased_progress

            try:
                widget.yview_moveto(current_position)
            except:
                pass

            if progress < 1.0:
                widget.after(16, lambda: animate(start_time))

        animate(time.time())

    @staticmethod
    def scroll_to_bottom(widget, duration: int = TIMING["fast"]):
        """Smoothly scroll to bottom"""
        if not hasattr(widget, 'yview'):
            return

        try:
            bottom_position = 1.0  # yview returns (top, bottom) as 0-1 range
            ScrollAnimator.smooth_scroll(widget, bottom_position, duration)
        except:
            pass


__all__ = [
    "TIMING",
    "Easing",
    "ColorTransition",
    "Animator",
    "RippleEffect",
    "ProgressAnimation",
    "TypingIndicator",
    "CounterAnimation",
    "ScrollAnimator",
]
