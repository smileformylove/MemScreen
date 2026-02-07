#!/usr/bin/env python3
"""
Test script for Native macOS Floating Ball - Updated
"""

import os
import sys
import time

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Check if running on macOS
if sys.platform != 'darwin':
    print("ERROR: Native floating ball is only supported on macOS")
    sys.exit(1)

from memscreen.ui.floating_ball_native import create_floating_ball


class MockPresenter:
    """Mock presenter for testing"""
    def get_recording_status(self):
        return {
            'frame_count': 42,
            'elapsed_time': 12.5
        }

    def stop_recording(self):
        print("[FloatingBall] Stop recording called")

    def toggle_pause(self):
        print("[FloatingBall] Toggle pause called")


def main():
    print("Starting Native macOS Floating Ball test...")
    print("=" * 60)

    # Create presenter
    presenter = MockPresenter()

    # Create floating ball
    ball = create_floating_ball(presenter=presenter)

    # Set callbacks
    def on_stop():
        print("[Callback] Stop recording -> Closing floating ball")
        ball.close()
        sys.exit(0)

    def on_pause():
        print("[Callback] Toggle pause")
        ball.contentView().setPaused_(not ball.contentView().is_paused)

    def on_show_main_window():
        print("[Callback] Show main window (floating ball stays active)")
        # In real app, this would show the Kivy window
        print("[Test] Main window would be shown now")

    def on_close_ball():
        print("[Callback] Close floating ball and restore main window")
        ball.close()
        sys.exit(0)

    ball.on_stop_callback = on_stop
    ball.on_pause_callback = on_pause
    ball.on_show_main_window_callback = on_show_main_window
    ball.on_main_window_callback = on_close_ball

    # Set recording state
    ball.setRecordingState_(True)

    print("=" * 60)
    print("Floating ball is now visible!")
    print("Try the following interactions:")
    print("  1. LEFT-CLICK: Show main window (ball stays active)")
    print("  2. DRAG: Move the ball around")
    print("  3. RIGHT-CLICK: See context menu")
    print("     - Stop Recording: Closes ball and exits")
    print("     - Main Window: Shows main window (ball stays)")
    print("  4. SWITCH APPS: Ball should stay visible")
    print("  5. Press Ctrl+C to exit")
    print("=" * 60)

    # Keep the script running
    try:
        from Cocoa import NSApplication
        app = NSApplication.sharedApplication()
        app.run()
    except KeyboardInterrupt:
        print("\n[FloatingBall] Test stopped by user")
        ball.close()


if __name__ == '__main__':
    main()
