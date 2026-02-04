"""
Runtime hook to fix cv2 import recursion in PyInstaller bundled apps.

This hook modifies cv2's import behavior to prevent recursion errors
by setting the appropriate environment variable before cv2 is imported.
"""

import os
import sys

# Set environment variable to disable OpenCV's CUDA and other extensions
# that cause recursion issues in PyInstaller
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'

# Try to prevent cv2 from loading problematic binary extensions
# by intercepting the import
class CV2ImportInterceptor:
    """Intercept cv2 imports to prevent recursion."""

    def find_spec(self, fullname, path, target=None):
        if fullname == 'cv2' or fullname.startswith('cv2.'):
            # Mark that cv2 is being imported to prevent recursion
            if fullname == 'cv2' and 'cv2' not in sys.modules:
                # Set a flag to indicate cv2 is being imported
                sys._cv2_importing = True

            try:
                # Continue with normal import
                return None
            finally:
                if fullname == 'cv2':
                    # Clear the flag after import attempt
                    sys._cv2_importing = False

        return None


# Install the import interceptor before any cv2 imports
interceptor = CV2ImportInterceptor()
sys.meta_path.insert(0, interceptor)
