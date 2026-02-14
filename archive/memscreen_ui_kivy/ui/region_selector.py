### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT               ###

"""
Region Selector Widget for Kivy UI.

Provides drag-to-select functionality for choosing screen regions.
"""

from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Line
from kivy.properties import NumericProperty
from kivy.core.window import Window
from kivy.core.window import Keyboard
from typing import Optional, Tuple, Callable


class RegionSelector(Widget):
    """
    Full-screen overlay widget for drag-to-select region functionality.

    Users can drag on screen to select a rectangular region for recording.
    Press ESC or click Cancel button to exit without selecting.
    """

    selection_start_x = NumericProperty(0)
    selection_start_y = NumericProperty(0)
    selection_end_x = NumericProperty(0)
    selection_end_y = NumericProperty(0)

    def __init__(self, on_selection_callback: Optional[Callable] = None, **kwargs):
        """
        Initialize RegionSelector widget.

        Args:
            on_selection_callback: Function to call when selection is complete or cancelled
                                  Called with bbox tuple (left, top, right, bottom) or None if cancelled
            **kwargs: Additional Kivy widget arguments
        """
        super().__init__(**kwargs)

        self.selecting = False
        self.on_selection_callback = on_selection_callback

        # Track selection state
        self.has_selection = False
        self.current_bbox = None
        self.touch_start_pos = None  # Track initial touch position

        # Make widget full screen
        self.size = Window.size
        self.pos = (0, 0)

        # Create transparent overlay with selection rectangle
        with self.canvas:
            # Semi-transparent purple fill for selected area
            self.color = Color(0.6, 0.4, 0.75, 0.2)  # Purple with low alpha
            self.rect = Rectangle(pos=self.pos, size=self.size)

            # Solid purple border for selection
            self.line_color = Color(0.6, 0.4, 0.75, 1)  # Solid purple
            self.border = Line(rectangle=[0, 0, 0, 0], width=2)

            # Crosshair guide lines (faint)
            self.guide_color = Color(0.6, 0.4, 0.75, 0.3)  # Faint purple
            self.guides = Line(points=[], width=1)

        # Make widget capture all touches
        self.size_hint = (None, None)

        # Request keyboard to handle ESC key
        self._keyboard = Window.request_keyboard(
            self._on_keyboard_closed,
            self
        )
        self._keyboard.bind(on_key_down=self._on_key_down)

    def _on_keyboard_closed(self):
        """Called when keyboard is closed"""
        self._keyboard = None

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        """Handle keyboard key down events"""
        if keycode[1] == 'escape':
            # ESC pressed - exit region selector
            print("[RegionSelector] ESC pressed, exiting region selector")
            if self.on_selection_callback:
                self.on_selection_callback(None)
            self._remove_overlay()
            return True
        return False

    def _remove_overlay(self):
        """Remove this overlay from the window"""
        # Release keyboard
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_key_down)
            self._keyboard.release()
            self._keyboard = None

        # Remove from window
        if self.parent:
            self.parent.remove_widget(self)
        print("[RegionSelector] Overlay removed")

    def on_touch_down(self, touch):
        """
        Handle touch down event - start selection.

        Args:
            touch: Kivy touch object
        """
        if self.collide_point(*touch.pos):
            # Record touch start position to distinguish click vs drag
            self.touch_start_pos = (touch.x, touch.y)
            self.selection_start_x = touch.x
            self.selection_start_y = touch.y
            self.selection_end_x = touch.x
            self.selection_end_y = touch.y
            # Don't return True yet - wait to see if user is dragging or clicking
            # This allows clicks to pass through to buttons below

        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        """
        Handle touch move event - update selection rectangle.

        Args:
            touch: Kivy touch object
        """
        # Check if user has moved enough to consider it a drag (more than 5 pixels)
        if self.touch_start_pos:
            dx = abs(touch.x - self.touch_start_pos[0])
            dy = abs(touch.y - self.touch_start_pos[1])

            if dx > 5 or dy > 5:
                # This is a drag, not a click - start selecting
                if not self.selecting:
                    self.selecting = True
                    # Capture this touch by grabbing it
                    touch.grab(self)

        if self.selecting:
            self.selection_end_x = touch.x
            self.selection_end_y = touch.y
            self._update_selection()
            return True

        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        """
        Handle touch up event - complete selection.

        IMPORTANT: Does NOT close overlay - allows re-selection.
        Overlay is only closed when recording starts or ESC is pressed.

        Args:
            touch: Kivy touch object
        """
        # Clear touch start position
        self.touch_start_pos = None

        if self.selecting:
            self.selecting = False
            touch.ungrab(self)

            # Get final bbox
            bbox = self.get_normalized_bbox()

            # Call callback with result (may be None if too small)
            if bbox:
                # Valid selection - keep overlay open for re-selection!
                self.has_selection = True
                self.current_bbox = bbox
                print(f"[RegionSelector] Selected region: {bbox}")

                if self.on_selection_callback:
                    self.on_selection_callback(bbox)

                # DON'T call _remove_overlay() - keep overlay open!
            else:
                # Selection too small - allow user to try again
                print(f"[RegionSelector] Selection too small, please try again")
                # Clear the selection rectangle
                self.clear_selection()
                # Do NOT remove overlay - allow user to select again

            return bbox

        # If not selecting, let the touch pass through to buttons below
        return super().on_touch_up(touch)

    def _update_selection(self):
        """Draw selection rectangle with crosshair guides."""
        # Calculate rectangle dimensions
        x = min(self.selection_start_x, self.selection_end_x)
        y = min(self.selection_start_y, self.selection_end_y)
        width = abs(self.selection_end_x - self.selection_start_x)
        height = abs(self.selection_end_y - self.selection_start_y)

        # Update border rectangle
        # Kivy coordinates: (x, y, width, height)
        if width > 0 and height > 0:
            self.border.rectangle = [x, y, width, height]

            # Draw crosshair guides to screen edges
            center_x = x + width / 2
            center_y = y + height / 2

            self.guides.points = [
                center_x, 0, center_x, y,                      # Top vertical
                center_x, y + height, center_x, Window.size[1],  # Bottom vertical
                0, center_y, x, center_y,                      # Left horizontal
                x + width, center_y, Window.size[0], center_y   # Right horizontal
            ]
        else:
            self.guides.points = []

    def get_normalized_bbox(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Get selected region as normalized bbox tuple.

        Converts widget coordinates to screen coordinates and returns
        bbox as (left, top, right, bottom).

        Returns:
            Bbox tuple or None if selection is too small
        """
        # Get widget coordinates
        x1 = min(self.selection_start_x, self.selection_end_x)
        y1 = min(self.selection_start_y, self.selection_end_y)
        x2 = max(self.selection_start_x, self.selection_end_x)
        y2 = max(self.selection_start_y, self.selection_end_y)

        # Check minimum size (at least 50x50 pixels)
        if (x2 - x1) < 50 or (y2 - y1) < 50:
            print("[RegionSelector] Selection too small, ignoring")
            return None

        # Convert to screen coordinates
        # Note: This is a simplified conversion. For multi-monitor setups,
        # you may need to adjust based on monitor positions.
        try:
            # Get window position
            window = self.get_parent_window()

            if window:
                # Kivy Y-axis is inverted relative to screen
                # Screen Y = window.height - kivy_y
                screen_x1 = int(window.x + x1)
                screen_y1 = int(window.y + (window.height - y2))
                screen_x2 = int(window.x + x2)
                screen_y2 = int(window.y + (window.height - y1))

                return (screen_x1, screen_y1, screen_x2, screen_y2)

        except Exception as e:
            print(f"[RegionSelector] Error converting coordinates: {e}")

        # Fallback: return widget coordinates
        return (int(x1), int(y1), int(x2), int(y2))

    def clear_selection(self):
        """Clear the current selection and guides."""
        self.selection_start_x = 0
        self.selection_start_y = 0
        self.selection_end_x = 0
        self.selection_end_y = 0
        self.border.rectangle = [0, 0, 0, 0]
        self.guides.points = []  # Clear guide lines
        self.has_selection = False
        self.current_bbox = None
        self.touch_start_pos = None  # Clear touch start position

    def close_for_recording(self):
        """
        Close overlay when recording starts.
        Called externally by kivy_app when user clicks Start Recording.
        """
        print("[RegionSelector] Closing overlay for recording")
        self._remove_overlay()
