### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""
MemScreen Kivy UI - Main Application Entry Point

Modern, touch-friendly interface using Kivy framework.
Maintains MVP architecture with Presenters from tkinter version.
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition, SlideTransition
from kivy.core.window import Window
from kivy.config import Config

# Configure Kivy
Config.set('kivy', 'keyboard_mode', 'system')
Config.set('kivy', 'log_level', 'info')
Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '800')
Config.set('graphics', 'resizable', '1')

# Set window title and properties
Window.title = "MemScreen v0.3 - Modern UI"
Window.minimum_width = 1000
Window.minimum_height = 700

# Import screens
from .screens.base_screen import BaseScreen
from .screens.recording_screen import RecordingScreen
from .screens.chat_screen import ChatScreen
from .screens.video_screen import VideoScreen
from .screens.process_screen import ProcessScreen
from .screens.settings_screen import SettingsScreen


class MemScreenApp(App):
    """
    Main Kivy application for MemScreen.

    Uses ScreenManager to manage different screens (like tabs).
    Each screen corresponds to a tab in the tkinter version.
    """

    def build(self):
        """Build the application UI"""
        # Create screen manager with slide transition
        self.screen_manager = ScreenManager(transition=SlideTransition())

        # Add all screens
        self.screen_manager.add_widget(RecordingScreen(name='recording'))
        self.screen_manager.add_widget(ChatScreen(name='chat'))
        self.screen_manager.add_widget(VideoScreen(name='video'))
        self.screen_manager.add_widget(ProcessScreen(name='process'))
        self.screen_manager.add_widget(SettingsScreen(name='settings'))

        # Set default screen
        self.screen_manager.current = 'recording'

        return self.screen_manager

    def on_start(self):
        """Called when application starts"""
        print("[MemScreenApp] Application started")
        print("[MemScreenApp] Screens available: recording, chat, video, process, settings")

    def on_stop(self):
        """Called when application stops"""
        print("[MemScreenApp] Application stopped")


if __name__ == '__main__':
    MemScreenApp().run()
