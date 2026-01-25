### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                ###

"""Process Mining tab for workflow analysis and training recommendations"""

import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime, timedelta
from .base_tab import BaseTab
from ..components.colors import COLORS, FONTS
from ...process_mining import ProcessMiningAnalyzer


class ProcessMiningTab(BaseTab):
    """Process Mining and Workflow Analysis tab"""

    def __init__(self, parent, app, db_name="./db/screen_capture.db"):
        super().__init__(parent, app)
        self.db_name = db_name
        self.analyzer = ProcessMiningAnalyzer(db_name)

        # UI components
        self.time_filter_frame = None
        self.start_time_var = None
        self.end_time_var = None
        self.results_text = None
        self.analyze_btn = None
        self.export_btn = None

        # Real-time event display
        self.live_events_text = None
        self.live_update_job = None
        self.last_event_count = 0

    def create_ui(self):
        """Create process mining tab UI"""
        self.frame = tk.Frame(self.parent, bg=COLORS["bg"])

        # Header section
        header_frame = tk.Frame(self.frame, bg=COLORS["surface"], height=80)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="⛏️ Process Mining",
            font=FONTS["heading"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(side=tk.LEFT, padx=30, pady=20)

        tk.Label(
            header_frame,
            text="Track and analyze your workflow patterns",
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text_light"]
        ).pack(side=tk.LEFT, padx=10)

        # Tracking controls
        controls_frame = tk.Frame(self.frame, bg=COLORS["surface"])
        controls_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        # Tracking toggle
        self.tracking_btn = tk.Button(
            controls_frame,
            text="▶️ Start Tracking",
            font=("Helvetica", 12, "bold"),
            bg="#86EFAC",
            fg="#000000",
            relief=tk.RAISED,
            bd=3,
            cursor="hand2",
            width=15,
            command=self.toggle_tracking
        )
        self.tracking_btn.pack(side=tk.LEFT, padx=10)

        self.tracking_status = tk.Label(
            controls_frame,
            text="Tracking: OFF",
            font=("Helvetica", 10, "bold"),
            bg=COLORS["surface"],
            fg=COLORS["error"]
        )
        self.tracking_status.pack(side=tk.LEFT, padx=10)

        # Event counter
        self.event_counter = tk.Label(
            controls_frame,
            text="Events: 0",
            font=("Helvetica", 10, "bold"),
            bg=COLORS["surface"],
            fg=COLORS["text"]
        )
        self.event_counter.pack(side=tk.LEFT, padx=10)

        # Live event display section
        live_frame = tk.Frame(self.frame, bg=COLORS["surface"])
        live_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        tk.Label(
            live_frame,
            text="⚡ Live Event Feed",
            font=FONTS["subheading"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(anchor=tk.W, padx=0, pady=(10, 5))

        # Create live events display
        self.live_events_text = scrolledtext.ScrolledText(
            live_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            relief=tk.FLAT,
            height=12,
            padx=15,
            pady=15
        )
        self.live_events_text.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for colored output
        self.live_events_text.tag_configure("keyboard", foreground="#3B82F6")  # Blue for keyboard
        self.live_events_text.tag_configure("mouse", foreground="#10B981")  # Green for mouse
        self.live_events_text.tag_configure("timestamp", foreground="#6B7280")  # Gray for timestamps
        self.live_events_text.tag_configure("header", font=("Consolas", 10, "bold"), foreground=COLORS["primary"])

        # Initial message
        self.live_events_text.insert(tk.END, "📝 Live event monitoring ready...\n", "header")
        self.live_events_text.insert(tk.END, "Click 'Start Tracking' to begin capturing keyboard and mouse events.\n\n", "timestamp")

        # Time filter section
        filter_frame = tk.Frame(self.frame, bg=COLORS["surface"])
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        tk.Label(
            filter_frame,
            text="⏱️ Time Range Filter (Optional)",
            font=FONTS["subheading"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(anchor=tk.W, padx=20, pady=(10, 5))

        time_input_frame = tk.Frame(filter_frame, bg=COLORS["surface"])
        time_input_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Start time
        tk.Label(
            time_input_frame,
            text="From:",
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.start_time_var = tk.StringVar()
        start_entry = tk.Entry(
            time_input_frame,
            textvariable=self.start_time_var,
            font=FONTS["body"],
            bg=COLORS["input_bg"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief=tk.SOLID,
            bd=1,
            width=25
        )
        start_entry.pack(side=tk.LEFT, padx=(0, 20))

        # End time
        tk.Label(
            time_input_frame,
            text="To:",
            font=FONTS["body"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.end_time_var = tk.StringVar()
        end_entry = tk.Entry(
            time_input_frame,
            textvariable=self.end_time_var,
            font=FONTS["body"],
            bg=COLORS["input_bg"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief=tk.SOLID,
            bd=1,
            width=25
        )
        end_entry.pack(side=tk.LEFT)

        # Quick time range buttons
        tk.Button(
            time_input_frame,
            text="Last Hour",
            font=("Helvetica", 10),
            bg="#C7D2FE",
            fg="#000000",
            relief=tk.RAISED,
            cursor="hand2",
            command=lambda: self.set_time_range(hours=1)
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            time_input_frame,
            text="Today",
            font=("Helvetica", 10),
            bg="#C7D2FE",
            fg="#000000",
            relief=tk.RAISED,
            cursor="hand2",
            command=self.set_today_range
        ).pack(side=tk.LEFT, padx=5)

        # Analysis button
        analyze_btn_frame = tk.Frame(self.frame, bg=COLORS["surface"])
        analyze_btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        self.analyze_btn = tk.Button(
            analyze_btn_frame,
            text="🔍 Analyze Workflow",
            font=("Helvetica", 14, "bold"),
            bg="#C7D2FE",
            fg="#000000",
            relief=tk.RAISED,
            bd=4,
            cursor="hand2",
            width=20,
            command=self.analyze_workflow
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=10)

        self.export_btn = tk.Button(
            analyze_btn_frame,
            text="📊 Export Report",
            font=("Helvetica", 12, "bold"),
            bg="#FCD34D",
            fg="#000000",
            relief=tk.RAISED,
            bd=3,
            cursor="hand2",
            width=15,
            command=self.export_report
        )
        self.export_btn.pack(side=tk.LEFT, padx=10)

        # Results display
        results_frame = tk.Frame(self.frame, bg=COLORS["surface"])
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        tk.Label(
            results_frame,
            text="📊 Analysis Results",
            font=FONTS["subheading"],
            bg=COLORS["surface"],
            fg=COLORS["text"]
        ).pack(anchor=tk.W, padx=0, pady=(10, 5))

        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=COLORS["bg"],
            fg=COLORS["text"],
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for colored output
        self.results_text.tag_configure("title", font=("Consolas", 12, "bold"), foreground=COLORS["primary"])
        self.results_text.tag_configure("header", font=("Consolas", 10, "bold"), foreground=COLORS["secondary"])
        self.results_text.tag_configure("success", foreground=COLORS["success"])
        self.results_text.tag_configure("info", foreground=COLORS["info"])
        self.results_text.tag_configure("warning", foreground=COLORS["warning"])

    def toggle_tracking(self):
        """Toggle input tracking on/off"""
        if not hasattr(self.app, 'input_tracker'):
            # Import here to avoid import errors if pynput is not available
            try:
                from ...input_tracker import InputTracker
                self.app.input_tracker = InputTracker(self.db_name)
            except ImportError as e:
                messagebox.showerror("Error", f"Input tracking requires 'pynput' library.\n\nInstall with: pip install pynput\n\nError: {e}")
                return

        if not self.app.input_tracker.is_tracking:
            self.app.input_tracker.start_tracking()
            self.tracking_btn.config(text="⏹️ Stop Tracking", bg="#FCA5A5", fg="#000000")
            self.tracking_status.config(text="Tracking: ON", fg=COLORS["success"])

            # Clear and update live display
            self.live_events_text.delete(1.0, tk.END)
            self.live_events_text.insert(tk.END, "✅ Tracking started!\n", "header")
            self.live_events_text.insert(tk.END, "Capturing keyboard and mouse events...\n\n", "timestamp")

            # Start live update
            self.last_event_count = 0
            self.update_live_events()
        else:
            self.app.input_tracker.stop_tracking()
            self.tracking_btn.config(text="▶️ Start Tracking", bg="#86EFAC", fg="#000000")
            self.tracking_status.config(text="Tracking: OFF", fg=COLORS["error"])

            # Stop live update
            if self.live_update_job:
                self.frame.after_cancel(self.live_update_job)
                self.live_update_job = None

            self.live_events_text.insert(tk.END, "\n⏹️ Tracking stopped.\n", "header")

    def update_live_events(self):
        """Update live event display with recent events"""
        if not self.app.input_tracker.is_tracking:
            return

        try:
            # Get recent events
            events = self.app.input_tracker.get_recent_events(limit=100)

            # Update counter (use recent events count as approximation)
            self.event_counter.config(text=f"Events: {len(events)}")

            # Display new events
            if len(events) > self.last_event_count:
                # Get only new events (reverse to show newest first)
                new_events = events[self.last_event_count:][::-1]

                for event in new_events:
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

                    # Format event message
                    if event_type == 'keyboard':
                        icon = "⌨️"
                        tag = "keyboard"
                        if key_name:
                            msg = f"{icon} {action}: {key_name}"
                            if details:
                                msg += f" ({details})"
                        else:
                            msg = f"{icon} {action}"
                    elif event_type == 'mouse':
                        icon = "🖱️"
                        tag = "mouse"
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
                        icon = "•"
                        tag = ""
                        msg = f"{icon} {event_type}: {action}"

                    # Insert into text widget
                    self.live_events_text.insert(tk.END, f"[{time_str}] ", "timestamp")
                    self.live_events_text.insert(tk.END, f"{msg}\n", tag)

                self.last_event_count = len(events)

                # Auto-scroll to bottom
                self.live_events_text.see(tk.END)

                # Limit text widget size (keep last 500 lines)
                lines = int(self.live_events_text.index('end-1c').split('.')[0])
                if lines > 500:
                    self.live_events_text.delete(1.0, f"{lines-500}.0")

        except Exception as e:
            # Silently handle errors to avoid disrupting tracking
            pass

        # Schedule next update (every 500ms)
        if self.app.input_tracker.is_tracking:
            self.live_update_job = self.frame.after(500, self.update_live_events)

    def set_time_range(self, hours=None, days=None):
        """Set quick time range filter"""
        now = datetime.now()

        if hours:
            start_time = now - timedelta(hours=hours)
        elif days:
            start_time = now - timedelta(days=days)
        else:
            return

        self.start_time_var.set(start_time.strftime("%Y-%m-%d %H:%M:%S"))
        self.end_time_var.set(now.strftime("%Y-%m-%d %H:%M:%S"))

    def set_today_range(self):
        """Set time range to today"""
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        self.start_time_var.set(start_of_day.strftime("%Y-%m-%d %H:%M:%S"))
        self.end_time_var.set(now.strftime("%Y-%m-%d %H:%M:%S"))

    def analyze_workflow(self):
        """Analyze workflow patterns and display results"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete("1.0", tk.END)

        self._append_result("title", "="*70)
        self._append_result("title", "PROCESS MINING ANALYSIS")
        self._append_result("title", "="*70)
        self._append_result("", "")

        try:
            # Parse time filters
            start_time = None
            end_time = None

            if self.start_time_var.get():
                try:
                    start_time = datetime.strptime(self.start_time_var.get(), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    self._append_result("warning", "⚠️ Invalid start time format. Using all available data.\n")

            if self.end_time_var.get():
                try:
                    end_time = datetime.strptime(self.end_time_var.get(), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    self._append_result("warning", "⚠️ Invalid end time format. Using all available data.\n")

            # Generate report
            self._append_result("info", "📊 Loading and analyzing events...")
            self.frame.update()

            report = self.analyzer.generate_full_report(start_time=start_time, end_time=end_time)

            if "error" in report:
                self._append_result("error", f"❌ {report['error']}\n")
                self._append_result("info", "💡 Try recording some activities first!\n")
                return

            # Display summary
            self._display_report(report)

            # Enable export button
            self.export_btn.config(state=tk.NORMAL)

        except Exception as e:
            self._append_result("error", f"❌ Analysis failed: {e}\n")
            import traceback
            traceback.print_exc()

        self.results_text.config(state=tk.DISABLED)

    def _display_report(self, report: dict):
        """Display the analysis report"""
        # Summary
        summary = report.get("summary", {})
        self._append_result("header", "📈 SUMMARY")
        self._append_result("", "")
        self._append_result("info", f"  Total Events: {summary.get('total_events', 0):,}")

        time_range = summary.get("time_range", {})
        if time_range.get("start") and time_range.get("end"):
            self._append_result("info", f"  Time Range: {time_range['start'][:19]} to {time_range['end'][:19]}")
            duration = time_range.get("duration_seconds", 0) / 60
            self._append_result("info", f"  Duration: {duration:.1f} minutes")
        self._append_result("", "")

        # Activity Frequency
        self._append_result("header", "🔢 TOP ACTIVITIES")
        self._append_result("", "")
        activity_freq = report.get("activity_frequency", {})
        sorted_activities = sorted(activity_freq.items(), key=lambda x: x[1], reverse=True)[:15]

        for activity, count in sorted_activities:
            bar = "█" * min(50, count // 2)
            self._append_result("info", f"  {activity:<40} {count:>5} {bar}")

        self._append_result("", "")

        # Frequent Sequences
        self._append_result("header", "🔄 FREQUENT WORKFLOW PATTERNS")
        self._append_result("", "")
        sequences = report.get("frequent_sequences", [])[:10]

        for seq, count in sequences:
            pattern = " → ".join(seq)
            self._append_result("info", f"  {pattern}")
            self._append_result("success", f"    ({count} occurrences)\n")

        # Time Patterns
        time_patterns = report.get("time_patterns", {})
        if time_patterns:
            self._append_result("header", "⏰ TIME PATTERNS")
            self._append_result("", "")
            self._append_result("info", f"  Average time between actions: {time_patterns.get('average_duration_between_events', 0):.2f} seconds")

            # Most active hour
            hourly = time_patterns.get("hourly_distribution", {})
            if hourly:
                peak_hour = max(hourly.items(), key=lambda x: x[1])[0]
                self._append_result("info", f"  Most active hour: {peak_hour}:00")

            self._append_result("", "")

        # Common Patterns
        common = report.get("common_patterns", {})
        if common:
            self._append_result("header", "🎯 INTERACTION PATTERNS")
            self._append_result("", "")
            self._append_result("info", f"  Typing sessions: {common.get('typing_sessions', 0)}")
            self._append_result("info", f"  Average typing length: {common.get('average_typing_session_length', 0):.1f} keys")

            clicks = common.get("click_patterns", {})
            if clicks:
                self._append_result("info", "  Click patterns:")
                for click_type, count in clicks.items():
                    self._append_result("info", f"    {click_type}: {count}")

            shortcuts = common.get("shortcut_patterns", 0)
            self._append_result("info", f"  Keyboard shortcuts used: {shortcuts}")
            self._append_result("", "")

        # Training Recommendations
        self._append_result("title", "="*70)
        self._append_result("title", "💡 TRAINING RECOMMENDATIONS")
        self._append_result("title", "="*70)
        self._append_result("", "")

        # Analyze and provide recommendations
        recommendations = self._generate_recommendations(report)
        for rec in recommendations:
            self._append_result("header", f"• {rec['title']}")
            self._append_result("info", f"  {rec['description']}\n")

    def _generate_recommendations(self, report: dict) -> list:
        """Generate training recommendations based on analysis"""
        recommendations = []

        activity_freq = report.get("activity_frequency", {})
        common_patterns = report.get("common_patterns", {})

        # Recommendation 1: High mouse movement
        mouse_moves = sum(count for act, count in activity_freq.items() if "mouse_move" in act)
        if mouse_moves > 100:
            recommendations.append({
                "title": "Mouse Efficiency",
                "description": "High mouse movement detected. Consider learning keyboard shortcuts to reduce mouse dependency and improve speed."
            })

        # Recommendation 2: Repetitive patterns
        sequences = report.get("frequent_sequences", [])
        if sequences:
            top_seq, count = sequences[0]
            if count >= 5:
                pattern = " → ".join(top_seq)
                recommendations.append({
                    "title": "Automation Opportunity",
                    "description": f"Detected repetitive pattern: '{pattern}' (used {count} times). Consider creating a macro or automation script."
                })

        # Recommendation 3: Typing speed
        typing_sessions = common_patterns.get("typing_sessions", 0)
        avg_length = common_patterns.get("average_typing_session_length", 0)
        if typing_sessions > 10:
            recommendations.append({
                "title": "Typing Practice",
                "description": f"You have {typing_sessions} typing sessions with average {avg_length:.1f} keys per session. Consider touch typing training to improve efficiency."
            })

        # Recommendation 4: Time-based patterns
        time_patterns = report.get("time_patterns", {})
        hourly = time_patterns.get("hourly_distribution", {})
        if hourly:
            peak_hour = max(hourly.items(), key=lambda x: x[1])[0]
            recommendations.append({
                "title": "Peak Productivity Time",
                "description": f"Your most active hour is {peak_hour}:00. Schedule important tasks during this time for maximum efficiency."
            })

        if not recommendations:
            recommendations.append({
                "title": "Track More Data",
                "description": "Not enough data for personalized recommendations. Continue tracking your activities to get insights."
            })

        return recommendations

    def _append_result(self, tag, text):
        """Append text to results with formatting"""
        self.results_text.insert(tk.END, text + "\n", tag)

    def export_report(self):
        """Export analysis report to JSON file"""
        try:
            # Parse time filters
            start_time = None
            end_time = None

            if self.start_time_var.get():
                try:
                    start_time = datetime.strptime(self.start_time_var.get(), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass

            if self.end_time_var.get():
                try:
                    end_time = datetime.strptime(self.end_time_var.get(), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass

            # Generate report
            report = self.analyzer.generate_full_report(start_time=start_time, end_time=end_time)

            # Save to file
            default_name = f"process_mining_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=default_name,
                title="Export Process Mining Report"
            )

            if file_path:
                self.analyzer.export_report_json(report, file_path)
                messagebox.showinfo("Export Success", f"Report exported to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report:\n{e}")


__all__ = ["ProcessMiningTab"]
