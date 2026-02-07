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
        print("[Callback] Stop recording")
        # Just stop recording, don't close the ball
        ball.setRecordingState_(False)
        print("[Test] Recording stopped, ball remains active")

    def on_pause():
        print("[Callback] Toggle pause")
        ball.contentView().setPaused_(not ball.contentView().is_paused)

    def on_show_main_window():
        print("[Callback] Show main window (floating ball stays active)")
        # Write switch file to communicate with main UI
        switch_file = os.path.expanduser('~/.memscreen/switch_screen.txt')
        with open(switch_file, 'w') as f:
            f.write('recording')
        print(f"[Test] Wrote 'recording' to {switch_file}")
        print("[Test] Main UI should activate now")

    def on_close_ball():
        print("[Callback] Quit: Closing floating ball and main application")
        ball.close()

        # Also quit the main application
        import subprocess
        try:
            # Kill memscreen-ui process
            subprocess.run(['pkill', '-f', 'memscreen-ui'],
                         capture_output=True, timeout=5)
            print("[Test] Sent quit signal to main application")
        except Exception as e:
            print(f"[Test] Error quitting main app: {e}")

        sys.exit(0)

    def on_start_recording():
        """Start recording from floating ball"""
        print("[Callback] Start recording requested")
        # Notify main UI to start recording
        switch_file = os.path.expanduser('~/.memscreen/recording_trigger.txt')
        with open(switch_file, 'w') as f:
            f.write('start')
        print(f"[Test] Wrote start recording trigger to {switch_file}")
        print("[Test] Main UI should start recording")

        # Update floating ball state to recording
        ball.setRecordingState_(True)
        print("[Test] Floating ball now shows recording state")
    def on_select_region():
        """Select region from floating ball using native macOS selector"""
        print("[Callback] Select region requested - minimizing windows and using native selector")

        # Minimize all Python windows first
        import subprocess
        try:
            # Minimize all Python windows (including main UI)
            subprocess.run(['osascript', '-e', 'tell application "System Events" to tell every process whose name contains "Python" to set minimized to true'],
                         capture_output=True, timeout=3)
            print("[Test] Minimized all Python windows")
        except Exception as e:
            print(f"[Test] Warning: Could not minimize windows: {e}")

        # Use native region selector directly
        try:
            from memscreen.ui.native_region_selector import select_region
            from Cocoa import NSApplication

            def region_callback(bbox):
                """Handle region selection"""
                if bbox:
                    print(f"[Test] Region selected: {bbox}")
                    # Update presenter with new region
                    if presenter:
                        try:
                            presenter.set_recording_mode('region', bbox=bbox)
                            print(f"[Test] Presenter updated with region mode")
                        except Exception as e:
                            print(f"[Test] Error updating presenter: {e}")
                else:
                    print("[Test] Region selection cancelled")
                    # Reset to fullscreen mode
                    if presenter:
                        try:
                            presenter.set_recording_mode('fullscreen')
                            print("[Test] Reset to fullscreen mode")
                        except Exception as e:
                            print(f"[Test] Error resetting mode: {e}")

            # Show native region selector
            print("[Test] Opening native macOS region selector...")
            selector = select_region(region_callback)
            print("[Test] Native selector is now active")

        except Exception as e:
            print(f"[Test] Error opening native selector: {e}")
            import traceback
            traceback.print_exc()

    ball.on_stop_callback = on_stop
    ball.on_pause_callback = on_pause
    ball.on_show_main_window_callback = on_show_main_window
    ball.on_main_window_callback = on_close_ball
    ball.on_quit_callback = on_close_ball  # Use same callback for quit
    ball.on_select_region_callback = on_select_region  # Region selection callback
    ball.on_start_recording_callback = on_start_recording  # Start recording callback

    # Add screen switch callbacks
    def on_switch_screen(screen_name):
        """Generic screen switch callback"""
        print(f"[Callback] Switch to {screen_name}")
        switch_file = os.path.expanduser('~/.memscreen/switch_screen.txt')
        with open(switch_file, 'w') as f:
            f.write(screen_name)
        print(f"[Test] Wrote '{screen_name}' to {switch_file}")

    ball.on_switch_screen_callback = on_switch_screen

    # Set recording state (False = ready, True = recording)
    ball.setRecordingState_(False)  # Start in ready state (purple)

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
        from PyObjCTools import AppHelper

        app = NSApplication.sharedApplication()

        # Set activation policy to prevent Dock icon
        # NSApplicationActivationPolicyAccessory = 1 (runs in background, no dock icon)
        app.setActivationPolicy_(1)

        print("[FloatingBall] Starting event loop (no Dock icon)")
        AppHelper.runEventLoop()
    except KeyboardInterrupt:
        print("\n[FloatingBall] Test stopped by user")
        ball.close()


if __name__ == '__main__':
    main()
