### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT               ###

"""
Video Screen for viewing recordings - Kivy Version
"""

import os
import sqlite3
import cv2
from datetime import datetime
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.lang import Builder
from kivy.graphics.texture import Texture
from kivy.utils import platform

from .base_screen import BaseScreen
from ..components.colors_kivy import *


class VideoScreen(BaseScreen):
    """Video playback screen with Kivy UI"""

    # UI Components
    video_list = ObjectProperty(None)
    video_image = ObjectProperty(None)
    video_info = ObjectProperty(None)
    play_button = ObjectProperty(None)
    timeline_slider = ObjectProperty(None)
    timecode_label = ObjectProperty(None)

    # State
    current_video_path = StringProperty(None)
    current_video_id = NumericProperty(-1)
    is_playing = BooleanProperty(False)
    current_time = NumericProperty(0.0)
    total_time = NumericProperty(0.0)
    fps = NumericProperty(30.0)

    # Video data
    video_paths = []
    video_ids = []
    video_capture = None
    _playback_event = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_texture_event = None

    def on_enter(self):
        """Called when screen is displayed"""
        # Auto-load video list
        Clock.schedule_once(self._load_video_list, 0.3)

    def on_leave(self):
        """Called when leaving screen"""
        # Stop playback
        self.stop_playback()

    def _load_video_list(self, dt):
        """Load video list from database"""
        if self.presenter:
            videos = self.presenter.get_video_list()
            self._update_video_list(videos)

    def _update_video_list(self, videos):
        """Update video list UI"""
        self.video_paths = []
        self.video_ids = []

        if self.video_list:
            self.video_list.data = []

            for video_info in videos:
                filename = video_info.get('filename', '')
                timestamp = video_info.get('timestamp', '')
                duration = video_info.get('duration', 0)
                video_id = video_info.get('id', 0)

                # Format display text
                try:
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                except:
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

                formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                minutes, seconds = divmod(int(duration), 60)
                display_text = f"{formatted_time} - {minutes:02d}:{seconds:02d}"

                # Add to list
                self.video_list.data.append({
                    'text': display_text,
                    'filename': filename,
                    'video_id': video_id,
                    'on_release': lambda v=video_info: self._on_video_select(v)
                })

                self.video_paths.append(filename)
                self.video_ids.append(video_id)

            print(f"[VideoScreen] Loaded {len(videos)} videos")

    def _on_video_select(self, video_info):
        """Handle video selection"""
        self.current_video_path = video_info.get('filename', '')
        self.current_video_id = video_info.get('id', -1)

        print(f"[VideoScreen] Selected video: {self.current_video_path}")

        # Load video
        self._load_video(self.current_video_path)

    def _load_video(self, filepath):
        """Load video for playback"""
        # Stop any existing playback
        self.stop_playback()

        # Release previous capture
        if self.video_capture:
            self.video_capture.release()

        # Open video
        self.video_capture = cv2.VideoCapture(filepath)

        if self.video_capture.isOpened():
            # Get video properties
            total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS) or 30.0
            self.total_time = total_frames / self.fps
            self.current_time = 0.0

            # Update timeline
            if self.timeline_slider:
                self.timeline_slider.max = self.total_time
                self.timeline_slider.value = 0

            # Show first frame
            self._show_frame(0)

            # Update info
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                size_mb = file_size / (1024 * 1024)

                info_text = f"📁 {os.path.basename(filepath)}\n"
                info_text += f"⏱️ {self.total_time:.1f}s | 📊 {size_mb:.1f} MB"

                if self.video_info:
                    self.video_info.text = info_text

            print(f"[VideoScreen] Video loaded: {self.total_time:.1f}s @ {self.fps:.1f}fps")

    def _show_frame(self, frame_pos):
        """Show specific frame"""
        if not self.video_capture or not self.video_capture.isOpened():
            return

        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        ret, frame = self.video_capture.read()

        if ret and self.video_image:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Create Kivy texture
            height, width = rgb_frame.shape[:2]
            texture = Texture.create(size=(width, height), colorfmt='rgb')
            texture.blit_buffer(rgb_frame.tobytes(), colorfmt='rgb', bufferfmt='ubyte')

            # Flip for Kivy
            texture.flip_vertical()

            # Display
            self.video_image.texture = texture
            self.video_image.norm = True
            self.video_image.allow_stretch = True

    def toggle_play(self):
        """Toggle play/pause"""
        if not self.video_capture or not self.video_capture.isOpened():
            return

        self.is_playing = not self.is_playing

        if self.is_playing:
            # Update button
            if self.play_button:
                self.play_button.text = "⏸️"

            # Start playback
            self._start_playback()
        else:
            # Update button
            if self.play_button:
                self.play_button.text = "▶️"

            # Stop playback
            self._stop_playback_loop()

    def _start_playback(self):
        """Start video playback"""
        if self._playback_event is None:
            self._playback_event = Clock.schedule_interval(self._playback_frame, 1.0 / self.fps)

    def _stop_playback_loop(self):
        """Stop playback loop"""
        if self._playback_event:
            self._playback_event.cancel()
            self._playback_event = None

    def stop_playback(self):
        """Stop playback completely"""
        self.is_playing = False
        self._stop_playback_loop()

        if self.play_button:
            self.play_button.text = "▶️"

    def _playback_frame(self, dt):
        """Play next frame"""
        if not self.is_playing or not self.video_capture or not self.video_capture.isOpened():
            return False

        ret, frame = self.video_capture.read()

        if ret:
            # Convert and display
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width = rgb_frame.shape[:2]

            if self.video_image:
                texture = Texture.create(size=(width, height), colorfmt='rgb')
                texture.blit_buffer(rgb_frame.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                texture.flip_vertical()
                self.video_image.texture = texture

            # Update timeline
            current_pos = self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)
            self.current_time = current_pos / self.fps

            if self.timeline_slider:
                self.timeline_slider.value = self.current_time

            # Update timecode
            self._update_timecode(self.current_time)

            return True  # Continue playback
        else:
            # Video ended
            self.stop_playback()
            self._reset_to_start()
            return False

    def _reset_to_start(self):
        """Reset video to start"""
        if self.video_capture and self.video_capture.isOpened():
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_time = 0
            if self.timeline_slider:
                self.timeline_slider.value = 0
            self._show_frame(0)
            self._update_timecode(0)

    def _update_timecode(self, time_seconds):
        """Update timecode display"""
        minutes, seconds = divmod(int(time_seconds), 60)
        hours, minutes = divmod(minutes, 60)
        timecode = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        if self.timecode_label:
            self.timecode_label.text = timecode

    def on_timeline_change(self, value):
        """Handle timeline slider change"""
        if not self.video_capture or not self.video_capture.isOpened():
            return

        seek_time = float(value)
        frame_pos = int(seek_time * self.fps)

        self._show_frame(frame_pos)
        self.current_time = seek_time
        self._update_timecode(seek_time)

    def refresh_list(self):
        """Refresh video list"""
        self._load_video_list(0)

    def delete_video(self):
        """Delete selected video"""
        if self.current_video_id < 0:
            print("[VideoScreen] No video selected")
            return

        # Stop playback if playing this video
        if self.is_playing:
            self.stop_playback()

        # Delete via presenter
        if self.presenter:
            # Get filename from database
            import sqlite3
            db_path = self.presenter.db_path if hasattr(self.presenter, 'db_path') else "./db/screen_capture.db"

            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT filename FROM videos WHERE id = ?", (self.current_video_id,))
                result = cursor.fetchone()

                if result:
                    filename = result[0]

                    # Delete file
                    if os.path.exists(filename):
                        os.remove(filename)

                    # Delete from database
                    cursor.execute("DELETE FROM videos WHERE id = ?", (self.current_video_id,))
                    conn.commit()
                    conn.close()

                    print(f"[VideoScreen] Deleted video: {filename}")

                    # Refresh list
                    self.refresh_list()

                    # Clear display
                    if self.video_image:
                        self.video_image.texture = None
                    if self.video_info:
                        self.video_info.text = "Select a video to play"

            except Exception as e:
                print(f"[VideoScreen] Failed to delete video: {e}")

    def cleanup(self):
        """Cleanup resources"""
        self.stop_playback()

        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None

    # Presenter callbacks
    def on_video_loaded(self, filename, total_frames, fps):
        """Called when video is loaded"""
        print(f"[VideoScreen] Video loaded callback: {filename}")
        self.fps = fps
        self.total_time = total_frames / fps

    def on_playback_started(self):
        """Called when playback starts"""
        self.is_playing = True
        if self.play_button:
            self.play_button.text = "⏸️"

    def on_playback_stopped(self):
        """Called when playback stops"""
        self.is_playing = False
        if self.play_button:
            self.play_button.text = "▶️"

    def on_playback_frame(self, frame_data):
        """Called for each playback frame"""
        # Frame data is already displayed in _playback_frame
        pass

    def on_video_deleted(self, video_id):
        """Called when video is deleted"""
        print(f"[VideoScreen] Video deleted callback: {video_id}")
        self.refresh_list()


