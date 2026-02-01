### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                 ###

import sqlite3
import datetime
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
import json


class ProcessMiningAnalyzer:
    """Process mining analyzer for keyboard and mouse interaction data"""
    
    def __init__(self, db_path: str = "./db/screen_capture.db"):
        """
        Initialize the process mining analyzer
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
    
    def load_event_logs(self, 
                       start_time: Optional[datetime.datetime] = None,
                       end_time: Optional[datetime.datetime] = None,
                       operate_type: Optional[str] = None) -> List[Dict]:
        """
        Load keyboard and mouse events from database as event logs
        
        Args:
            start_time: Start time filter (optional)
            end_time: End time filter (optional)
            operate_type: Filter by 'keyboard' or 'mouse' (optional)
        
        Returns:
            List of event dictionaries with keys: id, timestamp, activity, resource, case_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT id, operate_time, operate_type, action, content, details FROM keyboard_mouse_logs WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND operate_time >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND operate_time <= ?"
            params.append(end_time.isoformat())
        
        if operate_type:
            query += " AND operate_type = ?"
            params.append(operate_type)
        
        query += " ORDER BY operate_time ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            event_id, operate_time, operate_type, action, content, details = row
            # Parse timestamp - handle multiple formats
            if isinstance(operate_time, str):
                try:
                    timestamp = datetime.datetime.fromisoformat(operate_time)
                except:
                    try:
                        timestamp = datetime.datetime.strptime(operate_time, "%Y-%m-%d %H:%M:%S.%f")
                    except:
                        try:
                            timestamp = datetime.datetime.strptime(operate_time, "%Y-%m-%d %H:%M:%S")
                        except:
                            # Fallback: use current time if parsing fails
                            print(f"[WARNING] Failed to parse timestamp: {operate_time}, using current time")
                            timestamp = datetime.datetime.now()
            elif isinstance(operate_time, datetime.datetime):
                timestamp = operate_time
            else:
                # SQLite might return datetime as string in some cases
                print(f"[WARNING] Unexpected timestamp type: {type(operate_time)}, using current time")
                timestamp = datetime.datetime.now()
            
            # Create activity name from type and action
            activity = f"{operate_type}_{action}"
            
            # Extract case_id from session (group events by time windows or sessions)
            # For now, use a simple grouping by hour
            case_id = timestamp.strftime("%Y%m%d_%H")
            
            event = {
                "id": event_id,
                "timestamp": timestamp,
                "activity": activity,
                "resource": operate_type,
                "case_id": case_id,
                "action": action,
                "content": content,
                "details": details,
                "operate_type": operate_type
            }
            events.append(event)
        
        return events
    
    def analyze_activity_frequency(self, events: List[Dict]) -> Dict[str, int]:
        """
        Analyze frequency of each activity
        
        Args:
            events: List of event dictionaries
        
        Returns:
            Dictionary mapping activity names to their frequencies
        """
        activity_counter = Counter(event["activity"] for event in events)
        return dict(activity_counter)
    
    def discover_sequences(self, events: List[Dict], min_support: int = 2) -> List[Tuple[List[str], int]]:
        """
        Discover frequent sequences of activities
        
        Args:
            events: List of event dictionaries
            min_support: Minimum number of occurrences for a sequence to be considered frequent
        
        Returns:
            List of tuples (sequence, frequency) sorted by frequency
        """
        # Group events by case_id
        case_sequences = defaultdict(list)
        for event in events:
            case_id = event["case_id"]
            case_sequences[case_id].append(event)
        
        # Sort events within each case by timestamp
        for case_id in case_sequences:
            case_sequences[case_id].sort(key=lambda x: x["timestamp"])
        
        # Extract sequences (activities in order)
        sequences = []
        for case_id, case_events in case_sequences.items():
            sequence = [event["activity"] for event in case_events]
            sequences.append(sequence)
        
        # Count sequence patterns
        sequence_counter = Counter()
        for seq in sequences:
            # Count all subsequences of length 2 to 5
            for length in range(2, min(6, len(seq) + 1)):
                for i in range(len(seq) - length + 1):
                    subsequence = tuple(seq[i:i+length])
                    sequence_counter[subsequence] += 1
        
        # Filter by min_support and convert to list
        frequent_sequences = [
            (list(seq), count) 
            for seq, count in sequence_counter.items() 
            if count >= min_support
        ]
        
        # Sort by frequency
        frequent_sequences.sort(key=lambda x: x[1], reverse=True)
        
        return frequent_sequences
    
    def analyze_time_patterns(self, events: List[Dict]) -> Dict[str, Dict]:
        """
        Analyze time-based patterns in the event log
        
        Args:
            events: List of event dictionaries
        
        Returns:
            Dictionary with time analysis results
        """
        if not events:
            return {}
        
        # Calculate durations between consecutive events
        durations = []
        for i in range(1, len(events)):
            duration = (events[i]["timestamp"] - events[i-1]["timestamp"]).total_seconds()
            durations.append(duration)
        
        # Group by hour of day
        hourly_activity = defaultdict(int)
        for event in events:
            hour = event["timestamp"].hour
            hourly_activity[hour] += 1
        
        # Group by day of week
        daily_activity = defaultdict(int)
        for event in events:
            day = event["timestamp"].strftime("%A")
            daily_activity[day] += 1
        
        return {
            "total_events": len(events),
            "time_span": {
                "start": events[0]["timestamp"].isoformat(),
                "end": events[-1]["timestamp"].isoformat(),
                "duration_seconds": (events[-1]["timestamp"] - events[0]["timestamp"]).total_seconds()
            },
            "average_duration_between_events": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "hourly_distribution": dict(hourly_activity),
            "daily_distribution": dict(daily_activity)
        }
    
    def discover_workflow_patterns(self, events: List[Dict]) -> Dict[str, any]:
        """
        Discover workflow patterns (directly-follows graph)
        
        Args:
            events: List of event dictionaries
        
        Returns:
            Dictionary with workflow patterns including directly-follows relationships
        """
        # Group events by case_id
        case_sequences = defaultdict(list)
        for event in events:
            case_id = event["case_id"]
            case_sequences[case_id].append(event)
        
        # Sort events within each case by timestamp
        for case_id in case_sequences:
            case_sequences[case_id].sort(key=lambda x: x["timestamp"])
        
        # Build directly-follows graph
        directly_follows = defaultdict(int)
        activity_nodes = set()
        
        for case_id, case_events in case_sequences.items():
            for i in range(len(case_events) - 1):
                from_activity = case_events[i]["activity"]
                to_activity = case_events[i+1]["activity"]
                edge = (from_activity, to_activity)
                directly_follows[edge] += 1
                activity_nodes.add(from_activity)
                activity_nodes.add(to_activity)
        
        # Calculate transition probabilities
        transition_probs = {}
        activity_outgoing = defaultdict(int)
        
        for (from_act, to_act), count in directly_follows.items():
            activity_outgoing[from_act] += count
        
        for (from_act, to_act), count in directly_follows.items():
            prob = count / activity_outgoing[from_act] if activity_outgoing[from_act] > 0 else 0
            transition_probs[(from_act, to_act)] = prob
        
        return {
            "activities": list(activity_nodes),
            "directly_follows": dict(directly_follows),
            "transition_probabilities": {f"{k[0]} -> {k[1]}": v for k, v in transition_probs.items()},
            "total_cases": len(case_sequences)
        }
    
    def identify_common_patterns(self, events: List[Dict]) -> Dict[str, any]:
        """
        Identify common interaction patterns
        
        Args:
            events: List of event dictionaries
        
        Returns:
            Dictionary with identified patterns
        """
        # Pattern 1: Keyboard typing patterns (rapid key presses)
        keyboard_events = [e for e in events if e["operate_type"] == "keyboard"]
        typing_sessions = []
        current_session = []
        
        for i, event in enumerate(keyboard_events):
            if not current_session:
                current_session = [event]
            else:
                time_diff = (event["timestamp"] - current_session[-1]["timestamp"]).total_seconds()
                if time_diff < 2.0:  # Keys pressed within 2 seconds
                    current_session.append(event)
                else:
                    if len(current_session) >= 3:  # At least 3 keys
                        typing_sessions.append(current_session)
                    current_session = [event]
        
        if len(current_session) >= 3:
            typing_sessions.append(current_session)
        
        # Pattern 2: Mouse click patterns
        mouse_events = [e for e in events if e["operate_type"] == "mouse" and e["action"] in ["press", "release"]]
        click_patterns = Counter()
        for i in range(len(mouse_events) - 1):
            if mouse_events[i]["action"] == "press" and mouse_events[i+1]["action"] == "release":
                # Extract button type from content
                content = mouse_events[i].get("content", "")
                if "left" in content.lower():
                    click_patterns["left_click"] += 1
                elif "right" in content.lower():
                    click_patterns["right_click"] += 1
        
        # Pattern 3: Keyboard shortcuts (Ctrl, Alt, Shift combinations)
        shortcut_patterns = []
        for i in range(len(keyboard_events) - 1):
            if i + 1 < len(keyboard_events):
                time_diff = (keyboard_events[i+1]["timestamp"] - keyboard_events[i]["timestamp"]).total_seconds()
                if time_diff < 0.5:  # Keys pressed within 0.5 seconds
                    key1 = keyboard_events[i].get("content", "")
                    key2 = keyboard_events[i+1].get("content", "")
                    if any(mod in key1.lower() for mod in ["ctrl", "alt", "shift"]) or \
                       any(mod in key2.lower() for mod in ["ctrl", "alt", "shift"]):
                        shortcut_patterns.append((key1, key2))
        
        return {
            "typing_sessions": len(typing_sessions),
            "average_typing_session_length": sum(len(s) for s in typing_sessions) / len(typing_sessions) if typing_sessions else 0,
            "click_patterns": dict(click_patterns),
            "shortcut_patterns": len(shortcut_patterns),
            "total_keyboard_events": len(keyboard_events),
            "total_mouse_events": len(mouse_events)
        }
    
    def generate_full_report(self, 
                            start_time: Optional[datetime.datetime] = None,
                            end_time: Optional[datetime.datetime] = None) -> Dict[str, any]:
        """
        Generate a comprehensive process mining report
        
        Args:
            start_time: Start time filter (optional)
            end_time: End time filter (optional)
        
        Returns:
            Dictionary with complete analysis results
        """
        print("[INFO] Loading event logs from database...")
        events = self.load_event_logs(start_time, end_time)
        
        if not events:
            return {"error": "No events found in the specified time range"}
        
        print(f"[INFO] Analyzing {len(events)} events...")
        
        report = {
            "summary": {
                "total_events": len(events),
                "time_range": {
                    "start": events[0]["timestamp"].isoformat() if events else None,
                    "end": events[-1]["timestamp"].isoformat() if events else None
                }
            },
            "activity_frequency": self.analyze_activity_frequency(events),
            "frequent_sequences": self.discover_sequences(events, min_support=2),
            "time_patterns": self.analyze_time_patterns(events),
            "workflow_patterns": self.discover_workflow_patterns(events),
            "common_patterns": self.identify_common_patterns(events)
        }
        
        return report
    
    def export_report_json(self, report: Dict, output_path: str):
        """
        Export report to JSON file
        
        Args:
            report: Analysis report dictionary
            output_path: Path to output JSON file
        """
        # Convert datetime objects to strings for JSON serialization
        def json_serializer(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=json_serializer, ensure_ascii=False)
        
        print(f"[INFO] Report exported to {output_path}")
    
    def print_summary(self, report: Dict):
        """
        Print a human-readable summary of the analysis
        
        Args:
            report: Analysis report dictionary
        """
        if "error" in report:
            print(f"[ERROR] {report['error']}")
            return
        
        print("\n" + "="*60)
        print("PROCESS MINING ANALYSIS REPORT")
        print("="*60)
        
        summary = report.get("summary", {})
        print(f"\nTotal Events: {summary.get('total_events', 0)}")
        print(f"Time Range: {summary.get('time_range', {}).get('start', 'N/A')} to {summary.get('time_range', {}).get('end', 'N/A')}")
        
        print("\n--- Activity Frequency (Top 10) ---")
        activity_freq = report.get("activity_frequency", {})
        sorted_activities = sorted(activity_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        for activity, count in sorted_activities:
            print(f"  {activity}: {count}")
        
        print("\n--- Frequent Sequences (Top 5) ---")
        sequences = report.get("frequent_sequences", [])[:5]
        for seq, count in sequences:
            print(f"  {' -> '.join(seq)}: {count} occurrences")
        
        print("\n--- Time Patterns ---")
        time_patterns = report.get("time_patterns", {})
        if time_patterns:
            print(f"  Average duration between events: {time_patterns.get('average_duration_between_events', 0):.2f} seconds")
            print(f"  Most active hour: {max(time_patterns.get('hourly_distribution', {}).items(), key=lambda x: x[1], default=(0, 0))[0]}")
        
        print("\n--- Common Patterns ---")
        common_patterns = report.get("common_patterns", {})
        if common_patterns:
            print(f"  Typing sessions: {common_patterns.get('typing_sessions', 0)}")
            print(f"  Click patterns: {common_patterns.get('click_patterns', {})}")
            print(f"  Shortcut patterns: {common_patterns.get('shortcut_patterns', 0)}")
        
        print("\n" + "="*60)


def main():
    """Example usage of the ProcessMiningAnalyzer"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process Mining Analysis for Keyboard and Mouse Data")
    parser.add_argument("--db", type=str, default="./db/screen_capture.db",
                       help="Path to database file")
    parser.add_argument("--start", type=str, default=None,
                       help="Start time filter (ISO format: YYYY-MM-DDTHH:MM:SS)")
    parser.add_argument("--end", type=str, default=None,
                       help="End time filter (ISO format: YYYY-MM-DDTHH:MM:SS)")
    parser.add_argument("--output", type=str, default=None,
                       help="Output JSON file path (optional)")
    
    args = parser.parse_args()
    
    # Parse time filters
    start_time = None
    end_time = None
    if args.start:
        start_time = datetime.datetime.fromisoformat(args.start)
    if args.end:
        end_time = datetime.datetime.fromisoformat(args.end)
    
    # Create analyzer and generate report
    analyzer = ProcessMiningAnalyzer(db_path=args.db)
    report = analyzer.generate_full_report(start_time=start_time, end_time=end_time)
    
    # Print summary
    analyzer.print_summary(report)
    
    # Export to JSON if requested
    if args.output:
        analyzer.export_report_json(report, args.output)


if __name__ == "__main__":
    main()
