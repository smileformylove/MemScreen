"""
Runtime hook for cv2 (OpenCV) in PyInstaller
Fixes recursion and config file issues
"""

import os
import sys

# This hook MUST run before cv2 is imported
if hasattr(sys, '_MEIPASS'):
    # Running in PyInstaller bundle
    meipass = sys._MEIPASS

    # CRITICAL: Add cv2 to path BEFORE any imports
    cv2_path = os.path.join(meipass, 'cv2')
    if cv2_path not in sys.path:
        sys.path.insert(0, cv2_path)

    # Set environment variables to prevent cv2 from searching system paths
    # which can cause recursion in PyInstaller environment
    os.environ['OPENCV_IO_ENABLE_GEOS'] = 'FALSE'

    # Prevent cv2 from loading Qt which causes recursion
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''

    # Pre-load numpy to ensure it's available before cv2
    try:
        import numpy
        import numpy.core.multiarray
    except ImportError:
        pass

    # DON'T try to pre-import cv2 here - it causes module structure issues
    # The cv2_loader module will handle cv2 loading safely when needed

print("[Runtime Hook] cv2 runtime configuration complete")
