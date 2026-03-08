"""System/configuration HTTP routes."""

from fastapi import APIRouter, Query

router = APIRouter(tags=["system"])


@router.get("/config")
async def get_config_readonly():
    """Read-only config for Flutter (ollama URL, db path, etc.)."""
    from memscreen.config import get_config

    config = get_config()
    return {
        "ollama_base_url": config.ollama_base_url,
        "db_dir": str(config.db_dir),
        "videos_dir": str(config.videos_dir),
    }




@router.get("/permissions/status")
async def permission_status(prompt: bool = Query(False)):
    """Return macOS permission diagnostics for recording and tracking."""
    try:
        from memscreen.macos_permissions import get_permission_diagnostics

        return get_permission_diagnostics(prompt=prompt)
    except Exception as e:
        return {
            "platform": "unknown",
            "runtime_executable": "",
            "app_bundle_hint": "/Applications/MemScreen.app",
            "screen_recording": {"granted": False, "message": str(e)},
            "accessibility": {"granted": False, "message": str(e)},
            "input_monitoring": {"granted": False, "message": str(e)},
        }


@router.post("/permissions/open-settings")
async def open_permission_settings(area: str = Query(...)):
    """Open a specific macOS privacy settings pane."""
    try:
        from memscreen.macos_permissions import open_privacy_settings

        ok = open_privacy_settings(area)
        return {"ok": ok, "area": area}
    except Exception as e:
        return {"ok": False, "area": area, "error": str(e)}


@router.get("/health")
async def health(include_db: bool = Query(False), include_ollama: bool = Query(False)):
    """Lightweight health check with optional deeper dependency probes."""
    out = {"status": "ok", "mode": "light"}

    if include_db:
        try:
            from memscreen.config import get_config
            import sqlite3

            config = get_config()
            conn = sqlite3.connect(str(config.db_path))
            conn.close()
            out["db"] = "ok"
        except Exception as e:
            out["db"] = f"error: {str(e)}"
            out["status"] = "degraded"
        out["mode"] = "db"

    if include_ollama:
        try:
            from memscreen.config import get_config
            import requests

            config = get_config()
            response = requests.get(f"{config.ollama_base_url}/api/tags", timeout=2)
            out["ollama"] = (
                "ok" if response.status_code == 200 else f"status_{response.status_code}"
            )
        except Exception as e:
            out["ollama"] = f"error: {str(e)}"
            out["status"] = "degraded"
        out["mode"] = "full" if include_db else "ollama"

    return out