# Register KV language
Builder.load_string('''
<VideoScreen>:
    video_list: video_list
    video_image: video_image
    video_info: video_info
    play_button: play_button
    timeline_slider: timeline_slider
    timecode_label: timecode_label

    FloatLayout:
        # Left panel - video list
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.25
            pos_hint: {'x': 0.0}

            # Header
            Label:
                text: "📹 Recordings"
                font_size: 24
                bold: True
                color: PRIMARY_COLOR
                size_hint_y: None
                height: 50
                halign: 'center'
                text_size: self.size

            # Controls
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: 50
                spacing: 10
                padding: [10, 5, 10, 5]

                Button:
                    text: "🔄 Refresh"
                    font_size: 14
                    bold: True
                    background_color: BUTTON_PRIMARY
                    color: BUTTON_TEXT_COLOR
                    on_release: root.refresh_list()

                Button:
                    text: "🗑️ Delete"
                    font_size: 14
                    bold: True
                    background_color: BUTTON_DANGER
                    color: BUTTON_TEXT_COLOR
                    on_release: root.delete_video()

            # Video list
            BoxLayout:
                orientation: 'vertical'

                ScrollView:
                    bar_width: 10
                    bar_color: PRIMARY_COLOR

                    GridLayout:
                        id: video_list
                        cols: 1
                        size_hint_y: None
                        height: self.minimum_height
                        row_default_height: 50
                        row_force_default: True

                        # Video items will be added dynamically

        # Right panel - video player
        BoxLayout:
            orientation: 'vertical'
            pos_hint: {'x': 0.25}
            size_hint_x: 0.75

            # Video display
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: 0.8
                padding: [10, 10, 10, 10]

                BoxLayout:
                    orientation: 'vertical'
                    background_color: [0, 0, 0, 1]

                    Image:
                        id: video_image
                        allow_stretch: True
                        keep_ratio: True

            # Video info
            Label:
                id: video_info
                text: "Select a video to play"
                font_size: 14
                color: TEXT_LIGHT
                size_hint_y: None
                height: 60
                halign: 'center'
                text_size: self.size
                padding: [10, 10, 10, 10]

            # Controls
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: 80
                spacing: 15
                padding: [20, 10, 20, 10]

                # Play button
                Button:
                    id: play_button
                    text: "▶️"
                    font_size: 24
                    size_hint_x: None
                    width: 80
                    background_color: BUTTON_PRIMARY
                    color: BUTTON_TEXT_COLOR
                    on_release: root.toggle_play()

                # Timeline
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_x: 0.7
                    spacing: 5

                    Slider:
                        id: timeline_slider
                        min: 0
                        max: 100
                        value: 0
                        size_hint_y: 0.6
                        on_value: root.on_timeline_change(self.value)

                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: 30

                        Label:
                            text: "⏱️"
                            font_size: 18
                            size_hint_x: None
                            width: 40

                        Label:
                            id: timecode_label
                            text: "00:00:00"
                            font_size: 18
                            color: TEXT_COLOR
                            halign: 'center'
                            text_size: self.size

                # Volume (placeholder)
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_x: None
                    width: 100
                    spacing: 5

                    Label:
                        text: "🔊"
                        font_size: 18
                        size_hint_x: None
                        width: 40

                    Slider:
                        min: 0
                        max: 100
                        value: 50
                        size_hint_x: None
                        width: 60
''')


__all__ = ["VideoScreen"]
