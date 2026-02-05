"""
PyInstaller runtime hook for Kivy on macOS

Ensures SDL2 and Kivy work correctly when bundled with PyInstaller.
"""

import os
import sys

# Set up Kivy environment for packaged app
if getattr(sys, 'frozen', False) and sys.platform == 'darwin':
    # Ensure Kivy can find its modules
    kivy_path = os.path.join(sys._MEIPASS, 'kivy')
    if kivy_path not in sys.path:
        sys.path.insert(0, kivy_path)

    # Disable SDL2 video driver checks that might fail in packaged apps
    # This forces Kivy to use the SDL2 provider bundled with the app
    os.environ['KIVY_WINDOW'] = 'sdl2'
    os.environ['KIVY_TEXT'] = 'sdl2'
    os.environ['KIVY_AUDIO'] = 'sdl2'
    os.environ['KIVY_IMAGE'] = 'sdl2, imageio'

    # Force window to be visible and positioned on screen
    # These SDL2 environment variables help on macOS
    os.environ['SDL_VIDEO_WINDOW_POS'] = '100,100'
    os.environ['SDL_VIDEO_CENTERED'] = '0'
    os.environ['SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS'] = '0'

    # Ensure proper threading for SDL2
    # Note: DON'T set SDL_VIDEODRIVER on macOS - let SDL2 use the default (Cocoa)
    # os.environ['SDL_AUDIODRIVER'] = 'dummy'  # Don't force dummy audio
    # os.environ['SDL_VIDEODRIVER'] = 'x11'   # WRONG for macOS!

    # Fix dylib search path for SDL2
    dylib_path = os.path.join(sys._MEIPASS, 'kivy', '.dylibs')
    if os.path.exists(dylib_path):
        os.environ['DYLD_LIBRARY_PATH'] = dylib_path
        print(f"[Runtime Hook] Set DYLD_LIBRARY_PATH to: {dylib_path}")

print("[Runtime Hook] Kivy environment configured for packaged app")
