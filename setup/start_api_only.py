#!/usr/bin/env python3
"""
Start MemScreen API server only (NO Kivy UI).
For Flutter frontend - use this instead of start_api.py
"""

import uvicorn
from memscreen.config import get_config

if __name__ == "__main__":
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
