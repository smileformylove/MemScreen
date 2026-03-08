"""Model catalog and download HTTP routes."""

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from memscreen.ollama_runtime import (
    build_ollama_env,
    is_external_models_dir,
    resolve_ollama_models_dir,
)

router = APIRouter(prefix="/models", tags=["models"])


class ModelDownloadBody(BaseModel):
    model: str
    timeout_sec: int = 1800


@router.get("/catalog")
async def models_catalog():
    """List required local models with install status from Ollama runtime."""
    from memscreen.config import get_config
    import os
    import requests

    cfg = get_config()
    base_url = cfg.ollama_base_url.rstrip("/")
    disable_models = os.getenv("MEMSCREEN_DISABLE_MODELS", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    required_specs = [
        (cfg.ollama_llm_model, "Chat", True),
        (cfg.ollama_vision_model, "Video tags", True),
        (cfg.ollama_embedding_model, "Memory retrieval", True),
        ("qwen3.5:0.8b", "Ultra-light chat/vision (optional)", False),
        ("qwen3.5:2b", "Fast chat/vision (optional)", False),
        ("qwen3.5:4b", "Balanced chat/vision (optional)", False),
        ("qwen3.5:9b", "Advanced chat/vision (optional)", False),
        ("qwen3-vl:4b", "Vision fallback (optional)", False),
        ("qwen2.5vl:7b", "Advanced vision fallback (optional)", False),
    ]

    deduped_specs = []
    seen_names = set()
    for name, purpose, required in required_specs:
        clean = str(name or "").strip()
        if not clean or clean in seen_names:
            continue
        seen_names.add(clean)
        deduped_specs.append((clean, purpose, required))

    installed = {}
    runtime_ready = False
    runtime_error = None
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=4)
        if resp.status_code != 200:
            runtime_error = f"HTTP {resp.status_code}"
        else:
            runtime_ready = True
            payload = resp.json() if resp.content else {}
            for item in payload.get("models", []) or []:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                installed[name] = {
                    "size_bytes": item.get("size"),
                    "modified_at": item.get("modified_at"),
                }
    except Exception as e:
        runtime_error = str(e)

    def _split_model_ref(name: str):
        clean = str(name or "").strip().lower()
        if not clean:
            return "", None
        if ":" in clean:
            base, tag = clean.rsplit(":", 1)
            if base and tag and "/" not in tag:
                return base, tag
        return clean, None

    def _find_installed_model(name: str):
        req_base, req_tag = _split_model_ref(name)
        if not req_base:
            return None, {}
        for installed_name, meta in installed.items():
            ins_base, ins_tag = _split_model_ref(installed_name)
            if ins_base != req_base:
                continue
            if req_tag is None:
                return installed_name, meta
            if ins_tag == req_tag:
                return installed_name, meta
            if req_tag == "latest" and ins_tag is None:
                return installed_name, meta
        return None, {}


    def _classify_model(name: str):
        normalized = str(name or '').strip().lower()
        family = 'other'
        if normalized.startswith('qwen3.5'):
            family = 'qwen3.5'
        elif normalized.startswith('qwen3-vl'):
            family = 'qwen3-vl'
        elif normalized.startswith('qwen3'):
            family = 'qwen3'
        elif normalized.startswith('qwen2.5vl'):
            family = 'qwen2.5vl'
        elif 'embed' in normalized:
            family = 'embedding'

        size_label = None
        _, tag = _split_model_ref(normalized)
        if tag and tag.endswith('b'):
            size_label = tag

        supports_chat = family != 'embedding'
        supports_vision = (
            family in {'qwen3.5', 'qwen3-vl', 'qwen2.5vl'}
            or 'vision' in normalized
            or 'vl' in normalized
        )

        recommended_use = 'general'
        if normalized.startswith('qwen3.5:0.8b') or normalized.startswith('qwen3:0.6b'):
            recommended_use = 'ultra_light'
        elif normalized.startswith('qwen3.5:2b') or normalized.startswith('qwen3:1.7b'):
            recommended_use = 'fast'
        elif normalized.startswith('qwen3.5:4b') or normalized.startswith('qwen3:4b'):
            recommended_use = 'balanced'
        elif normalized.startswith('qwen3.5:9b'):
            recommended_use = 'advanced'
        elif family in {'qwen3-vl', 'qwen2.5vl'}:
            recommended_use = 'vision_fallback'
        elif family == 'embedding':
            recommended_use = 'embedding'

        return {
            'family': family,
            'size_label': size_label,
            'supports_chat': supports_chat,
            'supports_vision': supports_vision,
            'recommended_use': recommended_use,
        }


    def _recommended_chat_score(name: str, capabilities: dict) -> int:
        recommended_use = capabilities.get('recommended_use', 'general')
        score_map = {
            'balanced': 500,
            'fast': 450,
            'ultra_light': 420,
            'advanced': 390,
            'vision_fallback': 300,
            'general': 200,
            'embedding': 0,
        }
        normalized = str(name or '').strip().lower()
        size_bonus = 0
        _, tag = _split_model_ref(normalized)
        if tag and tag.endswith('b'):
            try:
                size_bonus = int(float(tag[:-1]) * 10)
            except Exception:
                size_bonus = 0
        return score_map.get(recommended_use, 0) + size_bonus

    current_chat_model = None
    available_chat_models = []
    try:
        from memscreen.api.deps import get_chat_presenter

        chat_presenter = get_chat_presenter()
        if chat_presenter is not None:
            current_chat_model = chat_presenter.get_current_model()
            available_chat_models = chat_presenter.get_available_models()
    except Exception:
        current_chat_model = None
        available_chat_models = []

    available_chat_model_set = {str(model).strip().lower() for model in available_chat_models}

    models = []
    recommended_chat_model = None
    recommended_chat_score = -1
    for name, purpose, required in deduped_specs:
        matched_name, meta = _find_installed_model(name)
        effective_name = matched_name or name
        capabilities = _classify_model(effective_name)
        installed_name_normalized = str(matched_name or '').strip().lower()
        requested_name_normalized = str(name).strip().lower()
        chat_selectable = (
            requested_name_normalized in available_chat_model_set
            or installed_name_normalized in available_chat_model_set
        )
        if chat_selectable and capabilities['supports_chat']:
            score = _recommended_chat_score(effective_name, capabilities)
            if score > recommended_chat_score:
                recommended_chat_score = score
                recommended_chat_model = matched_name or name
        models.append(
            {
                "name": name,
                "purpose": purpose,
                "required": required,
                "installed": matched_name is not None,
                "installed_name": matched_name,
                "size_bytes": meta.get("size_bytes"),
                "modified_at": meta.get("modified_at"),
                "family": capabilities["family"],
                "size_label": capabilities["size_label"],
                "supports_chat": capabilities["supports_chat"],
                "supports_vision": capabilities["supports_vision"],
                "recommended_use": capabilities["recommended_use"],
                "chat_selectable": chat_selectable,
                "recommended_chat_default": (matched_name or name) == recommended_chat_model,
            }
        )

    if recommended_chat_model is None and current_chat_model:
        recommended_chat_model = current_chat_model

    if recommended_chat_model is not None:
        for item in models:
            item['recommended_chat_default'] = (
                item.get('installed_name') or item['name']
            ) == recommended_chat_model

    models_dir = resolve_ollama_models_dir()
    return {
        "base_url": base_url,
        "models_dir": models_dir,
        "models_dir_external": is_external_models_dir(models_dir),
        "current_chat_model": current_chat_model,
        "recommended_chat_model": recommended_chat_model,
        "available_chat_models": available_chat_models,
        "models_disabled": disable_models,
        "runtime_ready": runtime_ready,
        "runtime_error": runtime_error,
        "models": models,
    }


