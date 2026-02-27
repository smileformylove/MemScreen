"""Model capability services for recording pipeline."""

from __future__ import annotations

import time
from typing import Optional

import numpy as np

from memscreen.cv2_loader import get_cv2


class RecordingModelCapabilityService:
    """Model-facing capability wrapper with graceful degradation."""

    def __init__(
        self,
        ollama_base_url: str,
        vision_model: str = "qwen2.5vl:3b",
        vision_timeout_sec: int = 6,
        recovery_cooldown_sec: int = 30,
    ) -> None:
        self._memory_enrichment_enabled = True
        self._vision_analysis_enabled = True
        self._model_unavailable_reason: Optional[str] = None
        self._ollama_base_url = ollama_base_url.rstrip("/")
        self._vision_generate_url = f"{ollama_base_url.rstrip('/')}/api/generate"
        self._vision_model = vision_model
        self._vision_timeout_sec = vision_timeout_sec
        self._recovery_cooldown_sec = max(3, int(recovery_cooldown_sec))
        self._model_disabled_until_ts = 0.0
        self._easyocr_reader = None
        self._backend_probe_ok: Optional[bool] = None
        self._backend_probe_next_ts: float = 0.0

    @property
    def memory_enrichment_enabled(self) -> bool:
        return self._memory_enrichment_enabled

    @property
    def vision_analysis_enabled(self) -> bool:
        return self._vision_analysis_enabled

    def can_enrich_memory(self, memory_system) -> bool:
        self._maybe_recover_model_features()
        return bool(memory_system and self._memory_enrichment_enabled)

    def is_async_enrichment_available(self, timeout_sec: float = 0.8) -> bool:
        """
        Fast readiness check for recording-time async enrichment.

        Returns False quickly when model backend is unavailable so recording flow
        can skip async enrichment without hanging in pending state.
        """
        self._maybe_recover_model_features()
        if not self._memory_enrichment_enabled or not self._vision_analysis_enabled:
            return False

        now = time.time()
        if self._backend_probe_ok is not None and now < self._backend_probe_next_ts:
            return bool(self._backend_probe_ok)

        try:
            import requests

            resp = requests.get(f"{self._ollama_base_url}/api/tags", timeout=timeout_sec)
            ok = resp.status_code == 200
            self._backend_probe_ok = ok
            # Keep success probes fresh but cheap; failures cached longer.
            self._backend_probe_next_ts = now + (12.0 if ok else 25.0)
            if not ok:
                self._disable_model_features(f"ollama health check status={resp.status_code}")
            return ok
        except Exception as e:
            self._backend_probe_ok = False
            self._backend_probe_next_ts = now + 25.0
            self._disable_model_features(str(e))
            return False

    def is_model_backend_error(self, error: Exception) -> bool:
        """Return whether an exception indicates model backend is unavailable."""
        msg = str(error).lower()
        indicators = [
            "failed to connect to ollama",
            "connection refused",
            "max retries exceeded",
            "newconnectionerror",
            "timed out",
            "name or service not known",
            "temporary failure in name resolution",
            "failed to establish a new connection",
            "connection error",
        ]
        return any(key in msg for key in indicators)

    def consume_model_error(self, error: Exception, action: str) -> bool:
        """Handle model-backend failures and return whether error was consumed."""
        if not self.is_model_backend_error(error):
            return False
        self._disable_model_features(str(error))
        print(f"[RecordingPresenter] Skip {action}: {error}")
        return True

    def _disable_model_features(self, reason: str) -> None:
        """Disable model-dependent paths so recording can continue independently."""
        already_disabled = (not self._memory_enrichment_enabled and not self._vision_analysis_enabled)
        self._memory_enrichment_enabled = False
        self._vision_analysis_enabled = False
        self._model_unavailable_reason = reason
        self._model_disabled_until_ts = time.time() + float(self._recovery_cooldown_sec)
        self._backend_probe_ok = False
        self._backend_probe_next_ts = self._model_disabled_until_ts
        if not already_disabled:
            print(f"[RecordingPresenter] Model backend unavailable. Running in recording-only mode: {reason}")

    def _maybe_recover_model_features(self) -> None:
        """Auto-recover model paths after cooldown to support seamless backend recovery."""
        if self._memory_enrichment_enabled and self._vision_analysis_enabled:
            return
        if time.time() < self._model_disabled_until_ts:
            return
        self._memory_enrichment_enabled = True
        self._vision_analysis_enabled = True
        self._backend_probe_ok = None
        self._backend_probe_next_ts = 0.0
        print("[RecordingPresenter] Retrying model capabilities after cooldown")

    def _get_easyocr_reader(self):
        """Lazy-init easyocr reader for local OCR fallback."""
        if self._easyocr_reader is not None:
            return self._easyocr_reader
        try:
            import easyocr  # type: ignore

            self._easyocr_reader = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
            return self._easyocr_reader
        except Exception as e:
            print(f"[RecordingPresenter] easyocr unavailable: {e}")
            self._easyocr_reader = False
            return None

    def _extract_text_with_easyocr(self, frame) -> str:
        """Extract meaningful text using easyocr as a robust local fallback."""
        try:
            cv2 = get_cv2()
            if cv2 is None:
                return ""

            reader = self._get_easyocr_reader()
            if not reader:
                return ""

            h, w = frame.shape[:2]
            img = frame
            if w > 1600:
                new_w = 1600
                new_h = int(h * (new_w / w))
                img = cv2.resize(frame, (new_w, new_h))

            try:
                results = reader.readtext(img, detail=0, paragraph=True)
            except Exception:
                results = []

            clean_items = []
            for item in results:
                text = " ".join(str(item).split())
                if len(text) >= 5:
                    clean_items.append(text)
                if len(clean_items) >= 6:
                    break

            if not clean_items:
                return ""
            return " | ".join(clean_items)
        except Exception as e:
            print(f"[RecordingPresenter] easyocr fallback failed: {e}")
            return ""

    def extract_text_from_frame(self, frame, use_vision: bool = True) -> str:
        """Extract text and scene context from one frame."""
        try:
            cv2 = get_cv2()
            if cv2 is None:
                return "Screen captured (analysis unavailable: cv2 not available)"

            self._maybe_recover_model_features()
            if use_vision and self._vision_analysis_enabled:
                import base64
                import requests

                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                img_str = base64.b64encode(buffer).decode("utf-8")

                prompt = (
                    "Describe this screenshot briefly for memory timeline.\n"
                    "Return one line with: App, Key text, Main action."
                )

                response = requests.post(
                    self._vision_generate_url,
                    json={
                        "model": self._vision_model,
                        "prompt": prompt,
                        "images": [img_str],
                        "stream": False,
                        "options": {
                            "num_predict": 160,
                            "temperature": 0.2,
                            "top_p": 0.8,
                        },
                    },
                    timeout=self._vision_timeout_sec,
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result.get("response", "").strip()
                    if content and content.lower() not in ["no text", "none", "no text found"]:
                        return content

        except Exception as e:
            if self.consume_model_error(e, "vision analysis"):
                print("[Recording] Model backend unavailable, using local OCR/fallback only")
            elif "timed out" in str(e).lower():
                print(f"[Recording] Vision API timeout ({self._vision_timeout_sec}s), using fallback")
            else:
                print(f"[Recording] Vision API error: {e}")

        ocr_text = self._extract_text_with_easyocr(frame)
        if ocr_text:
            return f"OCR detected: {ocr_text}"

        return self.extract_text_fallback(frame)

    def extract_text_fallback(self, frame) -> str:
        """Heuristic local fallback independent from external model backend."""
        cv2 = get_cv2()
        if cv2 is None:
            return "Screen captured (analysis unavailable: cv2 not available)"

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            text_density = np.sum(gray > 200) / gray.size
            brightness = float(np.mean(gray))

            if brightness > 200:
                lighting = "light theme"
            elif brightness < 80:
                lighting = "dark theme"
            else:
                lighting = "mixed theme"

            if text_density > 0.4:
                content = "text-heavy content (code, document, or terminal)"
            elif text_density > 0.2:
                content = "mixed content (text and graphics)"
            else:
                content = "graphical content (images, video, or design)"

            return f"Screen capture showing {content} with {lighting}"
        except Exception as e:
            return f"Screen captured (analysis unavailable: {str(e)[:30]})"


class NoopRecordingModelCapabilityService(RecordingModelCapabilityService):
    """No-model implementation for full recording-only mode."""

    def __init__(self) -> None:
        self._memory_enrichment_enabled = False
        self._vision_analysis_enabled = False
        self._model_unavailable_reason = "disabled by configuration"
        self._vision_generate_url = ""
        self._vision_model = ""
        self._vision_timeout_sec = 0
        self._easyocr_reader = False

    def can_enrich_memory(self, memory_system) -> bool:
        return False

    def consume_model_error(self, error: Exception, action: str) -> bool:
        return False

    def extract_text_from_frame(self, frame, use_vision: bool = True) -> str:
        return self.extract_text_fallback(frame)

    def is_async_enrichment_available(self, timeout_sec: float = 0.8) -> bool:
        return False
