#!/usr/bin/env python3
"""
MemScreen Kivy UI - Clean Modern Design with Light Purple Theme
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.config import Config
from kivy.core.text import LabelBase
from kivy.graphics.texture import Texture
import os
import cv2
import threading

Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '800')
Window.title = "MemScreen v0.3"

# Register Chinese fonts
mac_fonts = [
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/STHeiti Light.ttc',
    '/System/Library/Fonts/Helvetica.ttc',
]

for font_path in mac_fonts:
    if os.path.exists(font_path):
        try:
            LabelBase.register('chinese', font_path)
            print(f"[Font] Registered: {font_path}")
            break
        except:
            pass

from memscreen import Memory
from memscreen.memory.models import MemoryConfig, EmbedderConfig, LlmConfig, VectorStoreConfig
from memscreen.presenters.recording_presenter import RecordingPresenter
from memscreen.presenters.video_presenter import VideoPresenter


class BaseScreen(Screen):
    def __init__(self, memory_system=None, **kwargs):
        super().__init__(**kwargs)
        self.memory_system = memory_system
        self.presenter = None

        # Set screen background color to light purple
        with self.canvas.before:
            Color(0.95, 0.93, 0.98, 1)  # Light purple
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size

    def set_presenter(self, presenter):
        self.presenter = presenter


class RecordingScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_recording = False
        self.presenter = None
        self.preview_update_event = None

        layout = BoxLayout(orientation='vertical', spacing=15, padding=25)

        # Title
        title = Label(
            text='Screen Recording',
            font_name='chinese',
            font_size='40',
            bold=True,
            size_hint_y=None,
            height=70,
            color=(0, 0, 0, 1)  # Black
        )
        layout.add_widget(title)

        # Status
        self.status_label = Label(
            text='Status: Ready',
            font_name='chinese',
            font_size='22',
            size_hint_y=None,
            height=50,
            color=(0, 0, 0, 1)  # Black
        )
        layout.add_widget(self.status_label)

        # Settings
        settings = BoxLayout(size_hint_y=None, height=90, spacing=12)
        settings.add_widget(Label(text='Duration (seconds):', font_name='chinese', font_size='18', color=(0, 0, 0, 1)))
        self.duration_spinner = Spinner(
            text='60',
            values=['30', '60', '120', '300'],
            font_name='chinese',
            font_size='15'
        )
        settings.add_widget(self.duration_spinner)
        settings.add_widget(Label(text='Interval (seconds):', font_name='chinese', font_size='18', color=(0, 0, 0, 1)))
        self.interval_spinner = Spinner(
            text='2.0',
            values=['0.5', '1.0', '1.5', '2.0', '3.0', '5.0'],
            font_name='chinese',
            font_size='18'
        )
        settings.add_widget(self.interval_spinner)
        layout.add_widget(settings)

        # Preview area with image widget
        self.preview_box = BoxLayout(size_hint_y=0.45)
        with self.preview_box.canvas.before:
            Color(0.88, 0.85, 0.92, 1)  # Light purple gray
            self.preview_bg = Rectangle(pos=self.preview_box.pos, size=self.preview_box.size)
        self.preview_box.bind(pos=self._update_preview, size=self._update_preview)

        # Use Image widget for displaying frames
        self.preview_image = Image(
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=True
        )
        self.preview_box.add_widget(self.preview_image)
        layout.add_widget(self.preview_box)

        # Record button
        self.record_btn = Button(
            text='Start Recording',
            font_name='chinese',
            font_size='24',
            bold=True,
            size_hint_y=None,
            height=75,
            background_color=(0.6, 0.4, 0.75, 1),
            color=(1, 1, 1, 1)
        )
        self.record_btn.bind(on_press=self.toggle_recording)
        layout.add_widget(self.record_btn)

        # Info
        info = BoxLayout(size_hint_y=None, height=50, spacing=25)
        self.frame_label = Label(text='Frames: 0', font_name='chinese', font_size='18', color=(0, 0, 0, 1))
        self.time_label = Label(text='Time: 0s', font_name='chinese', font_size='18', color=(0, 0, 0, 1))
        info.add_widget(self.frame_label)
        info.add_widget(self.time_label)
        layout.add_widget(info)

        self.add_widget(layout)

        # Start preview update
        Clock.schedule_once(self._start_preview, 1)

    def _update_preview(self, instance, value):
        self.preview_bg.pos = instance.pos
        self.preview_bg.size = instance.size

    def _start_preview(self, dt):
        """Start updating preview"""
        if self.preview_update_event is None:
            self.preview_update_event = Clock.schedule_interval(self._update_preview_frame, 0.1)

    def _update_preview_frame(self, dt):
        """Update preview with current frame"""
        if self.presenter and not self.is_recording:
            frame = self.presenter.get_preview_frame()
            if frame is not None:
                self._display_frame(frame)

    def _display_frame(self, frame):
        """Convert OpenCV frame to Kivy texture and display"""
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Flip vertically for correct display
        frame_rgb = cv2.flip(frame_rgb, 0)

        # Create texture
        texture = Texture.create(size=(frame_rgb.shape[1], frame_rgb.shape[0]), colorfmt='rgb')
        texture.blit_buffer(frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')

        # Update image
        self.preview_image.texture = texture

    def set_presenter(self, presenter):
        """Set the presenter for this screen"""
        self.presenter = presenter
        self.presenter.view = self

    def on_recording_started(self):
        """Callback when recording starts"""
        self.is_recording = True
        self.record_btn.text = "Stop Recording"
        self.record_btn.background_color = (0.75, 0.3, 0.4, 1)
        self.status_label.text = "Status: Recording..."

    def on_recording_stopped(self):
        """Callback when recording stops"""
        self.is_recording = False
        self.record_btn.text = "Start Recording"
        self.record_btn.background_color = (0.6, 0.4, 0.75, 1)
        self.status_label.text = "Status: Saved"

    def on_frame_captured(self, frame, frame_count):
        """Callback when a frame is captured"""
        self.frame_label.text = f'Frames: {frame_count}'
        self._display_frame(frame)

    def on_recording_saved(self, filename, file_size):
        """Callback when recording is saved"""
        self.status_label.text = f"Status: Saved ({file_size / 1024 / 1024:.1f} MB)"

    def on_recording_deleted(self, filename):
        """Callback when recording is deleted"""
        pass  # Could update UI here if needed

    def toggle_recording(self, instance):
        if not self.is_recording:
            if self.presenter:
                duration = int(self.duration_spinner.text)
                interval = float(self.interval_spinner.text)
                self.presenter.start_recording(duration, interval)
        else:
            if self.presenter:
                self.presenter.stop_recording()


class ChatScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', spacing=15, padding=25)

        # Title
        title = Label(
            text='AI Chat',
            font_name='chinese',
            font_size='40',
            bold=True,
            size_hint_y=None,
            height=70,
            color=(0, 0, 0, 1)  # Black
        )
        layout.add_widget(title)

        # Model selector - larger
        model_box = BoxLayout(size_hint_y=None, height=70, spacing=10)
        model_box.add_widget(Label(text='Model:', font_name='chinese', font_size='20', color=(0, 0, 0, 1), size_hint_x=0.2))
        self.model_spinner = Spinner(
            text='qwen2.5vl:3b',
            values=['qwen2.5vl:3b', 'llama2', 'mistral'],
            font_name='chinese',
            font_size='20',
            size_hint_x=0.8
        )
        model_box.add_widget(self.model_spinner)
        layout.add_widget(model_box)

        # Chat history
        scroll = ScrollView(size_hint_y=0.65)
        self.chat_history = BoxLayout(orientation='vertical', size_hint_y=None, spacing=15, padding=18)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))
        scroll.add_widget(self.chat_history)
        layout.add_widget(scroll)

        # Input
        input_box = BoxLayout(size_hint_y=None, height=80, spacing=12)

        self.chat_input = TextInput(
            text='',
            multiline=False,
            hint_text='Type your message...',
            font_name='chinese',
            font_size=22,
            padding=[20, 20, 20, 20],
            foreground_color=(0, 0, 0, 1),
            background_color=(1, 1, 1, 1),
            cursor_color=(0, 0, 0, 1),
            use_bubble=False,
            write_tab=False
        )
        send_btn = Button(
            text='Send',
            font_name='chinese',
            font_size='22',
            bold=True,
            background_color=(0.6, 0.4, 0.75, 1),
            color=(1, 1, 1, 1)
        )
        send_btn.bind(on_press=self.send_message)
        input_box.add_widget(self.chat_input)
        input_box.add_widget(send_btn)
        layout.add_widget(input_box)

        self.add_widget(layout)

    def send_message(self, instance):
        text = self.chat_input.text
        if not text:
            return

        # Clear input immediately
        self.chat_input.text = ""

        # Add user message - larger font
        msg_user = Label(
            text=f'You: {text}',
            font_name='chinese',
            font_size='20',
            size_hint_y=None,
            height=60,
            halign='left',
            valign='top',
            text_size=(420, None),
            color=(0, 0, 0, 1)  # Black
        )
        msg_user.bind(texture_size=msg_user.setter('size'))
        self.chat_history.add_widget(msg_user)

        # Show typing indicator - larger
        typing_label = Label(
            text='AI: Typing...',
            font_name='chinese',
            font_size='20',
            size_hint_y=None,
            height=60,
            halign='left',
            valign='top',
            text_size=(420, None),
            color=(0.3, 0.3, 0.35, 1),
            italic=True
        )
        typing_label.bind(texture_size=typing_label.setter('size'))
        self.chat_history.add_widget(typing_label)

        # Get AI response in background thread
        def get_ai_response():
            ai_text = ""
            error_msg_text = None
            try:
                from memscreen.llm import OllamaLLM
                llm = OllamaLLM(config={"model": self.model_spinner.text})

                # Try to use Memory system to search for relevant context
                context = ""
                if self.memory_system:
                    try:
                        # Search memories for relevant context
                        # Use a default user_id for searching
                        search_result = self.memory_system.search(
                            query=text,
                            user_id="default_user",  # Default user ID
                            limit=5,
                            threshold=0.0
                        )

                        # Extract context from search results
                        if search_result and "results" in search_result:
                            memories = search_result["results"]
                            if memories and len(memories) > 0:
                                # Build context from memory items
                                context_parts = []
                                for mem in memories[:3]:  # Use top 3 memories
                                    if isinstance(mem, dict):
                                        if "memory" in mem:
                                            content = mem["memory"]
                                        elif "content" in mem:
                                            content = mem["content"]
                                        else:
                                            content = str(mem)
                                        context_parts.append(f"- {content}")
                                if context_parts:
                                    context = "Relevant context from memory:\n" + "\n".join(context_parts)
                                    print(f"[Chat] Found {len(memories)} relevant memories")
                    except Exception as mem_err:
                        print(f"[Chat] Memory search failed: {mem_err}")
                        # Continue without memory context

                # Prepare messages with context and system prompt
                messages = []

                # System prompt - define AI's role and behavior
                system_prompt = """You are MemScreen, a helpful AI assistant. You help users with:
