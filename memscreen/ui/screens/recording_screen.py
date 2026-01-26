### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Recording Screen - Screen capture functionality"""

from kivy.lang.builder import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.properties import NumericProperty
from kivy.animation import Animation

from .base_screen import BaseScreen
from ..components.colors_kivy import *
from ...presenters import RecordingPresenter


Builder.load_string('''
<RecordingScreen>:
    FloatLayout:
        # Header
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.12
            pos_hint: {"top": 1}
            canvas.before:
                Color:
                    rgba: 0.12, 0.12, 0.12, 1.0
                Rectangle:
                    pos: self.pos
                    size: self.size

            # Title
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: 60
                pos_hint: {"center_x": .5, "center_y": .5}
                spacing: 20

                # Title
                Label:
                    text: "🔴 Screen Recording"
                    font_size: 28
                    bold: True
                    color: 1, 1, 1, 1
                    size_hint_x: None
                    width: 250
                    text_size: self.ref('text_size') if hasattr(self, 'ref') else 28

                # Status indicator
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_x: None
                    width: 150
                    spacing: 10
                    pos_hint: {"center_x": .5, "center_y": .5}

                    # Pulsing circle
                    Canvas:
                        id: indicator_canvas
                        size_hint_x: None
                        size_hint_y: None
                        width: 30
                        height: 30

                    # Status label
                    Label:
                        id: status_label
                        text: "Ready to record"
                        font_size: 16
                        color: TEXT_SECONDARY
                        size_hint_x: None
                        width: 120

        # Main content
        BoxLayout:
            orientation: 'vertical'
            pos_hint: {"top": 0.88}
            size_hint_y: 0.76
            spacing: 15
            padding: 20

            # Settings bar
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: 80
                spacing: 20
                padding: 10

                # Duration setting
                BoxLayout:
                    orientation: 'vertical'
                    spacing: 5
                    size_hint_x: 0.3

                    Label:
                        text: "Duration (sec):"
                        font_size: 14
                        color: TEXT_SECONDARY
                        size_hint_y: None
                        height: 20

                    Spinner:
                        id: duration_spinner
                        text: '60'
                        values: '30', '60', '120', '300'
                        font_size: 16
                        size_hint_y: None
                        height: 40

                # Interval setting
                BoxLayout:
                    orientation: 'vertical'
                    spacing: 5
                    size_hint_x: 0.3

                    Label:
                        text: "Interval (sec):"
                        font_size: 14
                        color: TEXT_SECONDARY
                        size_hint_y: None
                        height: 20

                    Spinner:
                        id: interval_spinner
                        text: '2.0'
                        values: '0.5', '1.0', '1.5', '2.0', '3.0', '5.0'
                        font_size: 16
                        size_hint_y: None
                        height: 40

            # Preview area
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: 0.5
                spacing: 10

                Label:
                    text: "📺 Preview"
                    font_size: 18
                    bold: True
                    color: TEXT_PRIMARY
                    size_hint_y: None
                    height: 30

                # Preview canvas
                BoxLayout:
                    canvas.before:
                        Color:
                            rgba: 0.12, 0.12, 0.12, 1.0
                        Rectangle:
                            pos: self.pos
                            size: self.size
                    RelativeLayout:
                        # Preview image will be displayed here
                        Label:
                            id: preview_label
                            text: "Preview will appear here"
                            color: TEXT_HINT
                            font_size: 14
                            pos_hint: {"center_x": .5, "center_y": .5}

            # Control button
            Button:
                id: record_button
                text: "▶️ Start Recording"
                font_size: 20
                bold: True
                background_color: 0.53, 0.93, 0.42, 1.0
                color: 0, 0, 0, 1
                size_hint_y: None
                height: 60
                on_release: root.start_recording()

            # Info display
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: 40
                spacing: 20
                padding: 10

                Label:
                    id: frame_counter_label
                    text: "Frames: 0"
                    font_size: 16
                    color: TEXT_SECONDARY

                Label:
                    id: time_label
                    text: "Time: 0s"
                    font_size: 16
                    color: TEXT_SECONDARY

        # Bottom padding
        Label:
            size_hint_y: None
            height: 20
            canvas.before:
                Color:
                    rgba: 0.12, 0.12, 0.12, 1.0
            Rectangle:
                pos: self.pos
                size: self.size
''')


