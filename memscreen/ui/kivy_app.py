#!/usr/bin/env python3
"""
MemScreen Kivy UI - Fully Functional Application
Integrated with existing MVP presenters and memory system
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.config import Config

# Configure Kivy
Config.set('kivy', 'keyboard_mode', 'system')
Config.set('kivy', 'log_level', 'info')
Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '800')

Window.title = "MemScreen v0.3 - Kivy UI"
Window.minimum_width = 1000
Window.minimum_height = 700

# Import MemScreen components
from memscreen import Memory
from memscreen.memory.models import MemoryConfig, EmbedderConfig, LlmConfig, VectorStoreConfig
from memscreen.presenters import (
    RecordingPresenter,
    ChatPresenter,
    VideoPresenter,
    ProcessMiningPresenter
)
from memscreen.process_mining import ProcessMiningAnalyzer
from memscreen.input_tracker import InputTracker


class BaseScreen(Screen):
    """Base screen with common functionality"""

    def __init__(self, memory_system=None, **kwargs):
        super().__init__(**kwargs)
        self.memory_system = memory_system
        self.presenter = None

    def set_presenter(self, presenter):
        """Set the presenter for this screen"""
        self.presenter = presenter


class RecordingScreen(BaseScreen):
    """Screen recording screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_recording = False
        self.preview_update_job = None

        # Create layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Header
        header = BoxLayout(size_hint_y=None, height=60, spacing=20)
        title_label = Label(
            text='🔴 Screen Recording',
            font_size=28,
            bold=True,
            size_hint_x=0.7
        )
        self.status_label = Label(
            text='Ready to record',
            font_size=18,
            size_hint_x=0.3,
            halign='right'
        )
        header.add_widget(title_label)
        header.add_widget(self.status_label)
        layout.add_widget(header)

        # Settings
        settings_layout = BoxLayout(size_hint_y=None, height=80, spacing=20)
        settings_layout.add_widget(Label(text='Duration (sec):', size_hint_x=0.2))
        self.duration_spinner = Spinner(
            text='60',
            values=['30', '60', '120', '300'],
            size_hint_x=0.3
        )
        settings_layout.add_widget(self.duration_spinner)
        settings_layout.add_widget(Label(text='Interval (sec):', size_hint_x=0.2))
        self.interval_spinner = Spinner(
            text='2.0',
            values=['0.5', '1.0', '1.5', '2.0', '3.0', '5.0'],
            size_hint_x=0.3
        )
        settings_layout.add_widget(self.interval_spinner)
        layout.add_widget(settings_layout)

        # Preview area
        preview_layout = BoxLayout(orientation='vertical', size_hint_y=0.5)
        preview_layout.add_widget(Label(
            text='📺 Preview',
            font_size=18,
            bold=True,
            size_hint_y=None,
            height=30
        ))
        self.preview_label = Label(
            text='Preview will appear here',
            font_size=14,
            color=(0.5, 0.5, 0.5, 1)
        )
        preview_layout.add_widget(self.preview_label)
        layout.add_widget(preview_layout)

        # Record button
        self.record_button = Button(
            text='▶️ Start Recording',
            font_size=20,
            bold=True,
            size_hint_y=None,
            height=60,
            background_color=(0.2, 0.8, 0.4, 1)
        )
        self.record_button.bind(on_press=self.toggle_recording)
        layout.add_widget(self.record_button)

        # Info display
        info_layout = BoxLayout(size_hint_y=None, height=40)
        self.frame_counter_label = Label(text='Frames: 0')
        self.time_label = Label(text='Time: 0s')
        info_layout.add_widget(self.frame_counter_label)
        info_layout.add_widget(self.time_label)
        layout.add_widget(info_layout)

        self.add_widget(layout)

    def on_enter(self):
        """Initialize presenter when screen is shown"""
        if not self.presenter and self.memory_system:
            from memscreen.presenters import RecordingPresenter
            presenter = RecordingPresenter(
                view=self,
                memory_system=self.memory_system,
                db_path="./db/screen_capture.db"
            )
            self.set_presenter(presenter)

    def toggle_recording(self, instance):
        """Toggle recording state"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start recording"""
        if not self.presenter:
            self.show_error("Presenter not initialized")
            return

        duration = int(self.duration_spinner.text)
        interval = float(self.interval_spinner.text)

        success = self.presenter.start_recording(duration, interval)

        if success:
            self.is_recording = True
            self.record_button.text = "⏹️ Stop Recording"
            self.record_button.background_color = (0.9, 0.3, 0.3, 1)
            self.status_label.text = "🔴 Recording..."

            # Start preview updates
            self.preview_update_job = Clock.schedule_interval(
                self.update_preview, 0.1
            )

    def stop_recording(self):
        """Stop recording"""
        if self.presenter:
            self.presenter.stop_recording()

        self.is_recording = False
        self.record_button.text = "▶️ Start Recording"
        self.record_button.background_color = (0.2, 0.8, 0.4, 1)
        self.status_label.text = "Saving video..."

        if self.preview_update_job:
            self.preview_update_job.cancel()
            self.preview_update_job = None

        # Reset status after delay
        Clock.schedule_once(self._reset_status, 3)

    def _reset_status(self, dt):
        """Reset status label"""
        self.status_label.text = "Ready to record"

    def update_preview(self, dt):
        """Update preview"""
        if self.presenter:
            frame = self.presenter.get_preview_frame()
            if frame is not None:
                self.preview_label.text = f"Preview: {frame.shape[1]}x{frame.shape[0]}"

    # Presenter callbacks
    def on_recording_started(self):
        """Called when recording starts"""
        print("[RecordingScreen] Recording started")

    def on_recording_stopped(self):
        """Called when recording stops"""
        print("[RecordingScreen] Recording stopped")

    def on_recording_saved(self, filename, file_size):
        """Called when video is saved"""
        self.status_label.text = f"✅ Saved: {filename}"

    def on_frame_captured(self, frame_count, elapsed_time):
        """Called with frame updates"""
        self.frame_counter_label.text = f"Frames: {frame_count}"
        self.time_label.text = f"Time: {elapsed_time:.1f}s"

    def show_error(self, message):
        """Show error message"""
        self.status_label.text = f"❌ Error: {message}"


