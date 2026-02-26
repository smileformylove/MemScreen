#!/usr/bin/env python3
"""
Start MemScreen API server only (NO Kivy UI).
For Flutter frontend - use this instead of start_api.py
"""

import os
from pathlib import Path
import uvicorn
import sys
from typing import Optional


def _inject_embedded_source_path() -> Optional[Path]:
    """
    Ensure embedded backend source is importable in packaged runtime.

    Priority:
    1) MEMSCREEN_BACKEND_SRC (explicit path from bootstrap)
    2) <this_script_dir>/src (embedded source in app bundle)
    """
    candidates = []
    env_src = os.getenv("MEMSCREEN_BACKEND_SRC", "").strip()
    if env_src:
        candidates.append(Path(env_src))
    candidates.append(Path(__file__).resolve().parent / "src")

    for candidate in candidates:
        pkg_init = candidate / "memscreen" / "__init__.py"
        if candidate.is_dir() and pkg_init.exists():
            src = str(candidate)
            if src not in sys.path:
                sys.path.insert(0, src)
            print(f"[API] Using embedded source: {src}")
            return candidate

    print(
        "[API] Warning: embedded source path not found. "
        "Falling back to default Python import path."
    )
    return None


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
    _inject_embedded_source_path()
    _hide_dock_icon_on_macos()

    # Import after injecting embedded source path so packaged app always
    # resolves to bundled backend modules.
    from memscreen.config import get_config
    from memscreen.api.app import app as fastapi_app

    cfg = get_config()
    host = cfg.api_host
    port = cfg.api_port

    print(f"[API] Starting on http://{host}:{port}")
    print("[API] Backend only - NO Kivy UI will be started")

    uvicorn.run(
        fastapi_app,
        host=host,
        port=port,
        reload=False,
    )
