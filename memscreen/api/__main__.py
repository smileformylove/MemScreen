"""
Run API server: python -m memscreen.api
Uses config api.host / api.port (default 127.0.0.1:8765).
"""

import uvicorn
from memscreen.config import get_config

if __name__ == "__main__":
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
