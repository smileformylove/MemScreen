#!/usr/bin/env python3
"""
Start MemScreen API server only (NO Kivy UI).
For Flutter frontend - use this instead of start_api.py
"""

import uvicorn
import sys
from memscreen.config import get_config


def _hide_dock_icon_on_macos() -> None:
    """Run API process as background-only on macOS to avoid Dock bouncing icon."""
    if sys.platform != "darwin":
        return
    try:
        import AppKit  # type: ignore

        app = AppKit.NSApplication.sharedApplication()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyProhibited)
    except Exception as e:
        # Non-fatal: API should still start even if Dock hint fails.
        print(f"[API] Warning: failed to hide Dock icon on macOS: {e}")


if __name__ == "__main__":
    _hide_dock_icon_on_macos()
    cfg = get_config()
    host = cfg.api_host
    port = cfg.api_port

    print(f"[API] Starting on http://{host}:{port}")
    print("[API] Backend only - NO Kivy UI will be started")

    uvicorn.run(
        "memscreen.api.app:app",
        host=host,
        port=port,
        reload=False,
    )
