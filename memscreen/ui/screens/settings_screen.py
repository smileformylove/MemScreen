### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT               ###

"""
Settings Screen for configuration - Kivy Version
"""

from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty
from kivy.lang import Builder

from .base_screen import BaseScreen
from ..components.colors_kivy import *


class SettingsScreen(BaseScreen):
    """Settings and configuration screen"""

    # UI Components
    ollama_url_input = ObjectProperty(None)
    db_path_input = ObjectProperty(None)
    theme_spinner = ObjectProperty(None)
    stats_text = ObjectProperty(None)

    # State
    ollama_url = StringProperty("http://127.0.0.1:11434")
    db_path = StringProperty("./db/screen_capture.db")
    current_theme = StringProperty("Default")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        """Called when screen is displayed"""
        # Load current settings
        self._load_settings()

    def _load_settings(self):
        """Load current settings"""
        if self.ollama_url_input:
            self.ollama_url_input.text = self.ollama_url

        if self.db_path_input:
            self.db_path_input.text = self.db_path

        if self.theme_spinner:
            self.theme_spinner.text = self.current_theme

        # Load statistics
        self._load_statistics()

    def _load_statistics(self):
        """Load and display usage statistics"""
        if self.presenter:
            stats = self.presenter.get_statistics()

            if self.stats_text:
                lines = []
                lines.append("📊 Usage Statistics\n")
                lines.append("=" * 40 + "\n\n")

                if 'total_videos' in stats:
                    lines.append(f"Videos recorded: {stats['total_videos']}\n")

                if 'total_duration' in stats:
                    duration = stats['total_duration']
                    hours = int(duration // 3600)
                    minutes = int((duration % 3600) // 60)
                    seconds = int(duration % 60)
                    lines.append(f"Total duration: {hours:02d}:{minutes:02d}:{seconds:02d}\n")

                if 'total_events' in stats:
                    lines.append(f"Input events tracked: {stats['total_events']}\n")

                if 'db_size' in stats:
                    size_mb = stats['db_size'] / (1024 * 1024)
                    lines.append(f"Database size: {size_mb:.2f} MB\n")

                lines.append("\n")
                self.stats_text.text = ''.join(lines)

    def on_ollama_url_change(self, instance, value):
        """Handle Ollama URL change"""
        self.ollama_url = value
        print(f"[SettingsScreen] Ollama URL changed to: {value}")

    def on_db_path_change(self, instance, value):
        """Handle database path change"""
        self.db_path = value
        print(f"[SettingsScreen] DB path changed to: {value}")

    def on_theme_change(self, spinner_text):
        """Handle theme selection change"""
        self.current_theme = spinner_text
        print(f"[SettingsScreen] Theme changed to: {spinner_text}")

    def save_settings(self):
        """Save all settings"""
        self.ollama_url = self.ollama_url_input.text if self.ollama_url_input else self.ollama_url
        self.db_path = self.db_path_input.text if self.db_path_input else self.db_path
        self.current_theme = self.theme_spinner.text if self.theme_spinner else self.current_theme

        print("[SettingsScreen] Settings saved:")
        print(f"  Ollama URL: {self.ollama_url}")
        print(f"  DB Path: {self.db_path}")
        print(f"  Theme: {self.current_theme}")

        # Save via presenter
        if self.presenter:
            settings = {
                'ollama_url': self.ollama_url,
                'db_path': self.db_path,
                'theme': self.current_theme
            }
            self.presenter.save_settings(settings)

    def reset_settings(self):
        """Reset settings to defaults"""
        self.ollama_url = "http://127.0.0.1:11434"
        self.db_path = "./db/screen_capture.db"
        self.current_theme = "Default"

        self._load_settings()
        print("[SettingsScreen] Settings reset to defaults")

    def test_connection(self):
        """Test Ollama connection"""
        import requests

        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"[SettingsScreen] ✅ Ollama connection successful")
                # Show success message
                if self.stats_text:
                    current = self.stats_text.text
                    self.stats_text.text = f"✅ Ollama connection successful!\n\n{current}"
            else:
                print(f"[SettingsScreen] ❌ Ollama connection failed: {response.status_code}")
                if self.stats_text:
                    current = self.stats_text.text
                    self.stats_text.text = f"❌ Ollama connection failed: {response.status_code}\n\n{current}"
        except Exception as e:
            print(f"[SettingsScreen] ❌ Connection error: {e}")
            if self.stats_text:
                current = self.stats_text.text
                self.stats_text.text = f"❌ Connection error: {e}\n\n{current}"

    # Presenter callbacks
    def on_settings_loaded(self, settings):
        """Called when settings are loaded"""
        self.ollama_url = settings.get('ollama_url', self.ollama_url)
        self.db_path = settings.get('db_path', self.db_path)
        self.current_theme = settings.get('theme', self.current_theme)
        self._load_settings()

    def on_settings_saved(self):
        """Called when settings are saved"""
        print("[SettingsScreen] Settings saved callback")


# Register KV language
Builder.load_string('''
<SettingsScreen>:
    ollama_url_input: ollama_url_input
    db_path_input: db_path_input
    theme_spinner: theme_spinner
    stats_text: stats_text

    ScrollView:
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            padding: [30, 30, 30, 30]
            spacing: 20

            # Header
            Label:
                text: "⚙️ Settings"
                font_size: 36
                bold: True
                color: PRIMARY_COLOR
                size_hint_y: None
                height: 60
                halign: 'center'
                text_size: self.size

            # AI Models section
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: 180
                padding: [20, 15, 20, 15]
                spacing: 10

                canvas.before:
                    Color:
                        rgba: BG_COLOR
                    Rectangle:
                        pos: self.pos
                        size: self.size

                Label:
                    text: "🤖 AI Models"
                    font_size: 24
                    bold: True
                    color: TEXT_COLOR
                    size_hint_y: None
                    height: 40
                    halign: 'left'
                    text_size: self.size

                Label:
                    text: "Configure Ollama connection"
                    font_size: 14
                    color: TEXT_LIGHT
                    size_hint_y: None
                    height: 30
                    halign: 'left'
                    text_size: self.size

                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: 50
                    spacing: 10

                    Label:
                        text: "Ollama URL:"
                        font_size: 14
                        color: TEXT_COLOR
                        size_hint_x: None
                        width: 120
                        halign: 'right'
                        text_size: self.size

                    TextInput:
                        id: ollama_url_input
                        text: root.ollama_url
                        font_size: 14
                        foreground_color: TEXT_COLOR
                        background_color: INPUT_BG_COLOR
                        multiline: False
                        padding: [10, 10, 10, 10]
                        on_text: root.on_ollama_url_change(self, self.text)

                    Button:
                        text: "Test"
                        font_size: 12
                        size_hint_x: None
                        width: 80
                        background_color: BUTTON_PRIMARY
                        color: BUTTON_TEXT_COLOR
                        on_release: root.test_connection()

                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: 40
                    spacing: 10

                    Label:
                        text: "  • qwen2.5vl:3b - Vision capable"
                        font_size: 12
                        color: TEXT_LIGHT
                        halign: 'left'
                        text_size: self.size

            # Storage section
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: 150
                padding: [20, 15, 20, 15]
                spacing: 10

                canvas.before:
                    Color:
                        rgba: BG_COLOR
                    Rectangle:
                        pos: self.pos
                        size: self.size

                Label:
                    text: "💾 Storage"
                    font_size: 24
                    bold: True
                    color: TEXT_COLOR
                    size_hint_y: None
                    height: 40
                    halign: 'left'
                    text_size: self.size

                Label:
                    text: "Database location"
                    font_size: 14
                    color: TEXT_LIGHT
                    size_hint_y: None
                    height: 30
                    halign: 'left'
                    text_size: self.size

                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: 50
                    spacing: 10

                    Label:
                        text: "DB Path:"
                        font_size: 14
                        color: TEXT_COLOR
                        size_hint_x: None
                        width: 120
                        halign: 'right'
                        text_size: self.size

                    TextInput:
                        id: db_path_input
                        text: root.db_path
                        font_size: 14
                        foreground_color: TEXT_COLOR
                        background_color: INPUT_BG_COLOR
                        multiline: False
                        padding: [10, 10, 10, 10]
                        on_text: root.on_db_path_change(self, self.text)

            # Appearance section
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: 150
                padding: [20, 15, 20, 15]
                spacing: 10

                canvas.before:
                    Color:
                        rgba: BG_COLOR
                    Rectangle:
                        pos: self.pos
                        size: self.size

                Label:
                    text: "🎨 Appearance"
                    font_size: 24
                    bold: True
                    color: TEXT_COLOR
                    size_hint_y: None
                    height: 40
                    halign: 'left'
                    text_size: self.size

                Label:
                    text: "Theme settings"
                    font_size: 14
                    color: TEXT_LIGHT
                    size_hint_y: None
                    height: 30
                    halign: 'left'
                    text_size: self.size

                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: 50
                    spacing: 10

                    Label:
                        text: "Theme:"
                        font_size: 14
                        color: TEXT_COLOR
                        size_hint_x: None
                        width: 120
                        halign: 'right'
                        text_size: self.size

                    Spinner:
                        id: theme_spinner
                        text: 'Default'
                        values: ['Default', 'Dark', 'Light']
                        size_hint_x: None
                        width: 200
                        font_size: 14
                        background_color: SURFACE_COLOR
                        color: TEXT_COLOR
                        on_text: root.on_theme_change(self.text)

            # Statistics section
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: 200
                padding: [20, 15, 20, 15]
                spacing: 10

                canvas.before:
                    Color:
                        rgba: BG_COLOR
                    Rectangle:
                        pos: self.pos
                        size: self.size

                Label:
                    text: "📊 Statistics"
                    font_size: 24
                    bold: True
                    color: TEXT_COLOR
                    size_hint_y: None
                    height: 40
                    halign: 'left'
                    text_size: self.size

                Label:
                    text: "Usage statistics"
                    font_size: 14
                    color: TEXT_LIGHT
                    size_hint_y: None
                    height: 30
                    halign: 'left'
                    text_size: self.size

                ScrollView:
                    size_hint_y: 120
                    bar_width: 10
                    bar_color: PRIMARY_COLOR

                    TextInput:
                        id: stats_text
                        text: "Loading statistics..."
                        readonly: True
                        font_size: 12
                        foreground_color: TEXT_COLOR
                        background_color: BG_COLOR
                        padding: [15, 15, 15, 15]
                        size_hint_y: None
                        height: self.minimum_height

            # Action buttons
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: 60
                spacing: 20
                padding: [0, 20, 0, 20]

                Button:
                    text: "💾 Save Settings"
                    font_size: 16
                    bold: True
                    background_color: BUTTON_SUCCESS
                    color: BUTTON_TEXT_COLOR
                    on_release: root.save_settings()

                Button:
                    text: "🔄 Reset to Defaults"
                    font_size: 16
                    bold: True
                    background_color: BUTTON_WARNING
                    color: BUTTON_TEXT_COLOR
                    on_release: root.reset_settings()
''')


__all__ = ["SettingsScreen"]
