# Archive

This directory contains archived components that are no longer actively maintained.

## memscreen_ui_kivy/

**Status:** Archived as of v0.6.2

**Reason:** The project has migrated to Flutter as the primary UI framework. The Kivy-based desktop UI has been archived for historical reference.

**Contents:**
- `memscreen/ui/` - Original Kivy-based desktop UI
  - `kivy_app.py` - Main Kivy application
  - `floating_ball.py` - Floating ball implementation
  - `floating_ball_native.py` - Native macOS floating ball
  - `region_selector.py` - Region selection UI
  - `native_region_selector.py` - Native macOS region selector

**Migration:**
- New Flutter UI: `frontend/flutter/`
- API Backend: `memscreen/api/`

**Notes:**
- The Kivy UI was fully functional and can still be used if needed
- To use: Copy back to `memscreen/ui/` and install Kivy dependencies
- See `pyproject.toml` for Kivy dependencies under optional dependencies

**Date Archived:** February 14, 2026
