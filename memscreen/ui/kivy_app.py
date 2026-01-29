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
from kivy.uix.slider import Slider
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line, Instruction
from kivy.core.window import Window
from kivy.config import Config
from kivy.core.text import LabelBase
from kivy.graphics.texture import Texture
import os
import cv2
import threading

Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '800')

# Performance optimizations for smoother text input
Config.set('kivy', 'keyboard_mode', 'system')
Config.set('kivy', 'keyboard_layout', 'qwerty')
Config.set('input', 'mouse', 'mouse,disable_multitouch')

Window.title = "MemScreen v0.4.0"

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
from memscreen.memory.manager import get_memory_manager


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
        settings = BoxLayout(size_hint_y=None, height=100, spacing=15)

        # Duration
        duration_container = BoxLayout(orientation='vertical', spacing=5)
        duration_label = Label(
            text='Duration (seconds)',
            font_name='chinese',
            font_size='18',
            size_hint_y=None,
            height=30,
            color=(0, 0, 0, 1)
        )
        duration_container.add_widget(duration_label)
        self.duration_spinner = Spinner(
            text='60',
            values=['30', '60', '120', '300'],
            font_name='chinese',
            font_size='22',
            size_hint_y=None,
            height=55
        )
        duration_container.add_widget(self.duration_spinner)
        settings.add_widget(duration_container)

        # Interval
        interval_container = BoxLayout(orientation='vertical', spacing=5)
        interval_label = Label(
            text='Interval (seconds)',
            font_name='chinese',
            font_size='18',
            size_hint_y=None,
            height=30,
            color=(0, 0, 0, 1)
        )
        interval_container.add_widget(interval_label)
        self.interval_spinner = Spinner(
            text='2.0',
            values=['0.5', '1.0', '1.5', '2.0', '3.0', '5.0'],
            font_name='chinese',
            font_size='22',
            size_hint_y=None,
            height=55
        )
        interval_container.add_widget(self.interval_spinner)
        settings.add_widget(interval_container)

        layout.add_widget(settings)

        # Preview area with image widget - larger
        self.preview_box = BoxLayout(size_hint_y=0.6)
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

    def on_frame_captured(self, frame_count, elapsed_time):
        """Callback when a frame is captured"""
        self.frame_label.text = f'Frames: {frame_count}'
        # Don't update preview during recording to avoid type issues
        # Preview will update when recording stops

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
            hint_text_color=(0.5, 0.5, 0.5, 0.6),
            font_name='chinese',
            font_size=20,
            padding=[15, 12, 15, 12],
            foreground_color=(0, 0, 0, 1),
            background_color=(1, 1, 1, 1),
            cursor_color=(0.4, 0.3, 0.6, 1),
            use_bubble=False,
            write_tab=False,
            allow_copy=True,
            input_type='text',
            auto_indent=False,
            size_hint_x=0.85  # Take up 85% of the space
        )
        send_btn = Button(
            text='Send',
            font_name='chinese',
            font_size='20',
            bold=True,
            background_color=(0.6, 0.4, 0.75, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.15  # Take up 15% of the space
        )
        send_btn.bind(on_press=self.send_message)

        # Bind Enter key to send message
        self.chat_input.bind(on_text_validate=self.send_message)

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

                    # Save conversation to memory system for future context
                    if self.memory_system:
                        try:
                            # Create conversation messages
                            conversation = [
                                {"role": "user", "content": text},
                                {"role": "assistant", "content": ai_text}
                            ]

                            # Add to memory with user_id for later retrieval
                            memory_result = self.memory_system.add(
                                conversation,
                                user_id="default_user",
                                metadata={
                                    "source": "ai_chat",
                                    "timestamp": __import__('datetime').datetime.now().isoformat(),
                                    "model": self.model_spinner.text
                                },
                                infer=True  # Let LLM extract key facts
                            )

                            if memory_result and "results" in memory_result:
                                print(f"[Chat] Saved conversation to memory: {len(memory_result['results'])} memory items created/updated")
                        except Exception as mem_err:
                            print(f"[Chat] Failed to save conversation to memory: {mem_err}")
                            # Don't fail the chat if memory save fails
                            import traceback
                            traceback.print_exc()
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

    def on_enter(self):
        """Called when screen is displayed - automatically focus input"""
        # Schedule focus after a short delay to ensure UI is ready
        Clock.schedule_once(lambda dt: self._focus_input(), 0.1)

    def _focus_input(self):
        """Focus the chat input field"""
        if self.chat_input:
            self.chat_input.focus = True
            self.chat_input.cursor = (0, len(self.chat_input.text))


# Timeline marker class (defined at module level for visibility)
from kivy.graphics import Color, Ellipse, Line
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from datetime import datetime

class TimelineMarker(RelativeLayout):
    """Video marker on timeline with tech styling"""
    def __init__(self, video, **kwargs):
        self.video = video
        # Initialize size_hint before calling super().__init__
        kwargs.setdefault('size_hint', (None, None))

        super().__init__(**kwargs)

        # Extract time from timestamp
        try:
            dt = datetime.strptime(video.timestamp.split('.')[0], '%Y-%m-%d %H:%M:%S')
            time_str = dt.strftime('%H:%M')
        except:
            time_str = '??'

        # Main circle button
        self.circle_btn = Button(
            size_hint=(None, None),
            background_color=(0.6, 0.4, 0.75, 1),
            color=(1, 1, 1, 1)
        )
        self.circle_btn.bind(on_press=self.on_press)
        self.add_widget(self.circle_btn)

        # Time label below circle
        self.time_label = Label(
            text=time_str,
            font_name='chinese',
            font_size='11',
            color=(0.6, 0.4, 0.75, 1),
            size_hint=(None, None),
            halign='center',
            valign='middle'
        )
        self.add_widget(self.time_label)

        # Draw circle and glow on canvas
        self._setup_canvas()

        # Bind size/pos changes AFTER adding children
        self.bind(pos=self.update_styling, size=self.update_styling)

        # Force initial update
        if self.width > 0 and self.height > 0:
            self.update_styling(self, None)

    def _setup_canvas(self):
        """Setup canvas drawing"""
        with self.canvas.before:
            # Outer glow
            Color(0.6, 0.4, 0.75, 0.2)
            self.outer_glow = Ellipse()

            # Circle border
            Color(0.6, 0.4, 0.75, 0.8)
            self.circle_border = Line(width=1.5, cap='round', joint='round')

    def on_press(self, instance):
        """Handle press event"""
        if self.parent and hasattr(self.parent, 'parent'):
            # Find the VideoScreen and trigger play_video
            from kivy.utils import get_color_from_hex
            # This will be handled by the parent's binding
            pass

    def update_styling(self, instance, value):
        """Update visual styling"""
        # Set circle size (make it a perfect circle)
        circle_size = min(self.width, self.height) * 0.6

        # Position circle centered ON the timeline line (y=45)
        # Timeline line is at y=45 in the timeline_content coordinate system
        # We need to position relative to parent (marker_container which is at y=0)
        circle_x = self.x + (self.width - circle_size) / 2
        circle_y = 45 - circle_size / 2  # Center on timeline line (y=45)

        self.circle_btn.size = (circle_size, circle_size)
        self.circle_btn.pos = (circle_x, circle_y)

        # Outer glow (larger than circle) - centered on same position
        glow_size = circle_size * 1.6
        glow_x = self.x + (self.width - glow_size) / 2
        glow_y = 45 - glow_size / 2
        self.outer_glow.pos = (glow_x, glow_y)
        self.outer_glow.size = (glow_size, glow_size)

        # Circle border - centered at (center_x, 45)
        center_x = self.x + self.width / 2
        self.circle_border.circle = (
            center_x, 45,  # Explicitly center on y=45
            circle_size / 2 - 2
        )

        # Time label size and position (below the circle, below timeline line)
        self.time_label.texture_update()
        self.time_label.size = self.time_label.texture_size
        label_x = center_x - self.time_label.width / 2
        # Position time label below the circle
        label_y = circle_y + circle_size + 3
        self.time_label.pos = (label_x, label_y)

    def bind(self, **kwargs):
        """Forward bind to circle_btn"""
        if 'on_press' in kwargs:
            self.circle_btn.bind(on_press=kwargs['on_press'])
        super().bind(**kwargs)


class VideoScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.presenter = None
        self.current_video = None
        self.is_playing = False

        # Main layout
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=20)

        # Header: Title + Refresh button
        header = BoxLayout(size_hint_y=None, height=55, spacing=15)

        self.title_label = Label(
            text='Recorded Videos',
            font_name='chinese',
            font_size='32',
            bold=True,
            color=(0, 0, 0, 1),
            size_hint_x=0.7,
            halign='left',
            valign='middle'
        )

        refresh_btn = Button(
            text='Refresh',
            font_name='chinese',
            font_size='18',
            background_color=(0.6, 0.4, 0.75, 1),
            color=(1, 1, 1, 1),
            size_hint_x=0.3,
            size_hint_y=None,
            height=45
        )
        refresh_btn.bind(on_press=self.refresh)

        header.add_widget(self.title_label)
        header.add_widget(refresh_btn)
        main_layout.add_widget(header)

        # Status label (count) - moved into list_layout to avoid overlap with timeline
        # We'll add it later in the list_layout instead

        # Content area for switching views
        self.content_area = BoxLayout(orientation='vertical')
        main_layout.add_widget(self.content_area)

        # ===== VIDEO LIST =====
        self.list_layout = BoxLayout(orientation='vertical')

        # Status label (count) - add at top of list_layout
        self.status_label = Label(
            text='Loading...',
            font_name='chinese',
            font_size='15',
            color=(0.4, 0.4, 0.45, 1),
            size_hint_y=None,
            height=25,
            halign='left',
            valign='middle',
            padding=(15, 0, 15, 0)
        )
        self.list_layout.add_widget(self.status_label)

        # Add spacing between status label and timeline
        spacing_widget = BoxLayout(size_hint_y=None, height=10)
        self.list_layout.add_widget(spacing_widget)

        # Timeline at top of list
        self.timeline_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=130,
            spacing=10,
            padding=(15, 5, 15, 5)  # Reduced top padding since we have spacing widget above
        )

        # Timeline title
        timeline_title = Label(
            text='Timeline - Click a dot to play',
            font_name='chinese',
            font_size='14',
            color=(0.4, 0.4, 0.45, 1),
            size_hint_y=None,
            height=20,
            halign='center'
        )
        self.timeline_container.add_widget(timeline_title)

        # Container for timeline with scrolling - increased height
        timeline_scroll_wrapper = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=115  # Increased to accommodate navigation slider
        )

        self.marker_scroll = ScrollView(
            size_hint=(1, None),
            height=90,  # Fixed height for timeline
            do_scroll_y=False,
            do_scroll_x=True,
            bar_width=4,
            bar_color=(0.6, 0.4, 0.75, 0.4),
            scroll_type=['bars', 'content'],  # Enable both bar and touch scrolling
            scroll_wheel_distance=50,  # Smooth scrolling with mouse wheel
            always_overscroll=False  # Prevent overscroll bounce for smoother feel
        )

        # Store reference to scroll_x for navigation slider
        self.marker_scroll.bind(scroll_x=self._on_timeline_scroll)

        # Use RelativeLayout to layer line behind markers
        self.timeline_content = RelativeLayout(
            size_hint_y=None,
            height=90,
            size_hint_x=None,
            width=2000  # Extended initial width for more scrolling
        )

        # Draw timeline line with enhanced tech effect - more glow layers
        with self.timeline_content.canvas.before:
            # Widest outer glow - very diffuse
            Color(0.5, 0.3, 0.7, 0.08)
            self.timeline_glow_ultra = Line(
                points=[0, 45, 2000, 45],
                width=12,
                cap='round'
            )

            # Wide outer glow
            Color(0.6, 0.4, 0.75, 0.12)
            self.timeline_glow_outer = Line(
                points=[0, 45, 2000, 45],
                width=8,
                cap='round'
            )

            # Middle glow
            Color(0.65, 0.45, 0.8, 0.25)
            self.timeline_glow_middle = Line(
                points=[0, 45, 2000, 45],
                width=4,
                cap='round'
            )

            # Inner bright glow
            Color(0.7, 0.5, 0.85, 0.5)
            self.timeline_glow_inner = Line(
                points=[0, 45, 2000, 45],
                width=2.5,
                cap='round'
            )

            # Core line (brightest - almost white)
            Color(0.85, 0.75, 0.95, 1.0)
            self.timeline_line = Line(
                points=[0, 45, 2000, 45],  # Center of 90px height
                width=1.2,
                cap='round'
            )

            # Add tick marks along the timeline for tech feel
            Color(0.6, 0.4, 0.75, 0.3)
            self.timeline_ticks = []
            for i in range(0, 2000, 100):  # Tick every 100 pixels
                tick = Line(
                    points=[i, 40, i, 50],  # Small vertical tick marks
                    width=1,
                    cap='round'
                )
                self.timeline_ticks.append(tick)

        # Play position indicator - draw on canvas.after so it appears ON TOP of everything
        with self.timeline_content.canvas.after:
            # Outer glow - very bright orange
            Color(1.0, 0.6, 0.1, 1.0)  # Full opacity, bright orange
            self.play_indicator_glow_outer = Line(
                points=[0, 43, 0, 47],  # Vertical marker
                width=12,  # Very wide glow
                cap='round'
            )
            # Inner glow
            Color(1.0, 0.75, 0.3, 1.0)  # Orange
            self.play_indicator_glow = Line(
                points=[0, 44, 0, 46],  # Slightly smaller
                width=6,
                cap='round'
            )
            # Bright core - pure yellow-white
            Color(1.0, 1.0, 0.7, 1.0)  # Bright yellow-white, full opacity
            self.play_indicator = Line(
                points=[0, 44.5, 0, 45.5],  # Very thin, exactly centered on timeline
                width=2.5,
                cap='round'
            )

        # Marker container - use BoxLayout for horizontal layout
        self.marker_container = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=90,
            size_hint_x=None,
            width=2000,
            pos=(0, 0),
            spacing=10,
            padding=(80, 0, 80, 0)  # Increased padding for more centering space
        )

        # Bind to update marker_container size when timeline_content changes
        self.timeline_content.bind(size=self._update_marker_size, pos=self._update_marker_pos)

        self.timeline_content.add_widget(self.marker_container)
        self.marker_scroll.add_widget(self.timeline_content)
        timeline_scroll_wrapper.add_widget(self.marker_scroll)

        # Add navigation slider below timeline
        self.timeline_nav_slider = Slider(
            size_hint=(1, None),
            height=15,
            min=0,
            max=1,
            value=0,
            step=0.001,
            value_track=True,
            value_track_color=(0.6, 0.4, 0.75, 0.6),
            value_track_width=2,
            cursor_size=(20, 20)
        )
        # Bind to value property, not on_value_change
        self.timeline_nav_slider.bind(value=self._on_nav_slider_change)
        timeline_scroll_wrapper.add_widget(self.timeline_nav_slider)

        self.timeline_container.add_widget(timeline_scroll_wrapper)
        self.list_layout.add_widget(self.timeline_container)

        # Video list scroll
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=10,
            bar_color=(0.7, 0.65, 0.75, 1),
            scroll_type=['bars', 'content']
        )
        self.video_list = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=10,
            padding=5
        )
        self.video_list.bind(minimum_height=self.video_list.setter('height'))
        scroll.add_widget(self.video_list)
        self.list_layout.add_widget(scroll)
        self.content_area.add_widget(self.list_layout)

        # ===== VIDEO PLAYER =====
        self.player_layout = BoxLayout(orientation='vertical', spacing=10)

        # Back button
        self.back_btn = Button(
            text='← Back to List',
            font_name='chinese',
            font_size='16',
            background_color=(0.5, 0.4, 0.6, 1),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=40
        )
        self.back_btn.bind(on_press=self.show_list)
        self.player_layout.add_widget(self.back_btn)

        # Video preview
        self.video_preview = Image(
            size_hint=(1, 0.7),
            allow_stretch=True
        )
        self.player_layout.add_widget(self.video_preview)

        # Video info
        self.video_info_label = Label(
            text='Select a video to play',
            font_name='chinese',
            font_size='16',
            color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None,
            height=40,
            halign='center',
            valign='middle'
        )
        self.player_layout.add_widget(self.video_info_label)

        # Controls row
        controls = BoxLayout(size_hint_y=None, height=50, spacing=10)

        # Play button
        self.play_btn = Button(
            text='Play',
            font_name='chinese',
            font_size='18',
            background_color=(0.6, 0.4, 0.75, 1),
            color=(1, 1, 1, 1),
            size_hint_x=None,
            width=80
        )
        self.play_btn.bind(on_press=self.toggle_play)
        controls.add_widget(self.play_btn)

        # Progress bar container
        progress_container = BoxLayout(orientation='vertical', spacing=2)

        # Time labels row
        time_labels = BoxLayout(size_hint_y=None, height=20, spacing=5)

        self.current_time_label = Label(
            text='0:00',
            font_name='chinese',
            font_size='13',
            color=(0.4, 0.4, 0.4, 1)
        )
        time_labels.add_widget(self.current_time_label)

        self.total_time_label = Label(
            text='0:00',
            font_name='chinese',
            font_size='13',
            color=(0.4, 0.4, 0.4, 1),
            halign='right'
        )
        time_labels.add_widget(self.total_time_label)

        progress_container.add_widget(time_labels)

        # Progress slider - simple and reliable
        self.progress_slider = Slider(
            min=0,
            max=100,
            value=0,
            value_track=True,
            value_track_color=(0.6, 0.4, 0.75, 1),
            value_track_width=3
        )
        progress_container.add_widget(self.progress_slider)

        controls.add_widget(progress_container)
        self.player_layout.add_widget(controls)

        # Track video state for progress updates
        self.total_frames = 0
        self.fps = 30
        self.is_seeking = False

        self.add_widget(main_layout)
        Clock.schedule_once(lambda dt: self.refresh(None), 0.3)

    def set_presenter(self, presenter):
        """Set the presenter for this screen"""
        self.presenter = presenter
        self.presenter.view = self

    def refresh(self, instance):
        """Refresh the video list"""
        self.show_list()
        self.video_list.clear_widgets()

        if not self.presenter:
            self.status_label.text = 'Presenter not available'
            return

        try:
            videos = self.presenter.get_video_list()

            if not videos:
                self.status_label.text = 'No recordings found'
                msg = Label(
                    text='No recordings found.\nStart recording from the Recording tab.',
                    font_name='chinese',
                    font_size='20',
                    color=(0.3, 0.3, 0.35, 1),
                    size_hint_y=None,
                    height=100,
                    halign='center',
                    valign='middle'
                )
                self.video_list.add_widget(msg)
                return

            self.status_label.text = f'Found {len(videos)} recording(s)'

            # Update timeline with videos
            self._update_timeline(videos)

            for video in videos:
                # Create video item
                item = self._create_video_item(video)
                self.video_list.add_widget(item)

        except Exception as e:
            self.status_label.text = 'Error loading videos'
            error_label = Label(
                text=f'Error: {str(e)}',
                font_name='chinese',
                font_size='18',
                color=(0.8, 0.2, 0.2, 1),
                size_hint_y=None,
                height=60
            )
            self.video_list.add_widget(error_label)
            import traceback
            traceback.print_exc()

    def _update_marker_size(self, instance, value):
        """Update marker container size to match timeline content"""
        if hasattr(self, 'marker_container'):
            self.marker_container.width = instance.width
            self.marker_container.height = instance.height

    def _update_marker_pos(self, instance, value):
        """Update marker container position"""
        if hasattr(self, 'marker_container'):
            self.marker_container.pos = instance.pos

    def _on_timeline_scroll(self, instance, value):
        """Handle timeline scroll event - update navigation slider"""
        if hasattr(self, 'timeline_nav_slider'):
            # Update the slider to match scroll position (only if not being dragged)
            # Check if the slider is not the source of the change
            try:
                self.timeline_nav_slider.value = value
            except:
                pass  # Ignore errors during binding

    def _on_nav_slider_change(self, instance, value):
        """Handle navigation slider change - scroll timeline"""
        if hasattr(self, 'marker_scroll'):
            # Scroll the timeline to match slider position
            self.marker_scroll.scroll_x = value

    def update_play_position(self, progress):
        """Update the play position indicator on timeline

        Args:
            progress: float between 0 and 1 representing play progress
        """
        if hasattr(self, 'timeline_content') and hasattr(self, 'play_indicator'):
            # Calculate position on timeline
            # Consider the padding (80px on each side) for accurate positioning
            padding = 80
            usable_width = self.timeline_content.width - (padding * 2)
            x_pos = padding + (progress * usable_width)

            # Update all three layers of the play indicator
            self.play_indicator_glow_outer.points = [x_pos, 43, x_pos, 47]
            self.play_indicator_glow.points = [x_pos, 44, x_pos, 46]
            self.play_indicator.points = [x_pos, 44.5, x_pos, 45.5]

    def _update_timeline_line(self, instance, value):
        """Update timeline line position"""
        if hasattr(self, 'timeline_line') and hasattr(self, 'timeline_content'):
            # Update line to span the entire width of timeline_content
            y = self.timeline_content.center_y
            width = self.timeline_content.width

            # Update all five line layers
            self.timeline_glow_ultra.points = [0, y, width, y]
            self.timeline_glow_outer.points = [0, y, width, y]
            self.timeline_glow_middle.points = [0, y, width, y]
            self.timeline_glow_inner.points = [0, y, width, y]
            self.timeline_line.points = [0, y, width, y]

            # Note: Tick marks are dynamically recreated in _update_timeline
            # so they don't need to be updated here

    def _update_timeline(self, videos):
        """Update timeline markers with videos"""
        self.marker_container.clear_widgets()
        self.marker_widgets = []

        if not videos:
            print("[VideoScreen] _update_timeline: No videos to display")
            return

        # Sort videos by timestamp
        sorted_videos = sorted(videos, key=lambda v: v.timestamp)
        print(f"[VideoScreen] _update_timeline: Found {len(sorted_videos)} videos")

        # Get the padding from marker_container (left and right are both 80)
        padding = 80
        padding_total = padding * 2

        # Adaptive spacing and size based on video count
        num_videos = len(sorted_videos)
        if num_videos <= 5:
            marker_size = 45  # Increased to accommodate time label
            spacing = 100  # Increased for better spread
        elif num_videos <= 15:
            marker_size = 40
            spacing = 90
        elif num_videos <= 30:
            marker_size = 36
            spacing = 80
        else:
            marker_size = 32
            spacing = 70

        # Calculate content width (markers + spacing between them)
        # The actual space needed for markers themselves
        content_width = num_videos * marker_size + (num_videos - 1) * (spacing - marker_size)

        # Calculate total width - include padding and ensure minimum width
        # Extended minimum width for more scrolling space
        total_width = max(2000, content_width + padding_total + 200)
        print(f"[VideoScreen] _update_timeline: total_width={total_width}, marker_size={marker_size}, spacing={spacing}")

        # Update timeline_content and marker_container width
        self.timeline_content.width = total_width
        self.marker_container.width = total_width

        # Update all timeline lines to span the ENTIRE width including padding
        if hasattr(self, 'timeline_line'):
            y = self.timeline_content.center_y
            # Update all five line layers
            self.timeline_glow_ultra.points = [0, y, total_width, y]
            self.timeline_glow_outer.points = [0, y, total_width, y]
            self.timeline_glow_middle.points = [0, y, total_width, y]
            self.timeline_glow_inner.points = [0, y, total_width, y]
            self.timeline_line.points = [0, y, total_width, y]

            # Note: Don't redraw canvas here - it's already drawn in __init__
            # We just update the line points above

        # Update BoxLayout spacing
        self.marker_container.spacing = max(10, spacing - marker_size)

        # Add all markers
        for i, video in enumerate(sorted_videos):
            # Create marker
            marker = TimelineMarker(
                video=video,
                size_hint=(None, None),
                size=(marker_size, marker_size)
            )

            # Use a closure to properly capture the video variable
            def make_play_callback(v):
                return lambda btn: self.play_video(v)

            marker.circle_btn.bind(on_press=make_play_callback(video))
            self.marker_container.add_widget(marker)
            self.marker_widgets.append(marker)

        print(f"[VideoScreen] _update_timeline: Added {len(self.marker_widgets)} markers to timeline")

    def _create_video_item(self, video):
        """Create a single video list item"""
        # Parse video info
        filename = os.path.basename(video.filename)
        duration_str = f"{video.duration:.1f}s"
        timestamp_str = video.timestamp.split('.')[0] if '.' in video.timestamp else video.timestamp
        frames_str = f"{video.frame_count} frames" if video.frame_count else "N/A"

        # Main container
        item = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=6,
            padding=12
        )

        # Add background
        with item.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.98, 0.96, 1.0, 1)
            item.bg_rect = Rectangle(pos=item.pos, size=item.size)

        def update_bg(instance, value):
            item.bg_rect.pos = instance.pos
            item.bg_rect.size = instance.size

        item.bind(pos=update_bg, size=update_bg)

        # Top row: filename + play button
        top_row = BoxLayout(size_hint_y=None, height=35, spacing=10)

        filename_label = Label(
            text=filename,
            font_name='chinese',
            font_size='18',
            bold=True,
            color=(0, 0, 0, 1),
            halign='left',
            valign='middle',
            text_size=(None, None)
        )
        top_row.add_widget(filename_label)

        # Buttons container
        buttons_layout = BoxLayout(size_hint_x=None, width=210, spacing=5)

        play_btn = Button(
            text='▶ Play',
            font_name='chinese',
            font_size='15',
            background_color=(0.6, 0.4, 0.75, 1),
            color=(1, 1, 1, 1),
            size_hint_x=None,
            width=100,
            size_hint_y=None,
            height=33
        )
        play_btn.bind(on_press=lambda inst, v=video: self.play_video(v))
        buttons_layout.add_widget(play_btn)

        delete_btn = Button(
            text='Delete',
            font_name='chinese',
            font_size='15',
            background_color=(0.8, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            size_hint_x=None,
            width=100,
            size_hint_y=None,
            height=33
        )
        delete_btn.bind(on_press=lambda inst, v=video: self.delete_video(v))
        buttons_layout.add_widget(delete_btn)

        top_row.add_widget(buttons_layout)

        item.add_widget(top_row)

        # Bottom row: details
        details = f'Duration: {duration_str}  |  Recorded: {timestamp_str}  |  Frames: {frames_str}'
        details_label = Label(
            text=details,
            font_name='chinese',
            font_size='16',
            color=(0.35, 0.35, 0.4, 1),
            halign='left',
            valign='middle',
            size_hint_y=None,
            height=20,
            text_size=(None, None)
        )
        item.add_widget(details_label)

        # Calculate total height
        item.height = 35 + 6 + 20 + 24  # rows + spacing + padding

        return item

    def show_list(self, instance=None):
        """Show video list"""
        self.content_area.clear_widgets()
        self.content_area.add_widget(self.list_layout)

        # Stop playback if playing
        if self.is_playing and self.presenter:
            self.is_playing = False
            self.play_btn.text = 'Play'
            self.presenter.stop_video()

    def play_video(self, video):
        """Play a video"""
        print(f"[VideoScreen] play_video called: {video.filename}")
        self.current_video = video

        # Show player
        self.content_area.clear_widgets()
        self.content_area.add_widget(self.player_layout)
        self.title_label.text = os.path.basename(video.filename)

        # Store video info for progress bar
        self.total_frames = video.frame_count or 0
        self.fps = video.fps or 30

        # Update info
        duration_str = f"{video.duration:.1f}s"
        timestamp_str = video.timestamp.split('.')[0] if '.' in video.timestamp else video.timestamp
        frames_str = f"{video.frame_count} frames" if video.frame_count else "N/A"

        info_text = f"Duration: {duration_str}  |  Frames: {frames_str}\nRecorded: {timestamp_str}"
        self.video_info_label.text = info_text

        # Reset progress bar
        self.progress_slider.value = 0
        self.progress_slider.max = max(1, self.total_frames)
        self.current_time_label.text = '0:00'
        self.total_time_label.text = self._format_time(video.duration)

        # Bind slider event - unbind first to avoid duplicates
        self.progress_slider.unbind(on_touch_up=self._on_slider_touch)
        self.progress_slider.bind(on_touch_up=self._on_slider_touch)

        # Load video
        if self.presenter:
            print(f"[VideoScreen] Loading video...")
            if self.presenter.load_video(video.filename):
                self.video_info_label.text = info_text + "\nReady to play"
                print(f"[VideoScreen] Video loaded successfully")
            else:
                self.video_info_label.text = "Failed to load video"
                print(f"[VideoScreen] Failed to load video")

    def _on_slider_touch(self, slider, touch):
        """Handle slider touch event"""
        if slider.collide_point(*touch.pos):
            # Seek when user releases the slider
            target_frame = int(slider.value)
            self._seek_to_frame(target_frame)

    def _seek_to_frame(self, frame_number):
        """Seek to a specific frame"""
        if not self.presenter or self.total_frames == 0:
            return

        # Pause if playing
        if self.is_playing:
            self.presenter.pause_video()

        # Update time label
        current_time = frame_number / self.fps
        self.current_time_label.text = self._format_time(current_time)

        # Seek via presenter
        self.presenter.seek_to_frame(frame_number)

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
            self.is_playing = False
            self.play_btn.text = 'Play'
        else:
            # Play
            print("[VideoScreen] Starting video playback...")
            if self.presenter.play_video():
                self.is_playing = True
                self.play_btn.text = 'Pause'
                print("[VideoScreen] Playback started successfully")
            else:
                print("[VideoScreen] Failed to start playback")

    def on_playback_frame(self, frame, frame_number):
        """Callback when a new frame is available during playback"""
        # Schedule display update on main thread using Clock
        def update_frame(dt):
            self._display_frame(frame)

            # Update progress bar if not seeking
            if not self.is_seeking and self.total_frames > 0:
                self.progress_slider.value = frame_number
                current_time = frame_number / self.fps
                self.current_time_label.text = self._format_time(current_time)

                # Update timeline play position indicator
                progress = frame_number / self.total_frames if self.total_frames > 0 else 0
                self.update_play_position(progress)

        Clock.schedule_once(update_frame)

    def on_playback_finished(self):
        """Callback when playback finishes"""
        def update_ui(dt):
            self.is_playing = False
            self.play_btn.text = 'Play'
            # Update progress to end
            self.progress_slider.value = self.total_frames
            if self.total_frames > 0:
                current_time = self.total_frames / self.fps
                self.current_time_label.text = self._format_time(current_time)
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

    def _format_time(self, seconds):
        """Format seconds to MM:SS"""
        if not seconds or seconds <= 0:
            return "0:00"

        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def delete_video(self, video):
        """Delete a video file"""
        print(f"[VideoScreen] delete_video called: {video.filename}")

        # Check if file exists
        if not os.path.exists(video.filename):
            self.status_label.text = 'File already deleted'
            # Still need to refresh to clean up UI
            Clock.schedule_once(lambda dt: self._do_refresh(), 0.1)
            return

        try:
            # Delete the file
            os.remove(video.filename)
            print(f"[VideoScreen] Deleted: {video.filename}")
            self.status_label.text = 'Video deleted successfully'

            # Also delete from database through presenter
            if self.presenter:
                self.presenter.delete_video(video.filename)

            # Refresh the list immediately
            Clock.schedule_once(lambda dt: self._do_refresh(), 0.1)

        except Exception as e:
            print(f"[VideoScreen] Error deleting video: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.text = f'Delete failed: {str(e)}'

    def _do_refresh(self):
        """Internal refresh method"""
        self.refresh(None)

    def on_playback_stopped(self):
        """Callback when playback is stopped"""
        self.is_playing = False
        self.play_btn.text = 'Play'

    def on_frame_changed(self, frame, frame_number):
        """Callback when frame changes (seek)"""
        # Display frame immediately
        self._display_frame(frame)

    def on_video_deleted(self, filename):
        """Callback when video is deleted"""
        pass  # Could refresh list here


class ProcessScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_tracking = False
        self.current_session_events = []
        self.selected_session_id = None  # Track selected session

        layout = BoxLayout(orientation='vertical', spacing=12, padding=20)

        # Title
        title = Label(
            text='Process Mining',
            font_name='Roboto',  # 使用Roboto字体
            font_size='32',
            bold=True,
            size_hint_y=None,
            height=55,
            color=(0, 0, 0, 1)
        )
        layout.add_widget(title)

        # Start Tracking button (full width)
        self.track_btn = Button(
            text='Start Tracking',
            font_name='Roboto',  # 使用Roboto字体
            font_size='24',
            bold=True,
            size_hint_y=None,
            height=60,
            background_color=(0.6, 0.4, 0.75, 1),
            color=(1, 1, 1, 1)
        )
        self.track_btn.bind(on_press=self.toggle)
        layout.add_widget(self.track_btn)

        # Current Session Stats
        self.session_stats = Label(
            text='Events: 0 | Keystrokes: 0 | Mouse Clicks: 0',
            font_name='Roboto',  # 使用Roboto字体
            font_size='18',
            size_hint_y=None,
            height=40,
            color=(0.4, 0.4, 0.4, 1),
            halign='center'
        )
        layout.add_widget(self.session_stats)

        # Current Session Section (15% height)
        session_label = Label(
            text='Current Session',
            font_name='Roboto',  # 使用Roboto字体
            font_size='20',
            bold=True,
            size_hint_y=None,
            height=40,
            color=(0, 0, 0, 1),
            halign='left'
        )
        layout.add_widget(session_label)

        session_scroll = ScrollView(size_hint_y=0.10)
        self.session_events = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5, padding=10)
        self.session_events.bind(minimum_height=self.session_events.setter('height'))
        session_scroll.add_widget(self.session_events)
        layout.add_widget(session_scroll)

        # Session History Section (50% height)
        history_header = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)

        history_label = Label(
            text='Session History',
            font_name='Roboto',  # 使用Roboto字体
            font_size='20',
            bold=True,
            size_hint_x=0.6,
            color=(0, 0, 0, 1),
            halign='left'
        )
        history_header.add_widget(history_label)

        # Refresh button
        refresh_btn = Button(
            text='Refresh',
            font_name='Roboto',
            font_size='16',
            size_hint_x=0.2,
            background_color=(0.3, 0.6, 0.9, 1),
            color=(1, 1, 1, 1)
        )
        refresh_btn.bind(on_press=self._refresh_history)
        history_header.add_widget(refresh_btn)

        # Delete All button
        delete_all_btn = Button(
            text='Clear All',
            font_name='Roboto',
            font_size='16',
            size_hint_x=0.2,
            background_color=(0.8, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        delete_all_btn.bind(on_press=self._delete_all_sessions)
        history_header.add_widget(delete_all_btn)

        layout.add_widget(history_header)

        # Add spacing between header and list
        spacing_widget = Widget(size_hint_y=None, height=15)
        layout.add_widget(spacing_widget)

        history_scroll = ScrollView(size_hint_y=0.50)
        self.history_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10, padding=(10, 20, 10, 10))
        self.history_list.bind(minimum_height=self.history_list.setter('height'))
        history_scroll.add_widget(self.history_list)
        layout.add_widget(history_scroll)

        # Session Analysis Section (40% height, centered)
        analysis_label = Label(
            text='Session Analysis',
            font_name='Roboto',  # 使用Roboto字体
            font_size='20',
            bold=True,
            size_hint_y=None,
            height=40,
            color=(0, 0, 0, 1),
            halign='center'
        )
        layout.add_widget(analysis_label)

        # Analysis result display with ScrollView (centered)
        analysis_scroll = ScrollView(
            size_hint_y=0.4,
            scroll_type=['content', 'bars'],
            bar_width=8,
            bar_color=(0.6, 0.4, 0.75, 0.8),
            bar_inactive_color=(0.6, 0.4, 0.75, 0.3),
            do_scroll_x=False,
            do_scroll_y=True
        )
        self.analysis_result = BoxLayout(
            orientation='vertical',
            spacing=8,
            size_hint_y=None,
            padding=20
        )
        self.analysis_result.bind(minimum_height=self.analysis_result.setter('height'))

        self.analysis_content = Label(
            text='Select a session to view analysis\n\nTap on any session in Session History to see detailed categorization',
            font_name='Roboto',  # 使用Roboto字体
            font_size='18',
            color=(0.5, 0.5, 0.5, 1),
            halign='center',
            valign='top',
            text_size=(650, None),
            size_hint_y=None,
            size_hint_x=1
        )
        self.analysis_content.bind(texture_size=self.analysis_content.setter('size'))
        self.analysis_result.add_widget(self.analysis_content)
        analysis_scroll.add_widget(self.analysis_result)
        layout.add_widget(analysis_scroll)

        self.add_widget(layout)

        # Load history on init
        self._load_history()

    def toggle(self, instance):
        if not self.is_tracking:
            self.start()
        else:
            self.stop()

    def start(self):
        self.is_tracking = True
        self.track_btn.text = "Stop Tracking"
        self.track_btn.background_color = (0.75, 0.3, 0.4, 1)
        self._add_session_event("Tracking started")
        self._update_session_stats()

    def stop(self):
        self.is_tracking = False
        self.track_btn.text = "Start Tracking"
        self.track_btn.background_color = (0.6, 0.4, 0.75, 1)
        self._add_session_event("Tracking stopped")

        # Save session to history
        if len(self.current_session_events) > 1:
            self._save_session()

    def _add_session_event(self, text, event_type="info"):
        """Add event to current session"""
        import datetime

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        color_map = {
            "info": (0.2, 0.2, 0.2, 1),
            "keypress": (0.1, 0.3, 0.5, 1),
            "click": (0.5, 0.3, 0.1, 1),
            "success": (0.1, 0.5, 0.2, 1)
        }

        event_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=38)

        time_label = Label(
            text=timestamp,
            font_name='Roboto',  # 使用Roboto字体
            font_size='16',
            size_hint_x=0.15,
            color=(0.5, 0.5, 0.5, 1)
        )
        event_box.add_widget(time_label)

        event_label = Label(
            text=text,
            font_name='Roboto',  # 使用Roboto字体
            font_size='17',
            size_hint_x=0.85,
            color=color_map.get(event_type, (0.2, 0.2, 0.2, 1)),
            halign='left',
            text_size=(400, None)
        )
        event_label.bind(texture_size=event_label.setter('size'))
        event_box.add_widget(event_label)

        self.session_events.add_widget(event_box)
        self.current_session_events.append({"time": timestamp, "text": text, "type": event_type})

    def _update_session_stats(self):
        """Update session statistics display"""
        keystrokes = sum(1 for e in self.current_session_events if e["type"] == "keypress")
        clicks = sum(1 for e in self.current_session_events if e["type"] == "click")
        total = len(self.current_session_events)

        self.session_stats.text = f'Events: {total} | Keystrokes: {keystrokes} | Mouse Clicks: {clicks}'

    def _save_session(self):
        """Save current session to history"""
        import sqlite3
        import datetime

        try:
            conn = sqlite3.connect('./db/process_mining.db')
            cursor = conn.cursor()

            # Create table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT,
                    end_time TEXT,
                    event_count INTEGER,
                    keystrokes INTEGER,
                    clicks INTEGER,
                    events_json TEXT
                )
            ''')

            # Calculate stats
            keystrokes = sum(1 for e in self.current_session_events if e["type"] == "keypress")
            clicks = sum(1 for e in self.current_session_events if e["type"] == "click")

            start_time = self.current_session_events[0]["time"] if self.current_session_events else ""
            end_time = self.current_session_events[-1]["time"] if self.current_session_events else ""

            import json
            events_json = json.dumps(self.current_session_events)

            # Insert session
            cursor.execute('''
                INSERT INTO sessions (start_time, end_time, event_count, keystrokes, clicks, events_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (start_time, end_time, len(self.current_session_events), keystrokes, clicks, events_json))

            conn.commit()
            conn.close()

            # Refresh history
            self._load_history()

            # Clear current session
            self.current_session_events = []
            self.session_events.clear_widgets()
            self._update_session_stats()

            self._add_session_event("Session saved to history", "success")

        except Exception as e:
            print(f"[ProcessScreen] Error saving session: {e}")

    def _load_history(self):
        """Load session history from database"""
        import sqlite3

        try:
            conn = sqlite3.connect('./db/process_mining.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, start_time, end_time, event_count, keystrokes, clicks
                FROM sessions
                ORDER BY id DESC
                LIMIT 20
            ''')

            sessions = cursor.fetchall()
            conn.close()

            # Clear existing history
            self.history_list.clear_widgets()

            if not sessions:
                # Show empty message
                empty_label = Label(
                    text='No session history yet. Start tracking to record your workflow!',
                    font_name='chinese',
                    font_size='16',
                    size_hint_y=None,
                    height=60,
                    color=(0.5, 0.5, 0.5, 1),
                    halign='center',
                    valign='middle'
                )
                self.history_list.add_widget(empty_label)
            else:
                # Display sessions
                for session_id, start_time, end_time, event_count, keystrokes, clicks in sessions:
                    session_item = self._create_session_item(session_id, start_time, end_time, event_count, keystrokes, clicks)
                    self.history_list.add_widget(session_item)

        except Exception as e:
            print(f"[ProcessScreen] Error loading history: {e}")

    def _create_session_item(self, session_id, start_time, end_time, event_count, keystrokes, clicks):
        """Create a clickable session history item widget"""
        from kivy.metrics import dp

        # Main container
        item_box = BoxLayout(
            orientation='vertical',
            spacing=12,
            size_hint_y=None,
            padding=dp(18)
        )

        # Store session data
        item_box.session_id = session_id
        item_box.start_time = start_time
        item_box.end_time = end_time
        item_box.event_count = event_count
        item_box.keystrokes = keystrokes
        item_box.clicks = clicks
        item_box.delete_btn = None  # Will be set later

        # Add touch/click handler
        def on_touch_down(instance, touch):
            if instance.collide_point(*touch.pos):
                # Check if touch is on delete button
                if item_box.delete_btn and item_box.delete_btn.collide_point(*touch.pos):
                    # Let the button handle the click
                    return False
                # Otherwise, handle as session item click
                print(f"[ProcessScreen] Session #{session_id} selected")
                self._show_session_analysis(session_id, start_time, end_time, event_count, keystrokes, clicks)
                return True

        item_box.bind(on_touch_down=on_touch_down)

        # Header with time and stats
        header = BoxLayout(orientation='horizontal', spacing=15, size_hint_y=None, height=35)

        time_label = Label(
            text=f'Session #{session_id} • {start_time}',
            font_name='Roboto',
            font_size='19',
            bold=True,
            size_hint_x=0.55,
            color=(0, 0, 0, 1),
            halign='left',
            valign='middle',
            text_size=(250, None)
        )
        header.add_widget(time_label)

        stats_label = Label(
            text=f'{event_count} actions • {keystrokes} keys',
            font_name='Roboto',
            font_size='17',
            size_hint_x=0.45,
            color=(0.5, 0.5, 0.5, 1),
            halign='right',
            valign='middle',
            text_size=(250, None)
        )
        header.add_widget(stats_label)

        item_box.add_widget(header)

        # Combined row: duration + hint + delete button
        combined_row = BoxLayout(
            orientation='horizontal',
            spacing=10,
            size_hint_y=None,
            height=30
        )

        # Duration label (left side)
        duration_label = Label(
            text=f'{start_time} → {end_time}',
            font_name='Roboto',
            font_size='15',
            size_hint_x=0.45,
            color=(0.4, 0.4, 0.4, 1),
            halign='left',
            valign='middle',
            text_size=(200, None)
        )
        combined_row.add_widget(duration_label)

        # Hint label (middle)
        hint_label = Label(
            text='Tap to analyze',
            font_name='Roboto',
            font_size='16',
            size_hint_x=0.35,
            color=(0.6, 0.4, 0.75, 1),
            halign='center',
            valign='middle',
            text_size=(200, None)
        )
        combined_row.add_widget(hint_label)

        # Delete button (right side)
        delete_btn = Button(
            text='Delete',
            font_name='Roboto',
            font_size='14',
            size_hint_x=0.20,
            background_color=(0.9, 0.4, 0.4, 1),
            color=(1, 1, 1, 1)
        )

        def delete_session(instance):
            self._delete_session(session_id)

        delete_btn.bind(on_press=delete_session)
        combined_row.add_widget(delete_btn)

        # Store delete button reference for touch handling
        item_box.delete_btn = delete_btn

        item_box.add_widget(combined_row)

        # Separator line
        separator = Widget(size_hint_y=None, height=2)
        with separator.canvas.before:
            Color(0.85, 0.85, 0.85, 1)
            Rectangle(pos=separator.pos, size=separator.size)

        item_box.add_widget(separator)

        return item_box

    def _show_session_detail(self, session_id, start_time, end_time):
        """Show session detail popup with events and pattern analysis

        Note: This feature is temporarily disabled. Will be re-enabled in future versions.
        """
        try:
            # TODO: Implement session detail popup with event timeline and pattern analysis
            pass
        except Exception as e:
            import logging
            logging.error(f"Failed to show session detail: {e}")

    def _refresh_history(self, instance):
        """Refresh the session history list"""
        self._load_history()
        self._add_session_event("History refreshed", "success")

    def _delete_session(self, session_id):
        """Delete a specific session from database"""
        import sqlite3

        try:
            conn = sqlite3.connect('./db/process_mining.db')
            cursor = conn.cursor()

            cursor.execute('DELETE FROM sessions WHERE id=?', (session_id,))
            conn.commit()
            deleted_count = cursor.rowcount
            conn.close()

            if deleted_count > 0:
                print(f"[ProcessScreen] Session #{session_id} deleted")
                self._load_history()
                self._add_session_event(f"Session #{session_id} deleted", "success")
            else:
                print(f"[ProcessScreen] Session #{session_id} not found")

        except Exception as e:
            print(f"[ProcessScreen] Error deleting session: {e}")
            import traceback
            traceback.print_exc()

    def _delete_all_sessions(self, instance):
        """Delete all sessions from database"""
        import sqlite3

        try:
            conn = sqlite3.connect('./db/process_mining.db')
            cursor = conn.cursor()

            # Get count before deleting
            cursor.execute('SELECT COUNT(*) FROM sessions')
            count = cursor.fetchone()[0]

            if count == 0:
                conn.close()
                self._add_session_event("No sessions to delete", "info")
                return

            # Delete all sessions
            cursor.execute('DELETE FROM sessions')
            conn.commit()
            conn.close()

            print(f"[ProcessScreen] All {count} sessions deleted")
            self._load_history()
            self._add_session_event(f"All {count} sessions deleted", "success")

        except Exception as e:
            print(f"[ProcessScreen] Error deleting all sessions: {e}")
            import traceback
            traceback.print_exc()

    def _show_session_analysis(self, session_id, start_time, end_time, event_count, keystrokes, clicks):
        """Show categorized analysis of selected session"""
        import sqlite3
        import json

        try:
            # Load events from database
            conn = sqlite3.connect('./db/process_mining.db')
            cursor = conn.cursor()
            cursor.execute('SELECT events_json FROM sessions WHERE id=?', (session_id,))
            result = cursor.fetchone()
            conn.close()

            if not result:
                self.analysis_content.text = f'No data found for Session #{session_id}'
                self.analysis_content.color = (0.5, 0.5, 0.5, 1)
                return

            events = json.loads(result[0])

            # Categorize activities
            categories = self._categorize_activities(events)
            patterns = self._analyze_patterns(events)

            # Format duration
            duration_min = patterns['duration_minutes']
            duration_str = f"{duration_min:.1f} min" if duration_min > 0 else "N/A"

            # Build analysis text (centered layout)
            analysis_text = f'''
════════════════════════════════════════
           Session #{session_id} Analysis
════════════════════════════════════════

ACTIVITY BREAKDOWN
════════════════════════════════════════
  Typing:        {categories['typing']['percentage']:>3}%
  Browsing:      {categories['browsing']['percentage']:>3}%
  Design:        {categories['design']['percentage']:>3}%
  Programming:   {categories['programming']['percentage']:>3}%
  Communication: {categories['communication']['percentage']:>3}%
  Documents:     {categories['document']['percentage']:>3}%
  Gaming:        {categories['gaming']['percentage']:>3}%
  Other:         {categories['other']['percentage']:>3}%

════════════════════════════════════════
SESSION STATISTICS
════════════════════════════════════════
  Total Events:       {event_count:>6}
  Keystrokes:         {keystrokes:>6}
  Mouse Clicks:       {clicks:>6}
  Duration:           {duration_str:>6}
  Events/min:         {patterns['avg_events_per_minute']:>6.1f}
  Click Intensity:    {patterns['click_ratio']*100:>5.1f}%

════════════════════════════════════════
PRIMARY ACTIVITY: {categories['primary'].upper()}
════════════════════════════════════════

Top Keys: {', '.join(patterns['top_keys'][:3])}

Time: {start_time} → {end_time}
'''
            # Update analysis display (centered)
            self.analysis_content.text = analysis_text
            self.analysis_content.color = (0.2, 0.2, 0.2, 1)
            self.analysis_content.halign = 'center'
            self.analysis_content.valign = 'top'
            self.analysis_content.text_size = (650, None)

            print(f"[ProcessScreen] Analysis displayed for Session #{session_id}")

        except Exception as e:
            print(f"[ProcessScreen] Error showing analysis: {e}")
            import traceback
            traceback.print_exc()
            self.analysis_content.text = f'Error loading analysis: {str(e)}'
            self.analysis_content.color = (0.8, 0.3, 0.3, 1)

    def _categorize_activities(self, events):
        """Categorize events into detailed activity types"""
        typing_score = 0
        browsing_score = 0
        design_score = 0
        programming_score = 0
        communication_score = 0
        document_score = 0
        gaming_score = 0
        other_score = 0

        for event in events:
            event_type = event.get("type", "")
            text = event.get("text", "").lower()

            # Typing indicators (general keyboard activity)
            if event_type == "keypress":
                typing_score += 1

            # Browsing indicators
            if any(word in text for word in ["scroll", "browser", "chrome", "safari", "firefox", "edge", "webkit", "navigator"]):
                browsing_score += 2

            # Design indicators
            if any(word in text for word in ["figma", "sketch", "design", "draw", "paint", "canvas", "adobe", "photoshop", "illustrator"]):
                design_score += 3

            # Programming indicators
            if any(word in text for word in ["code", "python", "javascript", "java", "terminal", "console", "debug", "compile", "git", "vscode", "intellij", "vim", "emacs", "function", "class", "import"]):
                programming_score += 3

            # Communication indicators
            if any(word in text for word in ["slack", "teams", "zoom", "meet", "chat", "message", "email", "outlook", "telegram", "whatsapp", "discord"]):
                communication_score += 2

            # Document editing indicators
            if any(word in text for word in ["word", "excel", "powerpoint", "docs", "sheets", "slides", "notion", "evernote", "text", "edit", "document", "write"]):
                document_score += 2

            # Gaming indicators
            if any(word in text for word in ["game", "play", "steam", "epic", "minecraft", "lol", "valorant", "overwatch", "fps", "rpg"]):
                gaming_score += 3

            # General activity (baseline)
            other_score += 0.5

        # Calculate total and percentages
        total = typing_score + browsing_score + design_score + programming_score + communication_score + document_score + gaming_score + other_score

        if total == 0:
            return {
                'typing': {'score': 0, 'percentage': 0},
                'browsing': {'score': 0, 'percentage': 0},
                'design': {'score': 0, 'percentage': 0},
                'programming': {'score': 0, 'percentage': 0},
                'communication': {'score': 0, 'percentage': 0},
                'document': {'score': 0, 'percentage': 0},
                'gaming': {'score': 0, 'percentage': 0},
                'other': {'score': 0, 'percentage': 100},
                'primary': 'Unknown'
            }

        typing_pct = int((typing_score / total) * 100)
        browsing_pct = int((browsing_score / total) * 100)
        design_pct = int((design_score / total) * 100)
        programming_pct = int((programming_score / total) * 100)
        communication_pct = int((communication_score / total) * 100)
        document_pct = int((document_score / total) * 100)
        gaming_pct = int((gaming_score / total) * 100)
        other_pct = 100 - typing_pct - browsing_pct - design_pct - programming_pct - communication_pct - document_pct - gaming_pct

        # Determine primary activity
        scores = {
            'Typing': typing_pct,
            'Browsing': browsing_pct,
            'Design': design_pct,
            'Programming': programming_pct,
            'Communication': communication_pct,
            'Documents': document_pct,
            'Gaming': gaming_pct,
            'Other': other_pct
        }
        primary = max(scores, key=scores.get)

        return {
            'typing': {'score': typing_score, 'percentage': typing_pct},
            'browsing': {'score': browsing_score, 'percentage': browsing_pct},
            'design': {'score': design_score, 'percentage': design_pct},
            'programming': {'score': programming_score, 'percentage': programming_pct},
            'communication': {'score': communication_score, 'percentage': communication_pct},
            'document': {'score': document_score, 'percentage': document_pct},
            'gaming': {'score': gaming_score, 'percentage': gaming_pct},
            'other': {'score': other_score, 'percentage': other_pct},
            'primary': primary
        }

    def _analyze_patterns(self, events):
        """Analyze patterns in session events"""
        from collections import Counter
        import datetime

        # Extract key presses
        key_events = [e for e in events if e.get("type") == "keypress"]
        click_events = [e for e in events if e.get("type") == "click"]

        # Count top keys
        key_texts = []
        for e in key_events:
            text = e.get("text", "")
            if "Key press:" in text:
                key = text.split("Key press:")[-1].strip().strip("'\"")
                key_texts.append(key)

        top_keys = [k for k, v in Counter(key_texts).most_common(5)]

        # Calculate duration
        if len(events) >= 2:
            try:
                start_time = datetime.datetime.strptime(events[0]["time"], "%H:%M:%S")
                end_time = datetime.datetime.strptime(events[-1]["time"], "%H:%M:%S")
                duration_minutes = (end_time - start_time).total_seconds() / 60
                if duration_minutes < 0:  # Handle midnight crossover
                    duration_minutes = 24 * 60 + duration_minutes
            except:
                duration_minutes = 0
        else:
            duration_minutes = 0

        # Calculate metrics
        avg_events_per_minute = len(events) / duration_minutes if duration_minutes > 0 else 0
        click_ratio = len(click_events) / len(events) if events else 0

        return {
            "top_keys": top_keys if top_keys else ["N/A"],
            "avg_events_per_minute": avg_events_per_minute,
            "click_ratio": click_ratio,
            "duration_minutes": duration_minutes
        }

    def _create_detail_event_item(self, event):
        """Create a single event item for detail view"""
        from kivy.metrics import dp

        item = BoxLayout(
            orientation='horizontal',
            spacing=10,
            size_hint_y=None,
            height=dp(30),
            padding=dp(5)
        )

        # Time label
        time_label = Label(
            text=event.get("time", ""),
            font_name='chinese',
            font_size='12',
            size_hint_x=0.2,
            color=(0.5, 0.5, 0.5, 1)
        )
        item.add_widget(time_label)

        # Event text
        text_label = Label(
            text=event.get("text", ""),
            font_name='chinese',
            font_size='13',
            size_hint_x=0.8,
            color=(0.2, 0.2, 0.2, 1),
            halign='left',
            text_size=(None, None)
        )
        item.add_widget(text_label)

        return item


class AboutScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Main scrollable layout
        scroll = ScrollView()
        main_layout = BoxLayout(orientation='vertical', spacing=20, padding=30, size_hint_y=None)
        main_layout.bind(minimum_height=main_layout.setter('height'))
        scroll.add_widget(main_layout)

        # Author section
        author_box = self._create_section_box("About MemScreen", [
            ("Developer", "Jixiang Luo"),
            ("Email", "jixiangluo85@gmail.com"),
            ("Version", "v0.4.0"),
            ("License", "MIT License - Copyright 2026")
        ])
        main_layout.add_widget(author_box)

        self.add_widget(scroll)

    def _create_section_box(self, title, items):
        """Create a nicely formatted section box"""
        from kivy.metrics import dp

        section_layout = BoxLayout(orientation='vertical', spacing=12, size_hint_y=None, padding=dp(20))
        section_layout.bind(minimum_height=section_layout.setter('height'))

        # Section title
        title_label = Label(
            text=title,
            font_name='chinese',
            font_size=dp(20),
            bold=True,
            size_hint_y=None,
            height=dp(45),
            color=(0.4, 0.2, 0.6, 1),  # Purple
            halign='left',
            valign='middle',
            text_size=(None, dp(45))
        )
        section_layout.add_widget(title_label)

        # Separator line
        sep = BoxLayout(size_hint_y=None, height=dp(2))
        with sep.canvas.before:
            Color(0.7, 0.65, 0.75, 1)  # Light purple separator
            sep_bg = Rectangle(pos=sep.pos, size=sep.size)
        sep.bind(pos=lambda i,v: setattr(sep_bg, 'pos', i.pos),
                size=lambda i,v: setattr(sep_bg, 'size', i.size))
        section_layout.add_widget(sep)

        # Items
        for label, value in items:
            if not label:  # Continuation line
                item_label = Label(
                    text=f"  {value}",
                    font_name='chinese',
                    font_size=dp(15),
                    size_hint_y=None,
                    height=dp(30),
                    color=(0.3, 0.3, 0.3, 1),
                    halign='left',
                    valign='middle',
                    text_size=(None, dp(30))
                )
            else:
                item_label = Label(
                    text=f"[b]{label}:[/b]  {value}",
                    font_name='chinese',
                    font_size=dp(15),
                    size_hint_y=None,
                    height=dp(30),
                    color=(0, 0, 0, 1),
                    halign='left',
                    valign='middle',
                    markup=True,
                    text_size=(None, dp(30))
                )
            section_layout.add_widget(item_label)

        # Background for the section
        with section_layout.canvas.before:
            Color(0.98, 0.96, 1.0, 1)  # Very light purple background
            section_bg = Rectangle(pos=section_layout.pos, size=section_layout.size)
        section_layout.bind(pos=lambda i,v: setattr(section_bg, 'pos', i.pos),
                          size=lambda i,v: setattr(section_bg, 'size', i.size))

        # Border
        with section_layout.canvas.before:
            Color(0.6, 0.5, 0.7, 1)  # Purple border
            section_border = Line(rectangle=[section_layout.x, section_layout.y,
                                            section_layout.width, section_layout.height],
                                  width=1.5)
        section_layout.bind(pos=lambda i,v: self._update_border(section_border, i),
                          size=lambda i,v: self._update_border(section_border, i))

        return section_layout

    def _update_border(self, border, widget):
        """Update border rectangle position and size"""
        border.rectangle = [widget.x, widget.y, widget.width, widget.height]


class MemScreenApp(App):
    def build(self):
        # Set window title
        from kivy.core.window import Window
        Window.title = "MemScreen v0.4.0"

        # Memory
        try:
            config = MemoryConfig(
                embedder=EmbedderConfig(provider="ollama", config={"model": "nomic-embed-text"}),
                vector_store=VectorStoreConfig(provider="chroma", config={"path": "./db/chroma_db"}),
                llm=LlmConfig(provider="ollama", config={"model": "qwen3:1.7b", "max_tokens": 512, "temperature": 0.7})
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
            ('settings', 'About'),
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
        self.sm.add_widget(AboutScreen(name='settings', memory_system=self.memory))

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
    MemScreenApp().run()
