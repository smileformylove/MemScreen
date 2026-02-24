"""Model capability services for chat pipeline."""

from __future__ import annotations

import json
import subprocess
from typing import Any, Dict, Iterator, List, Optional

import requests


class ChatModelCapabilityService:
    """Wrapper around model backend APIs for chat and vision calls."""

    def __init__(self, ollama_base_url: str) -> None:
        self.ollama_base_url = ollama_base_url.rstrip("/")

    def generate_once(
        self,
        *,
        model: str,
        prompt: str,
        images: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
        timeout: float = 12.0,
    ) -> str:
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if images:
            payload["images"] = images
        if options:
            payload["options"] = options

        try:
            resp = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=timeout,
            )
            if resp.status_code != 200:
                return ""
            data = resp.json()
            return str(data.get("response", "")).strip()
        except Exception:
            return ""

    def generate_json_once(
        self,
        *,
        model: str,
        prompt: str,
        images: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
        timeout: float = 12.0,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if images:
            payload["images"] = images
        if options:
            payload["options"] = options

        try:
            resp = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=timeout,
            )
            if resp.status_code != 200:
                return {}
            return resp.json()
        except Exception:
            return {}

    def list_models(self, timeout: float = 10.0) -> List[str]:
        try:
            resp = requests.get(f"{self.ollama_base_url}/api/tags", timeout=timeout)
            if resp.status_code != 200:
                return []
            data = resp.json()
            models = data.get("models", []) or []
            out: List[str] = []
            for model in models:
                if isinstance(model, dict):
                    name = str(model.get("name", "")).strip()
                    if name:
                        out.append(name)
            return out
        except Exception:
            return []

    def stream_generate(self, payload: Dict[str, Any], timeout: float = 120.0) -> Iterator[Dict[str, Any]]:
        stream_payload = dict(payload)
        stream_payload["stream"] = True
        resp = requests.post(
            f"{self.ollama_base_url}/api/generate",
            json=stream_payload,
            stream=True,
            timeout=timeout,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"API error: {resp.status_code}")
        for line in resp.iter_lines():
            if not line:
                continue
            try:
                if isinstance(line, bytes):
                    line = line.decode("utf-8", errors="ignore")
                yield json.loads(line)
            except Exception:
                continue

    def pull_model(self, model_name: str, timeout: float = 240.0) -> bool:
        """Try to pull one model locally with ollama CLI."""
        try:
            pull = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if pull.returncode != 0:
                stderr = (pull.stderr or "").strip()
                print(f"[Chat] ollama pull failed for {model_name}: {stderr[:300]}")
                return False
            return True
        except Exception as e:
            print(f"[Chat] ollama pull error for {model_name}: {e}")
            return False


class NoopChatModelCapabilityService(ChatModelCapabilityService):
    """No-model implementation that keeps chat presenter operational."""

    def __init__(self) -> None:
        super().__init__(ollama_base_url="http://127.0.0.1:11434")

    def generate_once(
        self,
        *,
        model: str,
        prompt: str,
        images: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
        timeout: float = 12.0,
    ) -> str:
        return ""

    def generate_json_once(
        self,
        *,
        model: str,
        prompt: str,
        images: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
        timeout: float = 12.0,
    ) -> Dict[str, Any]:
        return {}

    def list_models(self, timeout: float = 10.0) -> List[str]:
        return []

    def stream_generate(self, payload: Dict[str, Any], timeout: float = 120.0) -> Iterator[Dict[str, Any]]:
        if False:
            yield {}
        return

    def pull_model(self, model_name: str, timeout: float = 240.0) -> bool:
        return False