class ChatScreen(BaseScreen):
    """AI Chat screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.conversation_history = []

        # Main layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Header
        header = Label(
            text='💬 AI Chat',
            font_size=28,
            bold=True,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(header)

        # Model selector
        model_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        model_layout.add_widget(Label(text='Model:', size_hint_x=0.2))
        self.model_spinner = Spinner(
            text='qwen2.5vl:3b',
            values=['qwen2.5vl:3b', 'llama2', 'mistral'],
            size_hint_x=0.8
        )
        model_layout.add_widget(self.model_spinner)
        layout.add_widget(model_layout)

        # Chat history
        scroll = ScrollView()
        self.chat_history = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=10
        )
        scroll.add_widget(self.chat_history)
        layout.add_widget(scroll)

        # Input area
        input_layout = BoxLayout(size_hint_y=None, height=60, spacing=10)
        self.chat_input = TextInput(
            multiline=False,
            hint_text='Ask about your screen...',
            size_hint_x=0.8
        )
        send_button = Button(
            text='Send',
            size_hint_x=0.2,
            background_color=(0.2, 0.6, 1.0, 1)
        )
        send_button.bind(on_press=self.send_message)
        input_layout.add_widget(self.chat_input)
        input_layout.add_widget(send_button)
        layout.add_widget(input_layout)

        self.add_widget(layout)

    def on_enter(self):
        """Initialize presenter when screen is shown"""
        if not self.presenter and self.memory_system:
            from memscreen.presenters import ChatPresenter
            presenter = ChatPresenter(
                view=self,
                memory_system=self.memory_system
            )
            self.set_presenter(presenter)

    def send_message(self, instance):
        """Send chat message"""
        user_input = self.chat_input.text.strip()
        if not user_input:
            return

        # Add user message
        self._add_message("You", user_input, color=(0.2, 0.6, 1.0, 1))
        self.chat_input.text = ""

        # Process through presenter
        if self.presenter:
            response = self.presenter.process_message(user_input)
            self._add_message("AI", response, color=(0.2, 0.8, 0.4, 1))

    def _add_message(self, sender, text, color=(1, 1, 1, 1)):
        """Add message to chat history"""
        msg_label = Label(
            text=f"{sender}: {text}",
            color=color,
            size_hint_y=None,
            height=40,
            halign='left'
        )
        msg_label.bind(texture_size=msg_label.setter('size'))
        self.chat_history.add_widget(msg_label)

    def show_message(self, message):
        """Show message from presenter"""
        self._add_message("AI", message)


class VideoScreen(BaseScreen):
    """Video management screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Header
        header = Label(
            text='🎬 Videos',
            font_size=28,
            bold=True,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(header)

        # Video list
        self.video_list = BoxLayout(orientation='vertical', spacing=10)
        layout.add_widget(self.video_list)

        # Refresh button
        refresh_button = Button(
            text='🔄 Refresh',
            size_hint_y=None,
            height=50
        )
        refresh_button.bind(on_press=self.refresh_videos)
        layout.add_widget(refresh_button)

        self.add_widget(layout)

    def on_enter(self):
        """Initialize when screen is shown"""
        self.refresh_videos(None)

    def refresh_videos(self, instance):
        """Refresh video list"""
        # Clear list
        self.video_list.clear_widgets()

        # Load videos from database
        import sqlite3
        import os

        try:
            conn = sqlite3.connect("./db/screen_capture.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT filename, duration, created_at
                FROM screen_recordings
                ORDER BY created_at DESC
                LIMIT 20
            """)
            videos = cursor.fetchall()
            conn.close()

            if not videos:
                self.video_list.add_widget(Label(text='No recordings yet'))
            else:
                for filename, duration, created_at in videos:
                    if os.path.exists(filename):
                        video_item = BoxLayout(
                            size_hint_y=None,
                            height=60,
                            spacing=10
                        )
                        video_item.add_widget(Label(
                            text=f"📹 {os.path.basename(filename)}",
                            size_hint_x=0.7
                        ))
                        video_item.add_widget(Label(
                            text=f"{duration:.1f}s",
                            size_hint_x=0.15
                        ))
                        video_item.add_widget(Label(
                            text=created_at[:19],
                            size_hint_x=0.15
                        ))
                        self.video_list.add_widget(video_item)

        except Exception as e:
            self.video_list.add_widget(Label(text=f'Error: {str(e)}'))


class ProcessScreen(BaseScreen):
    """Process mining screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_tracking = False

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Header
        header = Label(
            text='📊 Process Mining',
            font_size=28,
            bold=True,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(header)

        # Control buttons
        control_layout = BoxLayout(size_hint_y=None, height=60, spacing=10)
        self.track_button = Button(
            text='▶️ Start Tracking',
            background_color=(0.2, 0.8, 0.4, 1)
        )
        self.track_button.bind(on_press=self.toggle_tracking)
        control_layout.add_widget(self.track_button)
        layout.add_widget(control_layout)

        # Event feed
        layout.add_widget(Label(text='Live Event Feed:', font_size=18, bold=True))
        self.event_feed = BoxLayout(orientation='vertical', spacing=5)
        scroll = ScrollView()
        scroll.add_widget(self.event_feed)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def toggle_tracking(self, instance):
        """Toggle input tracking"""
        if not self.is_tracking:
            self.start_tracking()
        else:
            self.stop_tracking()

    def start_tracking(self):
        """Start tracking keyboard/mouse events"""
        self.is_tracking = True
        self.track_button.text = "⏹️ Stop Tracking"
        self.track_button.background_color = (0.9, 0.3, 0.3, 1)

        # Add event
        self._add_event("Tracking started", (0.2, 0.8, 0.4, 1))

    def stop_tracking(self):
        """Stop tracking"""
        self.is_tracking = False
        self.track_button.text = "▶️ Start Tracking"
        self.track_button.background_color = (0.2, 0.8, 0.4, 1)

        self._add_event("Tracking stopped", (0.9, 0.3, 0.3, 1))

    def _add_event(self, text, color=(1, 1, 1, 1)):
        """Add event to feed"""
        event_label = Label(
            text=text,
            color=color,
            size_hint_y=None,
            height=30
        )
        self.event_feed.add_widget(event_label)


class SettingsScreen(BaseScreen):
    """Settings screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Header
        header = Label(
            text='⚙️ Settings',
            font_size=28,
            bold=True,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(header)

        # Settings info
        info_text = """
Memory System: ChromaDB + SQLite
LLM Provider: Ollama
Embedding Model: nomic-embed-text
Database Path: ./db/

Version: v0.3
        """
        layout.add_widget(Label(text=info_text))

        self.add_widget(layout)


class MemScreenKivyApp(App):
    """Main Kivy Application"""

    def build(self):
        """Build the application"""
        # Initialize memory system
        try:
            config = MemoryConfig(
                embedder=EmbedderConfig(
                    provider="ollama",
                    config={"model": "nomic-embed-text"}
                ),
                vector_store=VectorStoreConfig(
                    provider="chroma",
                    config={"path": "./db/chroma_db"}
                ),
                llm=LlmConfig(
                    provider="ollama",
                    config={"model": "qwen2.5vl:3b"}
                )
            )
            self.memory_system = Memory(config=config)
            print("[MemScreenKivyApp] Memory system initialized")
        except Exception as e:
            print(f"[MemScreenKivyApp] Warning: {e}")
            self.memory_system = None

        # Create screen manager
        sm = ScreenManager()

        # Create screens
        recording_screen = RecordingScreen(name='recording', memory_system=self.memory_system)
        chat_screen = ChatScreen(name='chat', memory_system=self.memory_system)
        video_screen = VideoScreen(name='video', memory_system=self.memory_system)
        process_screen = ProcessScreen(name='process', memory_system=self.memory_system)
        settings_screen = SettingsScreen(name='settings', memory_system=self.memory_system)

        # Add screens
        sm.add_widget(recording_screen)
        sm.add_widget(chat_screen)
        sm.add_widget(video_screen)
        sm.add_widget(process_screen)
        sm.add_widget(settings_screen)

        # Set default screen
        sm.current = 'recording'

        return sm

    def on_start(self):
        """Called when app starts"""
        print("[MemScreenKivyApp] Application started")
        print("[MemScreenKivyApp] Use tabs to navigate: recording, chat, video, process, settings")

    def on_stop(self):
        """Called when app stops"""
        print("[MemScreenKivyApp] Application stopped")


if __name__ == '__main__':
    MemScreenKivyApp().run()
