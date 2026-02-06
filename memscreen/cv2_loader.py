"""
Safe cv2 loader for PyInstaller environment
Handles recursion detection and provides fallback behavior
"""

import sys
import os

# Module-level cache
_cv2_module = None
_cv2_available = None
_load_attempted = False


def get_cv2():
    """
    Safely get cv2 module, handling PyInstaller recursion issues.

    Returns:
        cv2 module if available, None otherwise

    This function uses multiple strategies to load cv2:
    1. Try direct import (works in dev environment)
    2. Try importing from cached sys.modules (if already loaded)
    3. Try lazy import with error handling
    4. Return None if all attempts fail
    """
    global _cv2_module, _cv2_available, _load_attempted

    # Return cached result if available
    if _load_attempted:
        return _cv2_module

    _load_attempted = True
    _cv2_available = False

    # Check if running in PyInstaller bundle
    # cv2 is known to have recursion issues in PyInstaller
    # However, we've fixed this with proper spec file configuration and runtime hooks
    if hasattr(sys, '_MEIPASS'):
        print("[cv2_loader] Running in PyInstaller bundle - attempting to load cv2...")
        print("[cv2_loader] If this fails, recording feature will be disabled")
        # Don't return None immediately - let's try to load it
        # The runtime hook and spec file should handle the recursion issue

    # Strategy 1: Check if cv2 is already in sys.modules
    if 'cv2' in sys.modules:
        _cv2_module = sys.modules['cv2']
        _cv2_available = True
        print("[cv2_loader] Using cached cv2 from sys.modules")
        return _cv2_module

    # Strategy 2: Try direct import (dev environment only)
    try:
        import cv2
        _cv2_module = cv2
        _cv2_available = True

        # Verify it actually works by testing a basic function
        import numpy as np
        test_array = np.zeros((10, 10, 3), dtype=np.uint8)
        _ = cv2.cvtColor(test_array, cv2.COLOR_RGB2BGR)

        print(f"[cv2_loader] ✓ cv2 loaded successfully (version: {cv2.__version__})")
        return _cv2_module

    except ImportError as e:
        error_msg = str(e)
        if 'recursion' in error_msg.lower():
            print("[cv2_loader] ✗ PyInstaller recursion detected")
            print("[cv2_loader] This is a known issue with cv2 in PyInstaller bundles")
            print("[cv2_loader] Recording feature will be disabled")
        else:
            print(f"[cv2_loader] ✗ Import error: {e}")
        _cv2_module = None
        _cv2_available = False
        return None

    except Exception as e:
        print(f"[cv2_loader] ✗ Unexpected error: {e}")
        _cv2_module = None
        _cv2_available = False
        return None


def is_cv2_available():
    """
    Check if cv2 is available without importing it.

    Returns:
        bool: True if cv2 is available, False otherwise
    """
    global _cv2_available

    # Check cache first
    if _cv2_available is not None:
        return _cv2_available

    # Try to load cv2
    cv2 = get_cv2()
    return cv2 is not None


def test_cv2_functionality():
    """
    Test if cv2 actually works (can process images).

    Returns:
        bool: True if cv2 works, False otherwise
    """
    cv2 = get_cv2()
    if cv2 is None:
        return False

    try:
        import numpy as np
        # Test basic operations
        test_array = np.zeros((100, 100, 3), dtype=np.uint8)
        result = cv2.cvtColor(test_array, cv2.COLOR_RGB2BGR)

        # Test VideoWriter
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_path = temp_file.name
        temp_file.close()

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(temp_path, fourcc, 30.0, (100, 100))

        if writer.isOpened():
            writer.write(test_array)
            writer.release()
            os.unlink(temp_path)
            return True
        else:
            return False

    except Exception as e:
        print(f"[cv2_loader] ✗ Functionality test failed: {e}")
        return False


# Export convenience functions
__all__ = ['get_cv2', 'is_cv2_available', 'test_cv2_functionality']