@router.post("/download")
async def models_download(body: ModelDownloadBody):
    """Download one local model through Ollama runtime."""
    from memscreen.config import get_config
    import subprocess
    import time
    import shutil
    import requests

    model_name = str(body.model or "").strip()
    if not model_name:
        raise HTTPException(status_code=400, detail="model is required")

    timeout_sec = int(body.timeout_sec) if int(body.timeout_sec) > 0 else 1800
    timeout_sec = max(60, min(timeout_sec, 7200))
    base_url = get_config().ollama_base_url.rstrip("/")

    def _ensure_ollama_runtime() -> bool:
        try:
            health = requests.get(f"{base_url}/api/tags", timeout=2)
            if health.status_code == 200:
                return True
        except Exception:
            pass

        ollama_bin = shutil.which("ollama")
        if not ollama_bin:
            return False

        try:
            subprocess.Popen(
                [ollama_bin, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                env=build_ollama_env(),
            )
        except Exception:
            return False

        for _ in range(6):
            try:
                health = requests.get(f"{base_url}/api/tags", timeout=2)
                if health.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(1.0)
        return False

    def _pull():
        if not _ensure_ollama_runtime():
            return {
                "ok": False,
                "error": "Ollama runtime is unavailable. Please start Ollama and retry.",
            }

        try:
            response = requests.post(
                f"{base_url}/api/pull",
                json={"name": model_name, "stream": False},
                timeout=timeout_sec,
            )
        except Exception as e:
            return {"ok": False, "error": f"Ollama is unavailable: {e}"}

        if response.status_code != 200:
            detail = ""
            try:
                payload = response.json()
                detail = str(payload.get("error") or payload.get("detail") or "").strip()
            except Exception:
                detail = response.text.strip()
            error = (
                f"Model download failed (HTTP {response.status_code})"
                + (f": {detail}" if detail else "")
            )
            return {"ok": False, "error": error}

        status_text = "success"
        try:
            payload = response.json() if response.content else {}
            status_text = str(payload.get("status") or payload.get("detail") or "success")
        except Exception:
            pass
        return {"ok": True, "status": status_text}

    result = await run_in_threadpool(_pull)
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error", "Model download failed"))
    return {
        "ok": True,
        "model": model_name,
        "status": result.get("status", "success"),
    }
