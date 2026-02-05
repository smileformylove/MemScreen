"""
PyInstaller hook for cv2 (OpenCV)

This hook excludes cv2's SDL2 libraries to avoid conflicts with Kivy's SDL2.
When both Kivy and OpenCV are used, their SDL2 libraries conflict and cause
the application to become unresponsive on macOS.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from PyInstaller.utils.hooks import remove_prefix

# Collect OpenCV data files but exclude SDL2
all_datas = collect_data_files('cv2', include_py_files=False)

# Filter out SDL2-related data files
datas = [(src, dest) for src, dest in all_datas if 'SDL2' not in src]

# Collect OpenCV submodules
hiddenimports = collect_submodules('cv2')

# Excluded imports
excludedimports = ['cv2.cuda', 'cv2.gapi']
