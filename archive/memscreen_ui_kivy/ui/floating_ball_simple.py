#!/usr/bin/env python3
"""
Simple Floating Ball using Tkinter
Creates an independent floating window that's simpler and more reliable than native APIs
"""

import sys
import tkinter as tk
from threading import Thread
from typing import Optional, Callable


class FloatingBallWindow:
    """
    A simple floating ball window using Tkinter.

    This creates an independent window that floats on top of the main window.
    It's simpler and more reliable than native macOS APIs.
    """

    def __init__(self, presenter=None, position=None):
        self.presenter = presenter
        self.is_recording = False
        self.is_paused = False

        # Create a hidden root window first
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window

        # Create the ball window (Toplevel for independent window)
        self.window = tk.Toplevel(self.root)

        # Window configuration
        self.ball_size = 80
        self.window.geometry(f"{self.ball_size}x{self.ball_size}")

        # Position
        if position:
            x, y = position
        else:
            # Default to top-right corner
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = screen_width - self.ball_size - 20
            y = screen_height - self.ball_size - 20

        self.window.geometry(f"+{x}+{y}")

        # Window styling
        self.window.overrideredirect(True)  # Remove window decorations
        self.window.attributes('-topmost', True)  # Always on top
        self.window.attributes('-transparentcolor', '')  # Transparent background

        # Create canvas for drawing
        self.canvas = tk.Canvas(
            self.window,
            width=self.ball_size,
            height=self.ball_size,
            bg='systemTransparent' if sys.platform == 'darwin' else 'white',
            highlightthickness=0
        )
        self.canvas.pack()

        # Draw the ball
        self._draw_ball()

        # Mouse bindings for dragging
        self.window.bind('<Button-1>', self._on_mouse_down)
        self.window.bind('<B1-Motion>', self._on_mouse_drag)
        self.window.bind('<Button-3>' if sys.platform != 'darwin' else '<Button-2>',
                        self._on_right_click)

        # Drag state
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Callbacks
        self.on_stop_callback = None
        self.on_pause_callback = None
        self.on_main_window_callback = None

        # Make window visible
        self.window.deiconify()

        print(f"[FloatingBall] Created floating ball at ({x}, {y})")

    def _draw_ball(self):
        """Draw the circular ball"""
        self.canvas.delete("all")

        # Colors based on state
        if self.is_paused:
            color = "#FFB31A"  # Yellow
        elif self.is_recording:
            color = "#CC3333"  # Red
        else:
            color = "#9966BF"  # Purple

        # Draw outer glow (semi-transparent circle)
        self.canvas.create_oval(
            2, 2, self.ball_size - 2, self.ball_size - 2,
            fill=color,
            outline=color,
            stipple='gray50'  # Semi-transparent effect
        )

        # Draw main ball
        self.canvas.create_oval(
            4, 4, self.ball_size - 4, self.ball_size - 4,
            fill=color,
            outline=color
        )

        # Draw highlight
        self.canvas.create_oval(
            self.ball_size * 0.3, self.ball_size * 0.3,
            self.ball_size * 0.6, self.ball_size * 0.6,
            fill='white',
            outline='',
            stipple='gray25'
        )

        # Draw status icon
        self._draw_icon()

    def _draw_icon(self):
        """Draw status icon (circle or pause bars)"""
        if self.is_paused:
            # Draw pause bars (II)
            bar_width = 4
            bar_height = 20
            x1 = self.ball_size / 2 - 6
            x2 = self.ball_size / 2 + 2
            y = (self.ball_size - bar_height) / 2

            self.canvas.create_rectangle(
                x1, y, x1 + bar_width, y + bar_height,
                fill='white', outline=''
            )
            self.canvas.create_rectangle(
                x2, y, x2 + bar_width, y + bar_height,
                fill='white', outline=''
            )

        elif self.is_recording:
            # Draw recording dot (●)
            dot_size = 16
            x = (self.ball_size - dot_size) / 2
            y = (self.ball_size - dot_size) / 2

            self.canvas.create_oval(
                x, y, x + dot_size, y + dot_size,
                fill='white', outline=''
            )

        else:
            # Draw ready circle (○)
            circle_size = 16
            x = (self.ball_size - circle_size) / 2
            y = (self.ball_size - circle_size) / 2

            self.canvas.create_oval(
                x, y, x + circle_size, y + circle_size,
                outline='white', width=2
            )

    def _on_mouse_down(self, event):
        """Handle mouse down - start dragging"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def _on_mouse_drag(self, event):
        """Handle mouse drag - move window"""
        x = self.window.winfo_x() + event.x - self.drag_start_x
        y = self.window.winfo_y() + event.y - self.drag_start_y
        self.window.geometry(f"+{int(x)}+{int(y)}")

    def _on_right_click(self, event):
        """Handle right click - show menu"""
        # Create context menu
        menu = tk.Menu(self.window, tearoff=0)

        # Recording info
        if self.presenter:
            try:
                status = self.presenter.get_recording_status()
                menu.add_command(
                    label=f"Frames: {status['frame_count']}\nTime: {status['elapsed_time']:.1f}s",
                    state='disabled'
                )
            except:
                pass

        menu.add_separator()

        # Stop Recording
        menu.add_command(
            label="⏹ Stop Recording",
            command=self._stop_recording
        )

        # Pause/Resume
        if self.is_recording:
            pause_text = "⏸ Pause" if not self.is_paused else "▶ Resume"
            menu.add_command(
                label=pause_text,
                command=self._toggle_pause
            )

        # Main Window
        menu.add_command(
            label="🏠 Main Window",
            command=self._show_main_window
        )

        # Show menu at mouse position
        try:
            # Get global screen coordinates
            x = self.window.winfo_rootx() + event.x
            y = self.window.winfo_rooty() + event.y
            menu.tk_popup(x, y)
        except:
            # Fallback to window position
            menu.tk_popup(event.x_root, event.y_root)

    def _stop_recording(self):
        """Stop recording"""
        if self.presenter:
            self.presenter.stop_recording()
        if self.on_stop_callback:
            self.on_stop_callback()

    def _toggle_pause(self):
        """Toggle pause/resume"""
        self.is_paused = not self.is_paused
        self.set_recording_state(self.is_recording, self.is_paused)
        if self.on_pause_callback:
            self.on_pause_callback()

    def _show_main_window(self):
        """Show main window"""
        if self.on_main_window_callback:
            self.on_main_window_callback()

    def set_recording_state(self, is_recording, is_paused=False):
        """Update recording state"""
        self.is_recording = is_recording
        self.is_paused = is_paused
        self._draw_ball()

    def set_presenter(self, presenter):
        """Set the recording presenter"""
        self.presenter = presenter

    def close(self):
        """Close the floating ball window"""
        try:
            self.window.destroy()
            self.root.destroy()
        except:
            pass

    def run(self):
        """Run the Tkinter main loop"""
        self.root.mainloop()


def create_floating_ball(presenter=None, position=None):
    """
    Create a floating ball window.

    Args:
        presenter: RecordingPresenter instance
        position: Initial position as (x, y) tuple, defaults to top-right of screen

    Returns:
        FloatingBallWindow instance
    """
    ball = FloatingBallWindow(presenter=presenter, position=position)

    # Run Tkinter in a separate thread to avoid blocking
    def run_tkinter():
        try:
            ball.run()
        except Exception as e:
            print(f"[FloatingBall] Error in Tkinter thread: {e}")

    thread = Thread(target=run_tkinter, daemon=True)
    thread.start()

    return ball
