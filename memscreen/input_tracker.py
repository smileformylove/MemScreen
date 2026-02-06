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

            cursor.execute("""
                INSERT INTO keyboard_mouse_logs (operate_type, action, content, details)
                VALUES (?, ?, ?, ?)
            """, (event_type, action, content, details))

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
            key_name = key.name if hasattr(key, 'name') else str(key)
            print(f"[DEBUG] Keyboard press: {key_name}")  # Debug log
            modifiers = []
            if keyboard.Shift in keyboard._modifiers_pressed:
                modifiers.append("Shift")
            if keyboard.Control in keyboard._modifiers_pressed:
                modifiers.append("Ctrl")
            if keyboard.Alt in keyboard._modifiers_pressed:
                modifiers.append("Alt")

            details = f"Modifiers: {', '.join(modifiers) if modifiers else 'None'}"
            self._log_event("keyboard", "press", key_name, details)
        except Exception as e:
            print(f"[ERROR] Keyboard press error: {e}")
        return True  # Continue listening

    def _on_keyboard_release(self, key):
        """Handle keyboard release event"""
        try:
            key_name = key.name if hasattr(key, 'name') else str(key)
            self._log_event("keyboard", "release", key_name, "Key released")
        except Exception as e:
            print(f"[ERROR] Keyboard release error: {e}")
        return True

    def _on_mouse_move(self, x, y):
        """Handle mouse move event"""
        # Throttle mouse move events to avoid flooding the database
        # Only log every 10th move or if significant time has passed
        try:
            details = f"Position: ({x}, {y})"
            # Only log periodically to avoid too many events
            current_time = time.time()
            if not hasattr(self, '_last_mouse_log_time'):
                self._last_mouse_log_time = current_time
                self._log_event("mouse", "move", "", details)
            elif current_time - self._last_mouse_log_time > 1.0:  # Log at most once per second
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
        import sys
        if sys.platform != 'darwin':
            return True  # Only check on macOS

        print("[INFO] Checking macOS Accessibility permissions...")

        try:
            # Try to create a CGEventTap to test permissions
            from Quartz.CoreGraphics import (
                CGEventTapCreate,
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                kCGEventTapOptionDefault,
            )
            from Quartz import kCGEventMaskForAllEvents

            tap = CGEventTapCreate(
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                kCGEventTapOptionDefault,
                kCGEventMaskForAllEvents(),
                None,
                None
            )

            if tap is None:
                # No permission - raise error with helpful message
                error_msg = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
缺少辅助功能权限
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MemScreen 需要辅助功能权限才能记录键盘和鼠标事件。

请按以下步骤授予权限：

1. 打开"系统设置"
2. 点击"隐私与安全性"
3. 选择"辅助功能"
4. 点击"+"按钮
5. 从"应用程序"文件夹中选择 MemScreen.app
6. 确保 MemScreen.app 旁边的开关已打开 ✓

完成后，重新启动 MemScreen 应用。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                raise PermissionError(error_msg)

            # Clean up the tap
            import ctypes
            CFRelease = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation').CFRelease
            CFRelease(tap)

            print("[INFO] ✓ Accessibility permissions verified")
            return True

        except ImportError:
            # Quartz not available - just show warning
            print("[WARNING] Cannot verify permissions (Quartz not available)")
            print("[INFO] If tracking crashes, grant Accessibility permissions in System Settings")
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

        # NOTE: Permission checking removed because CGEventTapCreate can cause crashes
        # Instead, we rely on exception handling when starting listeners
        import sys
        if sys.platform == 'darwin':
            print("[INFO] macOS detected. If tracking fails, grant Accessibility permissions:")
            print("       System Settings > Privacy & Security > Accessibility > Add MemScreen")

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

        # TEMPORARY DISABLE KEYBOARD LISTENER ON MACOS
        # Due to pynput compatibility issues with macOS 15.5 + Python 3.13
        # The keyboard listener causes crashes in TSMGetInputSourceProperty
        import sys
        if sys.platform == 'darwin':
            print("[WARNING] Keyboard tracking disabled on macOS due to compatibility issues")
            print("[INFO] Mouse tracking is enabled")
            print("[INFO] Full input tracking will be enabled in a future update")
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

    def get_recent_events(self, limit: int = 100) -> list:
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

            cursor.execute("""
                SELECT id, operate_time, operate_type, action, content, details
                FROM keyboard_mouse_logs
                ORDER BY operate_time DESC
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
