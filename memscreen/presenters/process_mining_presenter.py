### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""Presenter for Process Mining functionality (MVP Pattern)"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from .base_presenter import BasePresenter


class ProcessMiningPresenter(BasePresenter):
    """
    Presenter for Process Mining functionality.

    Responsibilities:
    - Manage input tracking state
    - Start/stop event tracking
    - Analyze workflow patterns
    - Generate training recommendations
    - Export reports

    View (ProcessMiningTab) responsibilities:
    - Display tracking controls
    - Show live event feed
    - Display analysis results
    - Show recommendations
    """

    def __init__(self, view=None, input_tracker=None, analyzer=None, db_path: str = "./db/input_events.db"):
        """
        Initialize process mining presenter.

        Args:
            view: ProcessMiningTab view instance
            input_tracker: InputTracker instance for capturing events
            analyzer: ProcessMiningAnalyzer instance
            db_path: Path to event database
        """
        super().__init__(view)
        self.input_tracker = input_tracker
        self.analyzer = analyzer
        self.db_path = db_path

        # Tracking state
        self.is_tracking = False
        self.event_count = 0
        self.last_event_count = 0

        # Live event update
        self.update_interval = 500  # ms
        self.update_job = None

        self._is_initialized = False

    def initialize(self):
        """Initialize presenter"""
        try:
            # Import using absolute imports to work in both dev and packaged environments
            from memscreen.input_tracker import InputTracker
            from memscreen.process_mining import ProcessMiningAnalyzer

            if not self.input_tracker:
                self.input_tracker = InputTracker(db_path=self.db_path)

            if not self.analyzer:
                self.analyzer = ProcessMiningAnalyzer(self.db_path)

            self._is_initialized = True
            print("[ProcessMiningPresenter] Initialized successfully")

        except Exception as e:
            self.handle_error(e, "Failed to initialize ProcessMiningPresenter")
            raise

    def cleanup(self):
        """Clean up resources"""
        # Stop tracking if active
        if self.is_tracking:
            self.stop_tracking()

        self._is_initialized = False

    # ==================== Public API for View ====================

    def get_tracking_status(self) -> Dict[str, Any]:
        """
        Get current tracking status.

        Returns:
            Dictionary with tracking status
        """
        return {
            "is_tracking": self.is_tracking,
            "event_count": self.event_count,
            "db_path": self.db_path
        }

    def start_tracking(self) -> bool:
        """
        Start input event tracking.

        Returns:
            True if tracking started successfully
        """
        if self.is_tracking:
            self.show_error("Tracking is already active")
            return False

        try:
            if not self.input_tracker:
                self.initialize()

            self.input_tracker.start_tracking()
            self.is_tracking = True
            self.event_count = 0
            self.last_event_count = 0

            # Notify view
            if self.view:
                self.view.on_tracking_started()

            return True

        except Exception as e:
            self.handle_error(e, "Failed to start tracking")
            return False

    def stop_tracking(self) -> bool:
        """
        Stop input event tracking.

        Returns:
            True if tracking stopped successfully
        """
        if not self.is_tracking:
            return False

        try:
            if self.input_tracker:
                self.input_tracker.stop_tracking()

            self.is_tracking = False

            # Notify view
            if self.view:
                self.view.on_tracking_stopped(self.event_count)

            return True

        except Exception as e:
            self.handle_error(e, "Failed to stop tracking")
            return False

    def get_recent_events(self, limit: int = 100) -> list:
        """
        Get recent input events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        if not self.input_tracker:
            return []

        try:
            events = self.input_tracker.get_recent_events(limit=limit)
            self.event_count = len(events)
            return events

        except Exception as e:
            self.handle_error(e, "Failed to get recent events")
            return []

    def analyze_workflow(self, start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze workflow patterns.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Analysis report dictionary
        """
        if not self.analyzer:
            self.show_error("Analyzer not initialized")
            return None

        try:
            # Notify view that analysis is starting
            if self.view:
                self.view.on_analysis_started()

            # Generate report
            report = self.analyzer.generate_full_report(
                start_time=start_time,
                end_time=end_time
            )

            # Notify view with results
            if self.view:
                self.view.on_analysis_completed(report)

            return report

        except Exception as e:
            self.handle_error(e, "Failed to analyze workflow")
            return None

    def export_report(self, report: Dict[str, Any], filepath: str) -> bool:
        """
        Export analysis report to file.

        Args:
            report: Analysis report dictionary
            filepath: Path to save report

        Returns:
            True if export successful
        """
        try:
            if not self.analyzer:
                self.show_error("Analyzer not initialized")
                return False

            self.analyzer.export_report_json(report, filepath)

            # Notify view
            if self.view:
                self.view.on_report_exported(filepath)

            return True

        except Exception as e:
            self.handle_error(e, f"Failed to export report to {filepath}")
            return False

    def generate_recommendations(self, report: Dict[str, Any]) -> list:
        """
        Generate training recommendations based on analysis.

        Args:
            report: Analysis report dictionary

        Returns:
            List of recommendation strings
        """
        try:
            recommendations = []

            # Analyze activity frequency
            activity_freq = report.get("activity_frequency", {})
            if activity_freq:
                top_activity = max(activity_freq.items(), key=lambda x: x[1])
                recommendations.append(
                    f"Most frequent action: '{top_activity[0]}' ({top_activity[1]} times)"
                )

            # Analyze sequences
            sequences = report.get("frequent_sequences", [])
            if sequences:
                top_seq = sequences[0]
                seq_str = " → ".join(top_seq["sequence"])
                recommendations.append(
                    f"Common pattern: '{seq_str}' ({top_seq['count']} times)"
                )

            # Time patterns
            time_patterns = report.get("time_patterns", {})
            typing_sessions = time_patterns.get("typing_sessions", 0)
            if typing_sessions > 5:
                recommendations.append(
                    f"Consider using text expansion tools ({typing_sessions} typing sessions detected)"
                )

            # General recommendations
            recommendations.extend([
                "Learn keyboard shortcuts for frequently used actions",
                "Automate repetitive tasks when possible",
                "Organize workspace for efficiency"
            ])

            return recommendations

        except Exception as e:
            self.handle_error(e, "Failed to generate recommendations")
            return []

    def get_quick_time_ranges(self) -> Dict[str, tuple]:
        """
        Get quick time range options.

        Returns:
            Dictionary with range name -> (start, end) tuples
        """
        now = datetime.now()

        return {
            "last_hour": (now - timedelta(hours=1), now),
            "today": (now.replace(hour=0, minute=0, second=0), now),
            "this_week": (now - timedelta(days=7), now),
            "all_time": (None, now)
        }

    # ==================== Private Methods ====================

    def _update_event_count(self):
        """Update event count from tracker"""
        if self.input_tracker and self.is_tracking:
            try:
                events = self.input_tracker.get_recent_events(limit=1000)
                self.event_count = len(events)

                # Notify view if count changed
                if self.view and self.event_count != self.last_event_count:
                    self.view.on_event_count_updated(self.event_count)
                    self.last_event_count = self.event_count

            except Exception as e:
                print(f"[ProcessMiningPresenter] Failed to update event count: {e}")
