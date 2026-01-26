### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT               ###

"""
Process Mining Screen for workflow analysis - Kivy Version
"""

import os
from datetime import datetime, timedelta
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.lang import Builder

from .base_screen import BaseScreen
from ..components.colors_kivy import *


class ProcessScreen(BaseScreen):
    """Process Mining and Workflow Analysis screen"""

    # UI Components
    tracking_button = ObjectProperty(None)
    tracking_status = ObjectProperty(None)
    event_counter = ObjectProperty(None)
    live_events_text = ObjectProperty(None)
    results_text = ObjectProperty(None)
    start_time_input = ObjectProperty(None)
    end_time_input = ObjectProperty(None)

    # State
    is_tracking = BooleanProperty(False)
    event_count = NumericProperty(0)
    _live_update_event = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        """Called when screen is displayed"""
        # Check tracking status
        self._update_tracking_status()

    def on_leave(self):
        """Called when leaving screen"""
        # Stop live updates
        self._stop_live_updates()

    def toggle_tracking(self):
        """Toggle input tracking on/off"""
        if self.presenter:
            if self.is_tracking:
                self.presenter.stop_tracking()
            else:
                self.presenter.start_tracking()

        # Update UI
        self.is_tracking = not self.is_tracking
        self._update_tracking_ui()

        if self.is_tracking:
            # Start live updates
            self._start_live_updates()
            if self.live_events_text:
                self.live_events_text.text = "✅ Tracking started!\nCapturing keyboard and mouse events...\n\n"
        else:
            # Stop live updates
            self._stop_live_updates()
            if self.live_events_text:
                self.live_events_text.text += "\n⏹️ Tracking stopped.\n"

    def _update_tracking_status(self):
        """Update tracking status from presenter"""
        if self.presenter:
            status = self.presenter.get_tracking_status()
            self.is_tracking = status.get('is_tracking', False)
            self._update_tracking_ui()

    def _update_tracking_ui(self):
        """Update tracking UI elements"""
        if self.tracking_button:
            if self.is_tracking:
                self.tracking_button.text = "⏹️ Stop Tracking"
                self.tracking_button.background_color = BUTTON_DANGER
            else:
                self.tracking_button.text = "▶️ Start Tracking"
                self.tracking_button.background_color = BUTTON_SUCCESS

        if self.tracking_status:
            if self.is_tracking:
                self.tracking_status.text = "Tracking: ON"
                self.tracking_status.color = SUCCESS_COLOR
            else:
                self.tracking_status.text = "Tracking: OFF"
                self.tracking_status.color = ERROR_COLOR

    def _start_live_updates(self):
        """Start live event feed updates"""
        if self._live_update_event is None:
            self._live_update_event = Clock.schedule_interval(self._update_live_events, 0.5)

    def _stop_live_updates(self):
        """Stop live event feed updates"""
        if self._live_update_event:
            self._live_update_event.cancel()
            self._live_update_event = None

    def _update_live_events(self, dt):
        """Update live event display"""
        if not self.is_tracking or not self.presenter:
            return False

        try:
            # Get recent events
            events = self.presenter.get_recent_events(limit=100)

            # Update counter
            self.event_count = len(events)
            if self.event_counter:
                self.event_counter.text = f"Events: {self.event_count}"

            # Update text display
            if self.live_events_text and events:
                # Format events
                event_lines = ["⚡ Live Event Feed\n", "="*50 + "\n\n"]

                for event in events[-20:]:  # Show last 20 events
                    timestamp = event.get('timestamp', '')
                    event_type = event.get('event_type', '')
                    action = event.get('action', '')
                    key_name = event.get('key_name', '')
                    details = event.get('details', '')

                    # Format timestamp
                    if isinstance(timestamp, str):
                        time_str = timestamp.split('.')[0] if '.' in timestamp else timestamp
                        time_str = time_str.split('T')[-1] if 'T' in timestamp else timestamp[-8:]
                    else:
                        time_str = str(timestamp)

                    # Format event
                    if event_type == 'keyboard':
                        icon = "⌨️"
                        if key_name:
                            msg = f"{icon} {action}: {key_name}"
                            if details:
                                msg += f" ({details})"
                        else:
                            msg = f"{icon} {action}"
                    elif event_type == 'mouse':
                        icon = "🖱️"
                        if action == 'move':
                            msg = f"{icon} Move"
                        elif action == 'click':
                            msg = f"{icon} Click: {key_name if key_name else 'button'}"
                        elif action == 'scroll':
                            msg = f"{icon} Scroll"
                        else:
                            msg = f"{icon} {action}"
                        if details:
                            msg += f" - {details}"
                    else:
                        msg = f"• {event_type}: {action}"

                    event_lines.append(f"[{time_str}] {msg}\n")

                self.live_events_text.text = ''.join(event_lines)

            return True  # Continue updates

        except Exception as e:
            print(f"[ProcessScreen] Live update error: {e}")
            return False

    def set_time_range(self, hours=None, days=None):
        """Set quick time range filter"""
        now = datetime.now()

        if hours:
            start_time = now - timedelta(hours=hours)
        elif days:
            start_time = now - timedelta(days=days)
        else:
            return

        if self.start_time_input:
            self.start_time_input.text = start_time.strftime("%Y-%m-%d %H:%M:%S")
        if self.end_time_input:
            self.end_time_input.text = now.strftime("%Y-%m-%d %H:%M:%S")

    def set_today_range(self):
        """Set time range to today"""
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if self.start_time_input:
            self.start_time_input.text = start_of_day.strftime("%Y-%m-%d %H:%M:%S")
        if self.end_time_input:
            self.end_time_input.text = now.strftime("%Y-%m-%d %H:%M:%S")

    def analyze_workflow(self):
        """Analyze workflow patterns"""
        if not self.presenter:
            return

        # Get time range
        start_time = None
        end_time = None

        if self.start_time_input and self.start_time_input.text:
            try:
                start_time = datetime.strptime(
                    self.start_time_input.text,
                    "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                print("[ProcessScreen] Invalid start time format")

        if self.end_time_input and self.end_time_input.text:
            try:
                end_time = datetime.strptime(
                    self.end_time_input.text,
                    "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                print("[ProcessScreen] Invalid end time format")

        # Run analysis
        report = self.presenter.analyze_workflow(start_time, end_time)

        # Display results
        self._display_results(report)

    def _display_results(self, report):
        """Display analysis results"""
        if not self.results_text:
            return

        lines = []
        lines.append("=" * 70 + "\n")
        lines.append("PROCESS MINING ANALYSIS\n")
        lines.append("=" * 70 + "\n\n")

        # Activity frequency
        if 'activity_frequency' in report:
            lines.append("📊 Activity Frequency\n")
            lines.append("-" * 50 + "\n")
            for activity, count in report['activity_frequency'].items():
                lines.append(f"  {activity}: {count}\n")
            lines.append("\n")

        # Frequent sequences
        if 'frequent_sequences' in report:
            lines.append("🔄 Frequent Sequences\n")
            lines.append("-" * 50 + "\n")
            for sequence in report['frequent_sequences'][:5]:
                lines.append(f"  {sequence}\n")
            lines.append("\n")

        # Time patterns
        if 'time_patterns' in report:
            lines.append("⏱️ Time Patterns\n")
            lines.append("-" * 50 + "\n")
            for pattern, value in report['time_patterns'].items():
                lines.append(f"  {pattern}: {value}\n")
            lines.append("\n")

        # Recommendations
        if 'recommendations' in report:
            lines.append("💡 Recommendations\n")
            lines.append("-" * 50 + "\n")
            for i, rec in enumerate(report['recommendations'], 1):
                lines.append(f"  {i}. {rec}\n")
            lines.append("\n")

        self.results_text.text = ''.join(lines)

    def export_report(self):
        """Export analysis report"""
        if self.presenter:
            # Generate current analysis
            start_time = None
            end_time = None

            if self.start_time_input and self.start_time_input.text:
                try:
                    start_time = datetime.strptime(
                        self.start_time_input.text,
                        "%Y-%m-%d %H:%M:%S"
                    )
                except:
                    pass

            if self.end_time_input and self.end_time_input.text:
                try:
                    end_time = datetime.strptime(
                        self.end_time_input.text,
                        "%Y-%m-%d %H:%M:%S"
                    )
                except:
                    pass

            # Export via presenter
            filename = self.presenter.export_report(start_time, end_time)

            if self.results_text:
                self.results_text.text = f"✅ Report exported to: {filename}\n"

    def cleanup(self):
        """Cleanup resources"""
        self._stop_live_updates()

    # Presenter callbacks
    def on_tracking_started(self):
        """Called when tracking starts"""
        self.is_tracking = True
        self._update_tracking_ui()

    def on_tracking_stopped(self):
        """Called when tracking stops"""
        self.is_tracking = False
        self._update_tracking_ui()

    def on_analysis_started(self):
        """Called when analysis starts"""
        if self.results_text:
            self.results_text.text = "⏳ Analyzing workflow...\n\n"

    def on_analysis_completed(self, report):
        """Called when analysis completes"""
        self._display_results(report)

    def on_report_exported(self, filename):
        """Called when report is exported"""
        print(f"[ProcessScreen] Report exported: {filename}")




# Register KV language
Builder.load_string('''
<ProcessScreen>:
    tracking_button: tracking_button
    tracking_status: tracking_status
    event_counter: event_counter
    live_events_text: live_events_text
    results_text: results_text
    start_time_input: start_time_input
    end_time_input: end_time_input

    ScrollView:
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            padding: [20, 20, 20, 20]
            spacing: 20

            # Header
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: 80
                spacing: 20

                Label:
                    text: "⛏️ Process Mining"
                    font_size: 32
                    bold: True
                    color: PRIMARY_COLOR
                    size_hint_x: 0.4
                    halign: 'left'
                    text_size: self.size

                Label:
                    text: "Track and analyze your workflow patterns"
                    font_size: 16
                    color: TEXT_LIGHT
                    size_hint_x: 0.6
                    halign: 'left'
                    text_size: self.size

            # Tracking controls
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: 60
                spacing: 15
                padding: [10, 10, 10, 10]

                Button:
                    id: tracking_button
                    text: "▶️ Start Tracking"
                    font_size: 16
                    bold: True
                    size_hint_x: None
                    width: 200
                    background_color: BUTTON_SUCCESS
                    color: BUTTON_TEXT_COLOR
                    on_release: root.toggle_tracking()

                Label:
                    id: tracking_status
                    text: "Tracking: OFF"
                    font_size: 14
                    bold: True
                    color: ERROR_COLOR
                    size_hint_x: None
                    width: 150
                    halign: 'center'
                    text_size: self.size

                Label:
                    id: event_counter
                    text: "Events: 0"
                    font_size: 14
                    bold: True
                    color: TEXT_COLOR
                    size_hint_x: None
                    width: 120
                    halign: 'center'
                    text_size: self.size

            # Live events section
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: 300
                spacing: 10

                Label:
                    text: "⚡ Live Event Feed"
                    font_size: 20
                    bold: True
                    color: TEXT_COLOR
                    size_hint_y: None
                    height: 40
                    halign: 'left'
                    text_size: self.size

                ScrollView:
                    size_hint_y: 280
                    bar_width: 10
                    bar_color: PRIMARY_COLOR

                    TextInput:
                        id: live_events_text
                        text: "📝 Live event monitoring ready...\\nClick 'Start Tracking' to begin capturing keyboard and mouse events.\\n\\n"
                        readonly: True
                        font_size: 12
                        foreground_color: TEXT_COLOR
                        background_color: BG_COLOR
                        padding: [15, 15, 15, 15]
                        size_hint_y: None
                        height: self.minimum_height

            # Time filter section
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: 120
                spacing: 10

                Label:
                    text: "⏱️ Time Range Filter (Optional)"
                    font_size: 18
                    bold: True
                    color: TEXT_COLOR
                    size_hint_y: None
                    height: 35
                    halign: 'left'
                    text_size: self.size

                BoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: 45
                    spacing: 10

                    Label:
                        text: "From:"
                        font_size: 14
                        color: TEXT_COLOR
                        size_hint_x: None
                        width: 60
                        halign: 'right'
                        text_size: self.size

                    TextInput:
                        id: start_time_input
                        text: ""
                        hint_text: "YYYY-MM-DD HH:MM:SS"
                        font_size: 14
                        foreground_color: TEXT_COLOR
                        background_color: INPUT_BG_COLOR
                        multiline: False
                        padding: [10, 10, 10, 10]
                        size_hint_x: None
                        width: 200

                    Label:
                        text: "To:"
                        font_size: 14
                        color: TEXT_COLOR
                        size_hint_x: None
                        width: 50
                        halign: 'right'
                        text_size: self.size

                    TextInput:
                        id: end_time_input
                        text: ""
                        hint_text: "YYYY-MM-DD HH:MM:SS"
                        font_size: 14
                        foreground_color: TEXT_COLOR
                        background_color: INPUT_BG_COLOR
                        multiline: False
                        padding: [10, 10, 10, 10]
                        size_hint_x: None
                        width: 200

                    Button:
                        text: "Last Hour"
                        font_size: 12
                        size_hint_x: None
                        width: 110
                        background_color: BUTTON_PRIMARY
                        color: BUTTON_TEXT_COLOR
                        on_release: root.set_time_range(hours=1)

                    Button:
                        text: "Today"
                        font_size: 12
                        size_hint_x: None
                        width: 90
                        background_color: BUTTON_PRIMARY
                        color: BUTTON_TEXT_COLOR
                        on_release: root.set_today_range()

            # Analysis buttons
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: 60
                spacing: 15

                Button:
                    text: "🔍 Analyze Workflow"
                    font_size: 18
                    bold: True
                    background_color: BUTTON_PRIMARY
                    color: BUTTON_TEXT_COLOR
                    on_release: root.analyze_workflow()

                Button:
                    text: "📊 Export Report"
                    font_size: 16
                    bold: True
                    background_color: BUTTON_WARNING
                    color: BUTTON_TEXT_COLOR
                    on_release: root.export_report()

            # Results section
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: 350
                spacing: 10

                Label:
                    text: "📊 Analysis Results"
                    font_size: 20
                    bold: True
                    color: TEXT_COLOR
                    size_hint_y: None
                    height: 40
                    halign: 'left'
                    text_size: self.size

                ScrollView:
                    size_hint_y: 310
                    bar_width: 10
                    bar_color: PRIMARY_COLOR

                    TextInput:
                        id: results_text
                        text: "Click 'Analyze Workflow' to see results..."
                        readonly: True
                        font_size: 12
                        foreground_color: TEXT_COLOR
                        background_color: BG_COLOR
                        padding: [15, 15, 15, 15]
                        size_hint_y: None
                        height: self.minimum_height
''')


__all__ = ["ProcessScreen"]
