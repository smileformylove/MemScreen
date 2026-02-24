#!/usr/bin/env python3
"""
Start MemScreen API server only (for Flutter / other frontends).
Does not start Kivy. Default: http://127.0.0.1:8765
Config: api.host, api.port in config file or MEMSCREEN_API_PORT, MEMSCREEN_API_HOST.
"""

import sys


def _hide_dock_icon_on_macos() -> None:
    """Run API process as background-only on macOS to avoid Dock bouncing icon."""
    if sys.platform != "darwin":
        return
    try:
        import AppKit  # type: ignore

        app = AppKit.NSApplication.sharedApplication()
        app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyProhibited)
    except Exception as e:
        print(f"[MemScreen API] Warning: failed to hide Dock icon on macOS: {e}")


if __name__ == "__main__":
    _hide_dock_icon_on_macos()
    import uvicorn
    from memscreen.config import get_config

    cfg = get_config()
    host = cfg.api_host
    port = cfg.api_port
    print(f"[MemScreen API] Starting on http://{host}:{port}")
    uvicorn.run(
        "memscreen.api.app:app",
        host=host,
        port=port,
        reload=False,
    )
