### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""
Keyboard and Mouse Event Tracker for Process Mining

This module captures user interactions (keyboard presses, mouse movements, clicks)
to enable process mining and workflow analysis.
"""

import sqlite3
import threading
import time
import datetime
import os
import sys
import ctypes
from typing import Optional, Callable
from collections import deque
from pynput import keyboard, mouse


class InputTracker:
    """
    Tracks keyboard and mouse events for process mining analysis

    Features:
    - Captures all keyboard and mouse events
    - Stores in SQLite database for later analysis
    - Minimal performance impact
    - Thread-safe operation
    """

    def __init__(self, db_path: str = "./db/screen_capture.db"):
        """
        Initialize the input tracker

        Args:
            db_path: Path to SQLite database for storing events
        """
        self.db_path = db_path
        self.is_tracking = False
        self.tracking_thread = None
        self.event_queue = None
        self.mouse_listener = None
        self.keyboard_listener = None
        self.track_mouse_move = os.getenv(
            "MEMSCREEN_TRACK_MOUSE_MOVE", ""
        ).strip().lower() in {"1", "true", "yes", "on"}
        self.track_mouse_scroll = os.getenv(
            "MEMSCREEN_TRACK_MOUSE_SCROLL", ""
        ).strip().lower() in {"1", "true", "yes", "on"}

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Create database tables if they don't exist"""
        # Ensure database directory exists
        import os
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"[InputTracker] Created database directory: {db_dir}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create keyboard_mouse_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keyboard_mouse_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operate_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                operate_type TEXT NOT NULL,
                action TEXT NOT NULL,
                content TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_operate_time
            ON keyboard_mouse_logs(operate_time)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_operate_type
            ON keyboard_mouse_logs(operate_type)
        """)

        conn.commit()
        conn.close()

    def _log_event(self, event_type: str, action: str, content: str = "", details: str = ""):
        """
        Log an event to the database

        Args:
            event_type: 'keyboard' or 'mouse'
            action: Specific action (press, release, move, scroll, click)
            content: The key or button name
            details: Additional details (position, modifiers, etc.)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Use local wall-clock time explicitly to avoid SQLite CURRENT_TIMESTAMP (UTC) offset surprises.
            local_time = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

            cursor.execute("""
                INSERT INTO keyboard_mouse_logs (operate_time, operate_type, action, content, details)
                VALUES (?, ?, ?, ?, ?)
            """, (local_time, event_type, action, content, details))

            conn.commit()
            conn.close()
            print(f"[DEBUG] Event logged: {event_type} - {action}")  # Debug log
        except Exception as e:
            print(f"[ERROR] Failed to log event: {e}")
            import traceback
            traceback.print_exc()

    def _on_keyboard_press(self, key):
        """Handle keyboard press event"""
        try:
            if hasattr(key, 'char') and key.char:
                key_name = key.char
            elif hasattr(key, 'name') and key.name:
                key_name = key.name
            else:
                key_name = str(key)
            print(f"[DEBUG] Keyboard press: {key_name}")  # Debug log
            self._log_event("keyboard", "press", key_name, "")
        except Exception as e:
            print(f"[ERROR] Keyboard press error: {e}")
        return True  # Continue listening

    def _on_keyboard_release(self, key):
        """Handle keyboard release event"""
        try:
            if hasattr(key, 'char') and key.char:
                key_name = key.char
            elif hasattr(key, 'name') and key.name:
                key_name = key.name
            else:
                key_name = str(key)
            self._log_event("keyboard", "release", key_name, "Key released")
        except Exception as e:
            print(f"[ERROR] Keyboard release error: {e}")
        return True

    def _on_mouse_move(self, x, y):
        """Handle mouse move event"""
        # Mouse move is noisy and can drift even when users feel "idle".
        # Keep it opt-in to make process counters stable by default.
        if not self.track_mouse_move:
            return True
        try:
            details = f"Position: ({x}, {y})"
            current_time = time.time()
            if not hasattr(self, '_last_mouse_log_time'):
                self._last_mouse_log_time = current_time
                self._log_event("mouse", "move", "", details)
            elif current_time - self._last_mouse_log_time > 1.0:
                self._log_event("mouse", "move", "", details)
                self._last_mouse_log_time = current_time
        except Exception as e:
            print(f"[ERROR] Mouse move error: {e}")
        return True

    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click event"""
        try:
            action = "press" if pressed else "release"
            button_name = button.name
            details = f"Position: ({x}, {y}), Button: {button_name}"
            self._log_event("mouse", action, button_name, details)
        except Exception as e:
            print(f"[ERROR] Mouse click error: {e}")
        return True

    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll event"""
        if not self.track_mouse_scroll:
            return True
        try:
            direction = "up" if dy > 0 else "down"
            details = f"Position: ({x}, {y}), Delta: ({dx}, {dy}), Direction: {direction}"
            self._log_event("mouse", "scroll", "", details)
        except Exception as e:
            print(f"[ERROR] Mouse scroll error: {e}")
        return True

    def _check_macos_permissions(self) -> bool:
        """
        Check if the app has necessary permissions on macOS.

        On macOS, pynput requires Accessibility permissions to monitor keyboard and mouse events.

        Returns:
            True if permissions are granted, raises PermissionError otherwise
        """
        if sys.platform != 'darwin':
            return True  # Only check on macOS

        print("[INFO] Checking macOS Accessibility permissions...")

        try:
            # Use AXIsProcessTrusted to avoid CGEventTap crash risk on some macOS/Python combos.
            app_services = ctypes.CDLL("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
            app_services.AXIsProcessTrusted.restype = ctypes.c_bool
            trusted = bool(app_services.AXIsProcessTrusted())
            if not trusted:
                exe_path = sys.executable
                error_msg = (
                    "Accessibility permission is required for keyboard/mouse recording.\n\n"
                    "Go to: System Settings > Privacy & Security > Accessibility.\n"
                    f"Enable access for the current runtime:\n{exe_path}\n\n"
                    "If launched from terminal, also ensure your terminal app is allowed."
                )
                raise PermissionError(error_msg)

            print("[INFO] ✓ Accessibility permissions verified")
            return True

        except OSError as e:
            print(f"[WARNING] Accessibility check unavailable: {e}")
            print("[INFO] Proceeding without explicit permission precheck")
            return True
        except PermissionError:
            # Re-raise PermissionError with our message
            raise

    def start_tracking(self):
        """Start tracking keyboard and mouse events"""
        if self.is_tracking:
            print("[WARNING] Tracking already active")
            return

        print("[INFO] Starting input tracking...")

        # Permission precheck: fail fast with a clear actionable message.
        self._check_macos_permissions()

        if sys.platform == 'darwin':
            print("[INFO] macOS detected. If tracking fails, grant Accessibility permissions:")
            print("       System Settings > Privacy & Security > Accessibility > Add MemScreen")
            print("       Also grant Input Monitoring to the runtime process for keyboard events.")

        self.is_tracking = True

        # Start mouse listener in a separate thread
        def start_mouse_listener():
            try:
                self.mouse_listener = mouse.Listener(
                    on_move=self._on_mouse_move,
                    on_click=self._on_mouse_click,
                    on_scroll=self._on_mouse_scroll
                )
                self.mouse_listener.start()
                print("[INFO] Mouse listener started")

                # Check if listener is actually running
                time.sleep(0.5)
                if self.mouse_listener.is_alive():
                    print("[INFO] Mouse listener is running")
                else:
                    print("[WARNING] Mouse listener failed to start (not alive)")

            except Exception as e:
                print(f"[ERROR] Failed to start mouse listener: {e}")
                import traceback
                traceback.print_exc()

        mouse_thread = threading.Thread(target=start_mouse_listener, daemon=True)
        mouse_thread.start()

        # Start keyboard listener in a separate thread to avoid blocking main thread
        # This is critical for GUI applications like Kivy to prevent freezing/crashes
        def start_keyboard_listener():
            try:
                self.keyboard_listener = keyboard.Listener(
                    on_press=self._on_keyboard_press,
                    on_release=self._on_keyboard_release
                )
                self.keyboard_listener.start()
                print("[INFO] Keyboard listener started")

                # Check if listener is actually running
                time.sleep(0.5)
                if self.keyboard_listener.is_alive():
                    print("[INFO] Keyboard listener is running")
                else:
                    print("[WARNING] Keyboard listener failed to start (not alive)")

            except Exception as e:
                print(f"[ERROR] Failed to start keyboard listener: {e}")
                import traceback
                traceback.print_exc()

        disable_keyboard = os.getenv("MEMSCREEN_DISABLE_MACOS_KEYBOARD_TRACKING", "").strip().lower() in {
            "1", "true", "yes", "on"
        }
        if sys.platform == 'darwin' and disable_keyboard:
            print("[WARNING] Keyboard tracking disabled by MEMSCREEN_DISABLE_MACOS_KEYBOARD_TRACKING")
        else:
            keyboard_thread = threading.Thread(target=start_keyboard_listener, daemon=True)
            keyboard_thread.start()

        print("[INFO] Input tracking started successfully")

    def stop_tracking(self):
        """Stop tracking keyboard and mouse events"""
        if not self.is_tracking:
            print("[WARNING] Tracking not active")
            return

        print("[INFO] Stopping input tracking...")
        self.is_tracking = False

        if self.mouse_listener:
            self.mouse_listener.stop()
            print("[INFO] Mouse listener stopped")

        if self.keyboard_listener:
            self.keyboard_listener.stop()
            print("[INFO] Keyboard listener stopped")

        print("[INFO] Input tracking stopped")

    def get_latest_event_id(self) -> int:
        """Return current max event id in storage."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(MAX(id), 0) FROM keyboard_mouse_logs")
            row = cursor.fetchone()
            conn.close()
            return int(row[0] or 0)
        except Exception as e:
            print(f"[ERROR] Failed to get latest event id: {e}")
            return 0

    def get_recent_events(self, limit: int = 100, since_id: Optional[int] = None) -> list:
        """
        Get recent events from database

        Args:
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if since_id is not None and since_id >= 0:
                cursor.execute("""
                    SELECT id, operate_time, operate_type, action, content, details
                    FROM keyboard_mouse_logs
                    WHERE id > ?
                    ORDER BY id DESC
                    LIMIT ?
                """, (since_id, limit))
            else:
                cursor.execute("""
                    SELECT id, operate_time, operate_type, action, content, details
                    FROM keyboard_mouse_logs
                    ORDER BY id DESC
                    LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            events = []
            for row in rows:
                event_id, operate_time, operate_type, action, content, details = row
                events.append({
                    "id": event_id,
                    "timestamp": operate_time,
                    "operate_type": operate_type,
                    "action": action,
                    "content": content,
                    "details": details
                })

            return events
        except Exception as e:
            print(f"[ERROR] Failed to get recent events: {e}")
            return []


def main():
    """Example usage"""
    tracker = InputTracker()

    print("Starting input tracking... (Press Ctrl+C to stop)")
    print("Try typing, clicking, and moving the mouse!")

    tracker.start_tracking()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping tracking...")
        tracker.stop_tracking()


if __name__ == "__main__":
    main()
