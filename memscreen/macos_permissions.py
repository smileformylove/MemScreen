### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                ###

"""
macOS Screen Recording Permission Checker

This module provides utilities to check and request screen recording permissions
on macOS, preventing repeated permission prompts.
"""

import sys
import os


# Cache permission check result to avoid repeated prompts
_permission_cache = None


def check_screen_recording_permission() -> tuple[bool, str]:
    """
    Check if the app has screen recording permission on macOS.

    Returns:
        tuple: (has_permission: bool, message: str)
    """
    if sys.platform != 'darwin':
        return True, "Not on macOS"

    try:
        # First, try using CGDisplayCreateImage to check permission
        # This method is less likely to trigger permission dialogs
        try:
            from Quartz.CoreGraphics import (
                CGMainDisplayID,
                CGDisplayCreateImage,
                CGImageRelease
            )
            import ctypes

            display_id = CGMainDisplayID()
            image = CGDisplayCreateImage(display_id)
            if image:
                # Permission granted
                CGImageRelease(image)
                return True, "Screen recording permission granted"
            else:
                # Permission denied
                return False, create_permission_message()
        except ImportError:
            # Quartz not available, fall back to PIL
            pass
        except Exception as cg_error:
            # If it's not a permission error, try PIL method
            error_msg = str(cg_error).lower()
            if "permission" in error_msg or "denied" in error_msg:
                return False, create_permission_message()

        # Fall back to PIL method if Quartz is not available
        from PIL import ImageGrab

        # Try to capture a 1x1 pixel area
        try:
            test_img = ImageGrab.grab(bbox=(0, 0, 1, 1))
            # If we get here, permission is granted
            return True, "Screen recording permission granted"
        except Exception as e:
            error_msg = str(e).lower()
            # Check for specific permission-related errors
            if "permission" in error_msg or "denied" in error_msg:
                return False, create_permission_message()
            elif "could not create image from display" in error_msg or "identify image file" in error_msg:
                # This happens when running without a display (e.g., SSH, CI)
                # In this case, we can't determine permission status, so assume granted
                # and let the actual recording attempt fail if needed
                return True, "Cannot verify permission (no display), assuming granted"
            else:
                # Some other error - might be permission issue
                return False, f"Error checking permission: {e}"

    except ImportError:
        # PIL not available
        return False, "PIL/Pillow not available"
    except Exception as e:
        # Unexpected error
        return False, f"Unexpected error: {e}"


def create_permission_message() -> str:
    """Create a helpful message for granting screen recording permission."""
    return """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MemScreen 



1. ""
2. ""
3. ""
4. "+"
5. "" MemScreen.app
6.  MemScreen.app  ✓
7.  MemScreen 

 MemScreen 

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def request_screen_recording_permission() -> bool:
    """
    Request screen recording permission by attempting to capture the screen.

    This will trigger macOS's permission prompt if not already granted.

    Returns:
        bool: True if permission is granted, False otherwise
    """
    has_permission, message = check_screen_recording_permission()

    if not has_permission:
        # Print the permission message
        print(message)
        return False

    return True


def get_cached_permission() -> bool:
    """
    Get cached permission result to avoid repeated checks.

    Returns:
        bool: True if permission was previously granted, None if not checked yet
    """
    global _permission_cache
    return _permission_cache


def update_permission_cache(granted: bool):
    """Update the permission cache."""
    global _permission_cache
    _permission_cache = granted


def check_permission_with_cache() -> tuple[bool, str]:
    """
    Check permission with caching to avoid repeated prompts.

    Returns:
        tuple: (has_permission: bool, message: str)
    """
    global _permission_cache

    if _permission_cache is not None:
        # Use cached result
        return _permission_cache, "Cached permission result"

    # Check permission
    has_permission, message = check_screen_recording_permission()

    # Cache the result
    _permission_cache = has_permission

    return has_permission, message
