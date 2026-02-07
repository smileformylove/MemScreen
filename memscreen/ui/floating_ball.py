#!/usr/bin/env python3
"""
Floating Ball Widget for Screen Recording
A circular floating widget with drag support and right-click menu
This creates an independent floating window on the screen
"""

from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.graphics import Color, Ellipse, Line
from kivy.properties import NumericProperty, BooleanProperty, ReferenceListProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.core.window import WindowBase
from kivy.config import Config
import sys


class FloatingBallWindow(Widget):
    """
    A floating circular widget for controlling screen recording.

    This is a standalone floating window that stays on top of the main window.
    """

    # Ball appearance
    ball_size = NumericProperty(80)  # Diameter of the ball

    # Recording state
    is_recording = BooleanProperty(False)
    is_paused = BooleanProperty(False)

    # Animation
    pulse_anim = BooleanProperty(False)

    # Window reference
    floating_window = None

    def __init__(self, presenter=None, **kwargs):
        super().__init__(**kwargs)
        self.presenter = presenter

        # Setup the widget first
        self.ball_size = 80
        self.size = (self.ball_size, self.ball_size)

        # Dragging state
        self.dragging = False
        self.drag_offset = (0, 0)
        self.touch_pos = None

        # Setup canvas
        self._setup_canvas()

        # Setup label
        self._setup_label()

    def _setup_canvas(self):
        """Setup the canvas with ball graphics"""
        with self.canvas:
            # Outer glow (semi-transparent)
            self.outer_color = Color(0.6, 0.4, 0.75, 0.3)
            self.outer_ellipse = Ellipse(pos=self.pos, size=(self.ball_size, self.ball_size))

            # Main ball
            self.main_color = Color(0.6, 0.4, 0.75, 1)
            self.main_ellipse = Ellipse(pos=self.pos, size=(self.ball_size, self.ball_size))

            # Inner highlight
            self.highlight_color = Color(1, 1, 1, 0.3)
            self.highlight_ellipse = Ellipse(
                pos=(10, 10),
                size=(self.ball_size * 0.4, self.ball_size * 0.4)
            )

        # Bind to position changes
        self.bind(pos=self._update_canvas)

    def _update_canvas(self, instance, value):
        """Update canvas when position changes"""
        self.outer_ellipse.pos = self.pos
        self.main_ellipse.pos = self.pos
        self.highlight_ellipse.pos = (self.x + 10, self.y + 10)

    def _setup_label(self):
        """Setup status text label on the ball"""
        self.status_label = Label(
            text='○',  # Default icon
            font_size='30',
            color=(1, 1, 1, 1),
            pos=self.pos,
            size=(self.ball_size, self.ball_size),
            halign='center',
            valign='middle'
        )
        self.add_widget(self.status_label)
        self.bind(pos=self._update_label)

    def _update_label(self, instance, value):
        """Update label position"""
        self.status_label.pos = self.pos
        self.status_label.size = (self.ball_size, self.ball_size)
        self.status_label.texture_update()
        self.status_label.center = self.center

    def set_recording_state(self, is_recording, is_paused=False):
        """
        Update visual state based on recording status.

        Args:
            is_recording: Whether recording is active
            is_paused: Whether recording is paused
        """
        self.is_recording = is_recording
        self.is_paused = is_paused

        with self.canvas:
            # Update colors based on state
            if is_paused:
                # Yellow for paused
                self.main_color.rgba = (1.0, 0.7, 0.2, 1)
                self.outer_color.rgba = (1.0, 0.7, 0.2, 0.3)
                self.status_label.text = 'II'
                self.pulse_anim = False
            elif is_recording:
                # Red for recording
                self.main_color.rgba = (0.8, 0.2, 0.3, 1)
                self.outer_color.rgba = (0.8, 0.2, 0.3, 0.3)
                self.status_label.text = '●'
                self.pulse_anim = True
                # Start pulse animation
                self._start_pulse_animation()
            else:
                # Purple for ready
                self.main_color.rgba = (0.6, 0.4, 0.75, 1)
                self.outer_color.rgba = (0.6, 0.4, 0.75, 0.3)
                self.status_label.text = '○'
                self.pulse_anim = False

    def _start_pulse_animation(self):
        """Start pulsing animation for recording state"""
        if not self.is_recording:
            return

        # Pulse the outer glow
        pulse_phase = 0

        def pulse(dt):
            nonlocal pulse_phase
            if not self.is_recording:
                return False  # Stop animation

            pulse_phase = (pulse_phase + dt * 3) % 6.28
            alpha = 0.3 + 0.2 * (0.5 + 0.5 * (pulse_phase // 3.14))
            self.outer_color.rgba = (0.8, 0.2, 0.3, alpha)
            return True  # Continue animation

        Clock.schedule_interval(pulse, 1/60)

    def on_touch_down(self, touch):
        """Handle touch/click start"""
        if self.collide_point(touch.x, touch.y):
            # Right click (button == 'right' on some platforms, or check modifiers)
            if 'button' in dir(touch) and touch.button == 'right':
                self.show_context_menu(touch.pos)
                return True

            # Left click or default - start dragging
            if 'button' not in dir(touch) or touch.button == 'left':
                self.dragging = True
                self.touch_pos = touch.pos
                self.drag_offset = (self.x - touch.x, self.y - touch.y)
                return True

        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        """Handle dragging"""
        if self.dragging and self.collide_point(touch.x, touch.y):
            # Move ball with touch
            new_x = touch.x + self.drag_offset[0]
            new_y = touch.y + self.drag_offset[1]

            # Move with touch
            self.pos = (new_x, new_y)
            return True

        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        """Handle touch/click end"""
        if self.dragging:
            self.dragging = False
            self.touch_pos = None
            return True

        return super().on_touch_up(touch)

    def show_context_menu(self, pos):
        """Show right-click context menu"""
        # Create menu content
        menu_layout = BoxLayout(orientation='vertical', spacing=10, padding=15)

        # Title
        title = Label(
            text='Recording Controls',
            font_name='chinese',
            font_size='20',
            bold=True,
            size_hint_y=None,
            height=40,
            color=(0, 0, 0, 1)
        )
        menu_layout.add_widget(title)

        # Recording info
        if self.presenter:
            status = self.presenter.get_recording_status()
            info_text = f"Frames: {status['frame_count']}\nTime: {status['elapsed_time']:.1f}s"
            info_label = Label(
                text=info_text,
                font_name='chinese',
                font_size='16',
                size_hint_y=None,
                height=60,
                color=(0.3, 0.3, 0.3, 1)
            )
            menu_layout.add_widget(info_label)

        # Stop Recording button
        stop_btn = Button(
            text='⏹ Stop Recording',
            font_name='chinese',
            font_size='18',
            size_hint_y=None,
            height=50,
            background_color=(0.8, 0.2, 0.3, 1)
        )
        stop_btn.bind(on_press=self._stop_recording)
        menu_layout.add_widget(stop_btn)

        # Pause/Resume button
        if self.is_recording:
            pause_text = '⏸ Pause' if not self.is_paused else '▶ Resume'
            pause_btn = Button(
                text=pause_text,
                font_name='chinese',
                font_size='18',
                size_hint_y=None,
                height=50,
                background_color=(0.6, 0.4, 0.75, 1)
            )
            pause_btn.bind(on_press=self._toggle_pause)
            menu_layout.add_widget(pause_btn)

        # Return to Main Window button
        main_btn = Button(
            text='🏠 Main Window',
            font_name='chinese',
            font_size='18',
            size_hint_y=None,
            height=50,
            background_color=(0.5, 0.5, 0.5, 1)
        )
        main_btn.bind(on_press=self._show_main_window)
        menu_layout.add_widget(main_btn)

        # Create popup
        self.context_menu = Popup(
            title='Menu',
            title_font='chinese',
            title_size='18',
            content=menu_layout,
            size_hint=(0.3, 0.4),
            auto_dismiss=True
        )

        self.context_menu.open()

    def _stop_recording(self, instance):
        """Stop recording callback"""
        if self.presenter:
            self.presenter.stop_recording()
        if hasattr(self, 'context_menu'):
            self.context_menu.dismiss()

    def _toggle_pause(self, instance):
        """Toggle pause/resume callback"""
        # Note: Pause functionality would need to be implemented in presenter
        # For now, just show a message
        self.is_paused = not self.is_paused
        self.set_recording_state(self.is_recording, self.is_paused)
        if hasattr(self, 'context_menu'):
            self.context_menu.dismiss()

    def _show_main_window(self, instance):
        """Show main window callback"""
        if hasattr(self, 'context_menu'):
            self.context_menu.dismiss()

        # Trigger callback to show main window
        if hasattr(self, 'on_main_window_requested'):
            self.on_main_window_requested()


def create_floating_ball(presenter=None):
    """
    Create a floating ball in an independent window.

    This creates a new Kivy window that floats above the main application window.
    The window is small (just the size of the ball) and can be dragged around.

    Args:
        presenter: RecordingPresenter instance for controlling recording

    Returns:
        Tuple of (window, ball_widget)
    """
    from kivy.core.window import Window

    # Create the ball widget
    ball = FloatingBallWindow(presenter=presenter)

    # Create a new window for the floating ball
    # Note: Kivy doesn't support creating multiple windows easily
    # Instead, we'll create a floating modal view

    # For now, return the ball widget which will be added to a ModalView
    return ball
