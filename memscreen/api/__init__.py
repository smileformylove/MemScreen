"""
MemScreen HTTP API for Flutter and other frontends.

Start with: python -m memscreen.api
Or: uvicorn memscreen.api.app:app --host 127.0.0.1 --port 8765
"""

from .app import app

__all__ = ["app"]