- Answering questions about their screen recordings and activities
- Providing information from their memory
- Assisting with general knowledge
- Being friendly and concise

Respond naturally without mentioning your model provider or technical details."""

                if context:
                    messages.append({"role": "system", "content": f"{system_prompt}\n\nHere is some relevant context from the user's memory:\n\n{context}"})
                else:
                    messages.append({"role": "system", "content": system_prompt})

                messages.append({"role": "user", "content": text})

                response = llm.generate_response(messages)

                if response:
                    ai_text = str(response)
                else:
                    ai_text = "I apologize, but I couldn't generate a response."

            except Exception as err:
                error_msg_text = f"Error: {str(err)}"
                import traceback
                traceback.print_exc()

            # Update UI on main thread
            def update_ui(dt):
                try:
                    self.chat_history.remove_widget(typing_label)
                except:
                    pass  # Widget may already be removed

                if error_msg_text:
                    # Show error message - larger
                    error_msg = Label(
                        text=f'AI: {error_msg_text}',
                        font_name='chinese',
                        font_size='20',
                        size_hint_y=None,
                        height=90,
                        halign='left',
                        valign='top',
                        text_size=(420, None),
                        color=(0.8, 0.2, 0.2, 1)
                    )
                    error_msg.bind(texture_size=error_msg.setter('size'))
                    self.chat_history.add_widget(error_msg)
                else:
                    # Show AI response - larger font
                    import math
                    estimated_lines = max(2, math.ceil(len(ai_text) / 40))
                    msg_height = min(280, estimated_lines * 32)

                    msg_ai = Label(
                        text=f'AI: {ai_text}',
                        font_name='chinese',
                        font_size='20',
                        size_hint_y=None,
                        height=msg_height,
                        halign='left',
                        valign='top',
                        text_size=(420, None),
                        color=(0, 0, 0, 1)
                    )
                    msg_ai.bind(texture_size=msg_ai.setter('size'))
                    self.chat_history.add_widget(msg_ai)

            Clock.schedule_once(update_ui)

        # Start background thread
        import threading
        thread = threading.Thread(target=get_ai_response, daemon=True)
        thread.start()


class VideoScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.presenter = None
        self.current_video = None
        self.is_playing = False

        layout = BoxLayout(orientation='vertical', spacing=15, padding=25)

        # Header with title, back button and refresh button
        header = BoxLayout(size_hint_y=None, height=60, spacing=15)
        self.back_btn = Button(
            text='← List',
            font_name='chinese',
            font_size='14',
            background_color=(0.5, 0.4, 0.6, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.15,
            size_hint_y=None,
            height=50
        )
        self.back_btn.bind(on_press=self.show_list)

        self.title_label = Label(
            text='Recorded Videos',
            font_name='chinese',
            font_size='32',
            bold=True,
            color=(0, 0, 0, 1),
            size_hint_x=0.55,
            halign='center'
        )

        refresh_btn = Button(
            text='Refresh',
            font_name='chinese',
            font_size='16',
            background_color=(0.6, 0.4, 0.75, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.3,
            size_hint_y=None,
            height=50
        )
        refresh_btn.bind(on_press=self.refresh)

        header.add_widget(self.back_btn)
        header.add_widget(self.title_label)
        header.add_widget(refresh_btn)
        layout.add_widget(header)

        # Info label
        self.info_label = Label(
            text='Loading...',
            font_name='chinese',
            font_size='18',
            color=(0.2, 0.2, 0.25, 1),
            size_hint_y=None,
            height=35,
            halign='left'
        )
        layout.add_widget(self.info_label)

        # Content area - switches between list and player
        self.content_area = BoxLayout(orientation='vertical')
        layout.add_widget(self.content_area)

        # Video list container
        self.list_container = BoxLayout(orientation='vertical')
        scroll = ScrollView(size_hint=(1, 1))
        self.video_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8, padding=10)
        self.video_list.bind(minimum_height=self.video_list.setter('height'))
        scroll.add_widget(self.video_list)
        self.list_container.add_widget(scroll)
        self.content_area.add_widget(self.list_container)

        # Video player container (hidden initially)
        self.player_container = BoxLayout(orientation='vertical', spacing=10)

        # Video preview image
        self.video_preview = Image(
            size_hint=(1, 0.6),
            allow_stretch=True,
            keep_ratio=False
        )
        with self.video_preview.canvas.before:
            Color(0.85, 0.82, 0.88, 1)
            self.preview_bg = Rectangle(pos=self.video_preview.pos, size=self.video_preview.size)
        self.video_preview.bind(pos=self._update_preview_bg, size=self._update_preview_bg)
        self.player_container.add_widget(self.video_preview)

        # Video info
        self.video_info_label = Label(
            text='Select a video to play',
            font_name='chinese',
            font_size='18',
            color=(0, 0, 0, 1),
            size_hint_y=None,
            height=50,
            halign='center'
        )
        self.player_container.add_widget(self.video_info_label)

        # Controls
        controls = BoxLayout(size_hint_y=None, height=60, spacing=10)
        self.play_btn = Button(
            text='Play',
            font_name='chinese',
            font_size='20',
            background_color=(0.6, 0.4, 0.75, 1),
            color=(1, 1, 1, 1)
        )
        self.play_btn.bind(on_press=self.toggle_play)
        controls.add_widget(self.play_btn)
        self.player_container.add_widget(controls)

        self.add_widget(layout)
        Clock.schedule_once(lambda dt: self.refresh(None), 0.3)

    def _update_preview_bg(self, instance, value):
        self.preview_bg.pos = instance.pos
        self.preview_bg.size = instance.size

    def set_presenter(self, presenter):
        """Set the presenter for this screen"""
        self.presenter = presenter
        self.presenter.view = self

    def refresh(self, instance):
        """Refresh the video list"""
        self.show_list(None)
        self.video_list.clear_widgets()

        if self.presenter:
            try:
                videos = self.presenter.get_video_list()

                if not videos:
                    self.info_label.text = 'No recordings found'
                    msg = Label(
                        text='No recordings found.\nStart recording from the Recording tab.',
                        font_name='chinese',
                        font_size='22',
                        color=(0.3, 0.3, 0.35, 1),
                        size_hint_y=None,
                        height=100,
                        halign='center'
                    )
                    self.video_list.add_widget(msg)
                else:
                    self.info_label.text = f'Found {len(videos)} recording(s)'

                    for idx, video in enumerate(videos):
                        item = BoxLayout(
                            orientation='vertical',
                            size_hint_y=None,
                            spacing=6,
                            padding=14
                        )

                        with item.canvas.before:
                            Color(0.98, 0.95, 1.0, 1)
                            item_bg = Rectangle(pos=item.pos, size=item.size)
                        item.bind(pos=lambda i,v: setattr(item_bg, 'pos', i.pos),
                                  size=lambda i,v: setattr(item_bg, 'size', i.size))

                        # Video info row with play button - larger
                        info_row = BoxLayout(size_hint_y=None, height=35, spacing=15)

                        filename = os.path.basename(video.filename)
                        duration_str = f"{video.duration:.1f}s"
                        timestamp_str = video.timestamp.split('.')[0] if '.' in video.timestamp else video.timestamp
                        frames_str = f"{video.frame_count} frames" if video.frame_count else "N/A"

                        filename_label = Label(
                            text=f'{filename}',
                            font_name='chinese',
                            font_size='20',
                            bold=True,
                            halign='left',
                            color=(0, 0, 0, 1),
                            text_size=(None, None)
                        )
                        info_row.add_widget(filename_label)

                        # Play button - larger
                        play_btn = Button(
                            text='▶ Play',
                            font_name='chinese',
                            font_size='16',
                            bold=True,
                            background_color=(0.6, 0.4, 0.75, 1),
                            color=(1, 1, 1, 1),
                            size_hint_x=0.2,
                            size_hint_y=None,
                            height=40
                        )
                        play_btn.bind(on_press=lambda instance, v=video: self.play_video(v))
                        info_row.add_widget(play_btn)

                        item.add_widget(info_row)

                        # Details - larger font
                        details = f'Duration: {duration_str}  |  Recorded: {timestamp_str}  |  Frames: {frames_str}'
                        details_label = Label(
                            text=details,
                            font_name='chinese',
                            font_size='16',
                            halign='left',
                            color=(0.3, 0.3, 0.35, 1),
                            size_hint_y=None,
                            height=25
                        )
                        item.add_widget(details_label)

                        self.video_list.add_widget(item)

            except Exception as e:
                self.info_label.text = 'Error loading videos'
                error_label = Label(
                    text=f'Error: {str(e)}',
                    font_name='chinese',
                    font_size='18',
                    color=(0.8, 0.2, 0.2, 1),
                    size_hint_y=None,
                    height=50
                )
                self.video_list.add_widget(error_label)
                import traceback
                traceback.print_exc()

    def show_list(self, instance):
        """Show video list"""
        self.content_area.clear_widgets()
        self.content_area.add_widget(self.list_container)
        self.back_btn.disabled = True
        self.title_label.text = 'Recorded Videos'

    def play_video(self, video):
        """Play a video"""
        print(f"[VideoScreen] play_video called: {video.filename}")
        self.current_video = video

        # Show player
        self.content_area.clear_widgets()
        self.content_area.add_widget(self.player_container)
        self.back_btn.disabled = False
        self.title_label.text = os.path.basename(video.filename)

        # Update info
        duration_str = f"{video.duration:.1f}s"
        timestamp_str = video.timestamp.split('.')[0] if '.' in video.timestamp else video.timestamp
        frames_str = f"{video.frame_count} frames" if video.frame_count else "N/A"

        info_text = f"Duration: {duration_str}  |  Frames: {frames_str}\nRecorded: {timestamp_str}"
        self.video_info_label.text = info_text

        # Load video without showing preview first (avoid frame position issues)
        if self.presenter:
            print(f"[VideoScreen] Loading video...")
            if self.presenter.load_video(video.filename):
                self.video_info_label.text = info_text + "\nReady to play"
                print(f"[VideoScreen] Video loaded successfully")
                # Don't show first frame - let user press play to avoid thread conflicts
            else:
                self.video_info_label.text = "Failed to load video"
                print(f"[VideoScreen] Failed to load video")

    def _display_frame(self, frame):
        """Display a frame in the preview"""
        try:
            if frame is None:
                print("[VideoScreen] Warning: Received None frame")
                return

            # Validate frame shape
            if len(frame.shape) != 3 or frame.shape[2] != 3:
                print(f"[VideoScreen] Warning: Invalid frame shape {frame.shape}")
                return

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.flip(frame_rgb, 0)

            # Validate frame size
            if frame_rgb.shape[0] == 0 or frame_rgb.shape[1] == 0:
                print(f"[VideoScreen] Warning: Invalid frame size {frame_rgb.shape}")
                return

            texture = Texture.create(size=(frame_rgb.shape[1], frame_rgb.shape[0]), colorfmt='rgb')
            texture.blit_buffer(frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            self.video_preview.texture = texture
        except Exception as e:
            print(f"[VideoScreen] Error displaying frame: {e}")
            import traceback
            traceback.print_exc()

    def toggle_play(self, instance):
        """Toggle video playback"""
        print(f"[VideoScreen] toggle_play called, is_playing={self.is_playing}")
        if not self.presenter:
            print("[VideoScreen] No presenter!")
            return

        if self.is_playing:
            # Pause
            print("[VideoScreen] Pausing video...")
            self.presenter.pause_video()
            # Update UI immediately
            self.is_playing = False
            self.play_btn.text = 'Play'
        else:
            # Play
            print("[VideoScreen] Starting video playback...")
            if self.presenter.play_video():
                # Update UI immediately after starting playback
                self.is_playing = True
                self.play_btn.text = 'Pause'
            else:
                print("[VideoScreen] Failed to start playback")

    def on_playback_frame(self, frame, frame_number):
        """Callback when a new frame is available during playback"""
        # Schedule display update on main thread using Clock
        def update_frame(dt):
            self._display_frame(frame)
        Clock.schedule_once(update_frame)

    def on_playback_finished(self):
        """Callback when playback finishes"""
        def update_ui(dt):
            self.is_playing = False
            self.play_btn.text = 'Play'
        Clock.schedule_once(update_ui)

    def on_video_loaded(self, filename, total_frames, fps):
        """Callback when video is loaded"""
        pass  # Video info already updated in play_video method

    def on_playback_started(self):
        """Callback when playback starts"""
        self.is_playing = True
        self.play_btn.text = 'Pause'

    def on_playback_paused(self):
        """Callback when playback is paused"""
        self.is_playing = False
        self.play_btn.text = 'Play'

    def on_playback_stopped(self):
        """Callback when playback is stopped"""
        self.is_playing = False
        self.play_btn.text = 'Play'

    def on_frame_changed(self, frame, frame_number):
        """Callback when frame changes (seek)"""
        self._display_frame(frame)

    def on_video_deleted(self, filename):
        """Callback when video is deleted"""
        pass  # Could refresh list here


class ProcessScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_tracking = False

        layout = BoxLayout(orientation='vertical', spacing=15, padding=25)

        # Title
        title = Label(
            text='Process Mining',
            font_name='chinese',
            font_size='40',
            bold=True,
            size_hint_y=None,
            height=70,
            color=(0, 0, 0, 1)  # Black
        )
        layout.add_widget(title)

        # Control button
        self.track_btn = Button(
            text='Start Tracking',
            font_name='chinese',
            font_size='24',
            bold=True,
            size_hint_y=None,
            height=75,
            background_color=(0.6, 0.4, 0.75, 1),
            color=(1, 1, 1, 1)
        )
        self.track_btn.bind(on_press=self.toggle)
        layout.add_widget(self.track_btn)

        # Event feed
        scroll = ScrollView()
        self.events = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8, padding=15)
        self.events.bind(minimum_height=self.events.setter('height'))
        scroll.add_widget(self.events)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def toggle(self, instance):
        if not self.is_tracking:
            self.start()
        else:
            self.stop()

    def start(self):
        self.is_tracking = True
        self.track_btn.text = "Stop Tracking"
        self.track_btn.background_color = (0.75, 0.3, 0.4, 1)
        self._add_event("Tracking started")

    def stop(self):
        self.is_tracking = False
        self.track_btn.text = "Start Tracking"
        self.track_btn.background_color = (0.6, 0.4, 0.75, 1)
        self._add_event("Tracking stopped")

    def _add_event(self, text):
        event = Label(
            text=text,
            font_name='chinese',
            font_size='18',
            size_hint_y=None,
            height=40,
            color=(0, 0, 0, 1),  # Black
            halign='left'
        )
        self.events.add_widget(event)


class SettingsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', spacing=15, padding=25)

        # Title
        title = Label(
            text='Settings',
            font_name='chinese',
            font_size='40',
            bold=True,
            size_hint_y=None,
            height=70,
            color=(0, 0, 0, 1)  # Black
        )
        layout.add_widget(title)

        # Info
        info = Label(
            text='''''Memory System: ChromaDB + SQLite
LLM Provider: Ollama
Embedding Model: nomic-embed-text
Database Path: ./db/

Version: v0.3
UI Framework: Kivy

Features:
  - Screen Recording
  - AI Chat
  - Video Management
  - Process Mining
  - Privacy-First Design''',
            font_name='chinese',
            font_size='18',
            halign='left',
            valign='top',
            color=(0, 0, 0, 1)  # Black
        )
        layout.add_widget(info)

        self.add_widget(layout)


class MemScreenKivyApp(App):
    def build(self):
        # Memory
        try:
            config = MemoryConfig(
                embedder=EmbedderConfig(provider="ollama", config={"model": "nomic-embed-text"}),
                vector_store=VectorStoreConfig(provider="chroma", config={"path": "./db/chroma_db"}),
                llm=LlmConfig(provider="ollama", config={"model": "qwen2.5vl:3b"})
            )
            self.memory = Memory(config=config)
            print("[App] Memory initialized")
        except Exception as e:
            print(f"[App] Warning: {e}")
            self.memory = None

        # Initialize presenters
        try:
            self.recording_presenter = RecordingPresenter(memory_system=self.memory)
            self.recording_presenter.initialize()
            print("[App] RecordingPresenter initialized")
        except Exception as e:
            print(f"[App] Failed to initialize RecordingPresenter: {e}")
            self.recording_presenter = None

        try:
            self.video_presenter = VideoPresenter()
            self.video_presenter.initialize()
            print("[App] VideoPresenter initialized")
        except Exception as e:
            print(f"[App] Failed to initialize VideoPresenter: {e}")
            self.video_presenter = None

        # Root layout
        root = BoxLayout(orientation='horizontal', spacing=0)

        # Sidebar with light purple - wider for larger buttons
        sidebar = BoxLayout(
            orientation='vertical',
            size_hint_x=None,
            width=200,
            spacing=12,
            padding=15
        )
        with sidebar.canvas.before:
            Color(0.35, 0.3, 0.4, 1)  # Light purple sidebar
            self.sidebar_bg = Rectangle(pos=sidebar.pos, size=sidebar.size)
        sidebar.bind(pos=lambda i,v: setattr(self.sidebar_bg, 'pos', i.pos),
                     size=lambda i,v: setattr(self.sidebar_bg, 'size', i.size))

        # Title
        app_title = Label(
            text='MemScreen',
            font_name='chinese',
            font_size=26,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=60
        )
        sidebar.add_widget(app_title)

        # Separator
        sep = BoxLayout(size_hint_y=None, height=2)
        with sep.canvas.before:
            Color(0.5, 0.45, 0.55, 1)
            sep_bg = Rectangle(pos=sep.pos, size=sep.size)
        sep.bind(pos=lambda i,v: setattr(sep_bg, 'pos', i.pos),
                 size=lambda i,v: setattr(sep_bg, 'size', i.size))
        sidebar.add_widget(sep)

        # Nav buttons - larger and more readable
        self.nav_btns = {}
        for name, label in [
            ('recording', 'Recording'),
            ('chat', 'AI Chat'),
            ('video', 'Videos'),
            ('process', 'Process'),
            ('settings', 'Settings'),
        ]:
            btn = ToggleButton(
                text=label,
                font_name='chinese',
                font_size=20,
                size_hint_y=None,
                height=75,
                group='nav',
                background_color=(0.3, 0.28, 0.35, 1),
                color=(0.9, 0.9, 0.9, 1),
                halign='center',
                valign='middle',
                padding=(10, 10)
            )
            btn.bind(on_press=lambda instance, n=name: self._switch(n))
            self.nav_btns[name] = btn
            sidebar.add_widget(btn)

        self.nav_btns['recording'].state = 'down'
        root.add_widget(sidebar)

        # Screen manager
        self.sm = ScreenManager()

        # Disable ScreenManager border and set background
        from kivy.core.window import Window
        Window.clearcolor = (0.95, 0.93, 0.98, 1)  # Light purple window background

        # Create screens and attach presenters
        recording_screen = RecordingScreen(name='recording', memory_system=self.memory)
        if self.recording_presenter:
            recording_screen.set_presenter(self.recording_presenter)
        self.sm.add_widget(recording_screen)

        self.sm.add_widget(ChatScreen(name='chat', memory_system=self.memory))

        video_screen = VideoScreen(name='video', memory_system=self.memory)
        if self.video_presenter:
            video_screen.set_presenter(self.video_presenter)
        self.sm.add_widget(video_screen)

        self.sm.add_widget(ProcessScreen(name='process', memory_system=self.memory))
        self.sm.add_widget(SettingsScreen(name='settings', memory_system=self.memory))

        root.add_widget(self.sm)

        return root

    def _switch(self, screen_name):
        self.sm.current = screen_name

        for name, btn in self.nav_btns.items():
            if name == screen_name:
                btn.state = 'down'
                btn.background_color = (0.6, 0.4, 0.75, 1)  # Purple for selected
                btn.color = (1, 1, 1, 1)
            else:
                btn.state = 'normal'
                btn.background_color = (0.3, 0.28, 0.35, 1)  # Darker purple for normal
                btn.color = (0.9, 0.9, 0.9, 1)

    def on_stop(self):
        """Clean up presenters when app closes"""
        if self.recording_presenter:
            self.recording_presenter.cleanup()
        if self.video_presenter:
            self.video_presenter.cleanup()

    def on_start(self):
        print("[App] Started - Light purple theme, all black text")


if __name__ == '__main__':
    MemScreenKivyApp().run()