class RecordingScreen(BaseScreen):
    """Recording screen with Kivy UI"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Animation state
        self.pulsing_animation = None
        self.preview_update_job = None

    def on_pre_enter(self):
        """Called before screen is displayed"""
        # Initialize presenter if not already set
        if not self.presenter:
            from ...presenters import RecordingPresenter
            from ...memory import Memory
            from ...memory.models import MemoryConfig, EmbedderConfig, VectorStoreConfig

            # Create memory system
            config = MemoryConfig(
                embedder=EmbedderConfig(
                    provider="ollama",
                    config={
                        "model": "nomic-embed-text",
                        "ollama_base_url": "http://127.0.0.1:11434"
                    }
                ),
                vector_store=VectorStoreConfig(
                    provider="chroma",
                    config={
                        "collection_name": "memscreen_records",
                        "path": "./db/chroma_db"
                    }
                )
            )

            mem = Memory(config=config)

            # Create presenter
            presenter = RecordingPresenter(
                view=self,
                memory_system=mem,
                db_path="./db/screen_capture.db"
            )

            self.set_presenter(presenter)

        # Start preview updates
        self.start_preview_updates()

    def on_pre_leave(self):
        """Called before leaving screen"""
        # Stop preview updates
        self.stop_preview_updates()

        # Stop any ongoing recording
        if self.presenter and self.presenter.is_recording:
            self.presenter.stop_recording()

    def _wire_presenter_callbacks(self):
        """Wire presenter callbacks to screen methods"""
        # We'll implement this by having the presenter call our methods directly
        pass

    def start_recording(self):
        """Start recording (called from UI button)"""
        if not self.presenter:
            self.show_error("Presenter not initialized")
            return

        # Get settings from UI
        duration = int(self.ids.duration_spinner.text)
        interval = float(self.ids.interval_spinner.text)

        # Start recording via presenter
        success = self.presenter.start_recording(duration, interval)

        if success:
            # Update UI
            self.ids.record_button.text = "⏹️ Stop Recording"
            self.ids.record_button.background_color = BUTTON_RED
            self.ids.status_label.text = "🔴 Recording..."
            self.ids.status_label.color = ERROR

            # Start pulsing animation
            self._start_pulsing_animation()

    def stop_recording(self):
        """Stop recording"""
        if not self.presenter:
            return

        # Stop recording via presenter
        self.presenter.stop_recording()

        # Update UI
        self.ids.record_button.text = "▶️ Start Recording"
        self.ids.record_button.background_color = BUTTON_GREEN
        self.ids.status_label.text = "Saving video..."
        self.ids.status_label.color = WARNING

        # Stop pulsing animation
        self._stop_pulsing_animation()

    def start_preview_updates(self):
        """Start updating preview"""
        self.preview_update_job = Clock.schedule_interval(0.1, self.update_preview)

    def stop_preview_updates(self):
        """Stop updating preview"""
        if self.preview_update_job:
            Clock.unschedule(self.preview_update_job)
            self.preview_update_job = None

    def update_preview(self, dt):
        """Update preview frame (called every 0.1s)"""
        if not self.presenter:
            return

        # Get preview frame from presenter
        frame = self.presenter.get_preview_frame()

        if frame is not None:
            # Update preview label with frame info
            self.ids.preview_label.text = f"Preview: {frame.shape[1]}x{frame.shape[0]}"
            # TODO: Display actual frame on canvas
            # Would need to convert frame to texture and display

    def _start_pulsing_animation(self):
        """Start pulsing animation for recording indicator"""
        indicator_canvas = self.ids.indicator_canvas

        with indicator_canvas.canvas.before:
            indicator_canvas.clear()
            self.pulsing_circle = Ellipse(
                pos=indicator_canvas.pos,
                size=(30, 30),
                color=ERROR
            )

        # Create pulsing animation
        self.pulsing_animation = Animation(
            size=(25, 25),
            t='out_quad',
            duration=0.5
        )
        self.pulsing_animation.bind(on_complete=self._restart_pulsing_animation)
        self.pulsing_animation.start(self.pulsing_circle)

    def _restart_pulsing_animation(self, instance, value):
        """Restart pulsing animation (callback)"""
        self.pulsing_animation = Animation(
            size=(35, 35),
            t='in_out_quad',
            duration=0.5
        )
        self.pulsing_animation.bind(on_complete=self._restart_pulsing_animation)
        self.pulsing_animation.start(self.pulsing_circle)

    def _stop_pulsing_animation(self):
        """Stop pulsing animation"""
        if self.pulsing_animation:
            self.pulsing_animation.stop(self.pulsing_circle)
            self.pulsing_animation = None

    # Presenter callbacks
    def on_recording_started(self):
        """Called by presenter when recording starts"""
        print("[RecordingScreen] Recording started")

    def on_recording_stopped(self):
        """Called by presenter when recording stops"""
        print("[RecordingScreen] Recording stopped")

    def on_recording_saved(self, filename, file_size):
        """Called by presenter when video is saved"""
        self.ids.status_label.text = "✅ Saved"
        self.ids.status_label.color = SUCCESS

        # Reset status after delay
        Clock.schedule_once(3, self._reset_status)

    def on_frame_captured(self, frame_count, elapsed_time):
        """Called by presenter with frame updates"""
        self.ids.frame_counter_label.text = f"Frames: {frame_count}"
        self.ids.time_label.text = f"Time: {elapsed_time:.1f}s"

    def _reset_status(self, dt):
        """Reset status label"""
        self.ids.status_label.text = "Ready to record"
        self.ids.status_label.color = TEXT_SECONDARY
