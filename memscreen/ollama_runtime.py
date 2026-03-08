"""Helpers for local Ollama runtime configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional


OLLAMA_MODELS_ENV_KEYS = ("MEMSCREEN_OLLAMA_MODELS_DIR", "OLLAMA_MODELS")


def resolve_ollama_models_dir() -> Optional[str]:
    """Resolve the preferred Ollama models directory."""
    for key in OLLAMA_MODELS_ENV_KEYS:
        raw = os.getenv(key, "").strip()
        if raw:
            return str(Path(raw).expanduser())

    ollama_home = Path.home() / ".ollama"
    try:
        if ollama_home.exists():
            return str(ollama_home.resolve())
    except Exception:
        return str(ollama_home)
    return None


def is_external_models_dir(path: Optional[str]) -> bool:
    if not path:
        return False
    try:
        resolved = Path(path).expanduser().resolve()
    except Exception:
        resolved = Path(path).expanduser()
    return str(resolved).startswith("/Volumes/")


def build_ollama_env(base_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    env = dict(base_env or os.environ)
    models_dir = resolve_ollama_models_dir()
    if models_dir:
        env["OLLAMA_MODELS"] = models_dir
    return env
