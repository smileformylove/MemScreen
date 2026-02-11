#!/usr/bin/env python3
"""
Start MemScreen API server only (for Flutter / other frontends).
Does not start Kivy. Default: http://127.0.0.1:8765
Config: api.host, api.port in config file or MEMSCREEN_API_PORT, MEMSCREEN_API_HOST.
"""

if __name__ == "__main__":
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
