# MemScreen macOS Window Visibility - Current Status

## Problem Summary

The MemScreen.app application launches successfully and creates a window, but the window is **not visible** to the user despite:
- Window existing in the window system
- Window having focus
- Process being frontmost
- Window being at a visible position (100, 100)

## Diagnostic Results

### What Works ✅
1. Application launches successfully
2. Process runs without crashing
3. Window is created with correct properties:
   - Position: (100, 100) - visible area
   - Size: 1200x828
   - Focused: true
   - Process frontmost: true
4. All components initialize correctly:
   - Kivy v2.3.1
   - OpenGL (Metal backend)
   - SDL2 provider
   - Ollama service
   - Memory system

### What Doesn't Work ❌
- Window is not visible to the user
- No error messages in logs
- No security prompts from macOS

## Technical Analysis

### Root Cause
This is a **macOS-specific SDL2/Kivy window rendering issue**. The window exists in the window manager but macOS is not rendering it to the display.

### Possible Causes
1. **macOS Security Policy**: macOS may be blocking SDL2 from creating visible windows without proper permissions
2. **Window Compositing**: The window might be on a different desktop space or layer
3. **SDL2 Compatibility**: SDL2 bundled with Kivy may have compatibility issues with macOS
4. **Display Configuration**: Multiple displays or desktop spaces may cause window placement issues

### System Configuration
- macOS Version: Darwin 24.5.0
- Desktop Spaces: 2 (window may be on wrong space)
- Displays: At least 2 (main display + secondary positioned above)
- Python: 3.13.3
- Kivy: 2.3.1
- Window Provider: SDL2

## Fixes Attempted

### 1. Runtime Hook Configuration ✅
- Set SDL_VIDEO_WINDOW_POS environment variable
- Disabled SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS
- Fixed DYLD_LIBRARY_PATH for SDL2 libraries

### 2. Window Activation Code ✅
- Added `Window.show()` and `Window.raise_window()` calls
- Implemented multiple activation attempts with delays
- Added `Window.request_attention()` calls
- Added osascript activation using subprocess

### 3. Enhanced Wrapper Script ✅
- Created aggressive activation sequence (10 attempts over 10 seconds)
- Multiple activation methods per attempt:
  - osascript activate
  - System Events frontmost
  - Force window position
  - Force window size

### 4. Window Positioning ✅
- Manually moved window to (100, 100)
- Forced process to frontmost
- Confirmed window has focus

## Current Status

The window exists and has all the right properties, but is still not visible. This suggests the issue is at the **macOS window compositing/rendering level**, not at the Kivy/application level.

## Recommended Solutions

### Option A: Grant macOS Permissions (Try First)
Some users have reported that granting Screen Recording permissions fixes SDL2 window issues:

1. **System Settings** → **Privacy & Security** → **Screen Recording**
2. Add **Terminal** (or **Python** if available)
3. Restart Terminal
4. Run the app again

### Option B: Use Alternative UI Framework (Recommended)
Kivy/SDL2 appears to have fundamental compatibility issues with your macOS configuration. Consider switching to:

1. **Tkinter** (easiest, system-bundled):
   ```bash
   # Already installed with Python
   python3 -c "import tkinter; print('Tkinter available')"
   ```

2. **PyQt5** (more reliable):
   ```bash
   pip install PyQt5
   ```

### Option C: Check Desktop Space
The window might be on the second desktop space:

1. Press **Control + Arrow Key** to switch desktop spaces
2. Press **F3** (Mission Control) to see all windows
3. Press **Command + Tab** to cycle through apps

### Option D: Run from Source
If you need to use the app immediately:

```bash
cd /Users/jixiangluo/Documents/project_code/repository/MemScreen
source venv/bin/activate
python start.py
```

This bypasses the packaging issues and runs the app directly with better window management.

## Testing Commands

### Check if window exists:
```bash
osascript -e 'tell application "System Events" to tell process "MemScreen" to get properties of window 1'
```

### Force window to front:
```bash
osascript -e 'tell application "MemScreen" to activate'
osascript -e 'tell application "System Events" to set frontmost of process "MemScreen" to true'
```

### Move window to visible position:
```bash
osascript -e 'tell application "System Events" to tell process "MemScreen" to tell window 1 to set position to {100, 100}'
```

### View all windows:
```bash
osascript -e 'tell application "System Events" to set winList to {} & repeat with proc in every process & try & repeat with win in every window of proc & set end of winList to {name of proc, name of win, position of win} & end repeat & end try & end repeat & return winList'
```

## Files Modified

1. **[memscreen/ui/kivy_app.py](memscreen/ui/kivy_app.py)** - Enhanced window activation with multiple retries
2. **[pyinstaller/rthook/pyi_rthook_kivy.py](pyinstaller/rthook/pyi_rthook_kivy.py)** - SDL2 environment configuration
3. **[/Applications/MemScreen.app/Contents/MacOS/MemScreen](/Applications/MemScreen.app/Contents/MacOS/MemScreen)** - Aggressive wrapper script

## Next Steps

Based on your preference, choose one of the following:

1. **Try granting Screen Recording permission** (5 minutes)
2. **Use the app from source** (bypasses packaging issues)
3. **Rebuild with PyQt5** (more reliable UI framework)
4. **Continue debugging SDL2** (may require deeper macOS troubleshooting)

Let me know which option you'd like to pursue, or if the window is now visible after trying Option A or C.

## Contact

- Email: jixiangluo85@gmail.com
- GitHub: https://github.com/smileformylove/MemScreen/issues
