"""macOS permission helpers for screen capture and input monitoring."""

from __future__ import annotations

import ctypes
import os
import platform
import subprocess
import sys
from typing import Dict, Tuple

_permission_cache = None


def _is_macos() -> bool:
    return sys.platform == "darwin"


def _application_services() -> ctypes.CDLL:
    return ctypes.CDLL(
        "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
    )


def _call_bool(lib: ctypes.CDLL, name: str) -> bool:
    fn = getattr(lib, name)
    fn.restype = ctypes.c_bool
    return bool(fn())


def _runtime_executable() -> str:
    return sys.executable or "python"


def _open_privacy_settings(anchor: str) -> None:
    try:
        subprocess.Popen(
            ["open", f"x-apple.systempreferences:com.apple.preference.security?{anchor}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass


def open_privacy_settings(area: str) -> bool:
    if not _is_macos():
        return False
    area_key = str(area or '').strip().lower()
    anchors = {
        'screen_recording': 'Privacy_ScreenCapture',
        'accessibility': 'Privacy_Accessibility',
        'input_monitoring': 'Privacy_ListenEvent',
    }
    anchor = anchors.get(area_key)
    if not anchor:
        return False
    _open_privacy_settings(anchor)
    return True


def create_permission_message() -> str:
    runtime_path = _runtime_executable()
    return (
        "Screen recording permission is required.\n\n"
        "Open macOS System Settings > Privacy & Security > Screen Recording, then allow:\n"
        f"- {runtime_path}\n"
        "- MemScreen.app (if installed in /Applications)\n\n"
        "After granting access, quit and reopen MemScreen."
    )


def check_screen_recording_permission(prompt: bool = False) -> Tuple[bool, str]:
    if not _is_macos():
        return True, "Not on macOS"

    try:
        lib = _application_services()
        granted = _call_bool(lib, "CGPreflightScreenCaptureAccess")
        if granted:
            return True, "Screen recording permission granted"
        if prompt:
            try:
                _call_bool(lib, "CGRequestScreenCaptureAccess")
            except Exception:
                pass
            _open_privacy_settings("Privacy_ScreenCapture")
        return False, create_permission_message()
    except Exception as e:
        return False, f"Failed to check screen recording permission: {e}"


def request_screen_recording_permission() -> bool:
    granted, _ = check_screen_recording_permission(prompt=True)
    return granted


def check_accessibility_permission() -> Tuple[bool, str]:
    if not _is_macos():
        return True, "Not on macOS"
    try:
        lib = _application_services()
        granted = _call_bool(lib, "AXIsProcessTrusted")
        if granted:
            return True, "Accessibility permission granted"
        return (
            False,
            "Accessibility permission is required. Allow the runtime process in "
            "System Settings > Privacy & Security > Accessibility.\n"
            f"Path: {_runtime_executable()}",
        )
    except Exception as e:
        return False, f"Failed to check Accessibility permission: {e}"


def check_input_monitoring_permission(prompt: bool = False) -> Tuple[bool, str]:
    if not _is_macos():
        return True, "Not on macOS"
    try:
        lib = _application_services()
        granted = _call_bool(lib, "CGPreflightListenEventAccess")
        if granted:
            return True, "Input Monitoring permission granted"
        if prompt:
            try:
                _call_bool(lib, "CGRequestListenEventAccess")
            except Exception:
                pass
            _open_privacy_settings("Privacy_ListenEvent")
        return (
            False,
            "Input Monitoring permission is required for keyboard shortcuts and key logging. "
            "Allow the runtime process in System Settings > Privacy & Security > Input Monitoring.\n"
            f"Path: {_runtime_executable()}",
        )
    except Exception as e:
        return False, f"Failed to check Input Monitoring permission: {e}"


def get_permission_diagnostics(prompt: bool = False) -> Dict[str, object]:
    screen_ok, screen_message = check_screen_recording_permission(prompt=prompt)
    accessibility_ok, accessibility_message = check_accessibility_permission()
    input_ok, input_message = check_input_monitoring_permission(prompt=prompt)
    runtime_path = _runtime_executable()
    return {
        "platform": platform.platform(),
        "runtime_executable": runtime_path,
        "app_bundle_hint": "/Applications/MemScreen.app",
        "screen_recording": {
            "granted": screen_ok,
            "message": screen_message,
            "settings_anchor": "Privacy_ScreenCapture",
        },
        "accessibility": {
            "granted": accessibility_ok,
            "message": accessibility_message,
            "settings_anchor": "Privacy_Accessibility",
        },
        "input_monitoring": {
            "granted": input_ok,
            "message": input_message,
            "settings_anchor": "Privacy_ListenEvent",
        },
    }


def get_cached_permission() -> bool:
    global _permission_cache
    return _permission_cache


def update_permission_cache(granted: bool):
    global _permission_cache
    _permission_cache = granted


def check_permission_with_cache() -> Tuple[bool, str]:
    global _permission_cache
    if _permission_cache is not None:
        return _permission_cache, "Cached permission result"
    granted, message = check_screen_recording_permission()
    _permission_cache = granted
    return granted, message
