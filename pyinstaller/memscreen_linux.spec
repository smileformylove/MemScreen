# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MemScreen on Linux
Creates a standalone application with all dependencies included.
"""

import os
import sys

block_cipher = None

# Get project root directory
spec_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
project_root = os.path.dirname(spec_dir)

print(f"Spec directory: {spec_dir}")
print(f"Project root: {project_root}")

# Verify project root
if not os.path.exists(os.path.join(project_root, 'start.py')):
    raise FileNotFoundError(f"start.py not found in project root: {project_root}")

# Collect all data files and directories (use absolute paths)
datas = [
    (os.path.join(project_root, 'assets'), 'assets'),
    (os.path.join(project_root, 'memscreen'), 'memscreen'),
]

# Collect hidden imports (Kivy and its dependencies)
hiddenimports = [
    'kivy',
    'kivy.core',
    'kivy.core.window',
    'kivy.core.audio',
    'kivy.core.video',
    'kivy.core.text',
    'kivy.core.image',
    'kivy.core.spelling',
    'kivy.input',
    'kivy.input.providers',
    'kivy.uix',
    'kivy.graphics',
    'PIL',
    'PIL._tkinter_finder',
    'cv2',
    'numpy',
    'torch',
    'ollama',
    'chromadb',
    'chromadb.api',
    'chromadb.api.rust',
    'chromadb.telemetry',
    'chromadb.telemetry.product',
    'chromadb.telemetry.product.posthog',
    'sentence_transformers',
    'openai',
    'pydantic',
    'yaml',
    'pyscreenshot',
    'sounddevice',
    'soundfile',
    'wave',
]

# Exclude unnecessary modules
excludes = [
    'pytest',
    'black',
    'flake8',
    'mypy',
    'tkinter',
    'matplotlib',
    'pandas',
    'scipy',
    # Exclude cv2's SDL2 to avoid conflict with kivy's SDL2
    'cv2.cuda',
    'cv2.cv2',
    'cv2.gapi',
]

# Exclude cv2's SDL2 binaries to avoid conflict with Kivy's SDL2
binaries_excludes = [
    'libSDL2',
    'SDL2',
]

a = Analysis(
    [os.path.join(project_root, 'start.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[os.path.join(spec_dir, 'hooks')],
    hooksconfig={},
    runtime_hooks=[
        os.path.join(spec_dir, 'rthook/pyi_rthook_chromadb.py'),
        os.path.join(spec_dir, 'rthook/pyi_rthook_disable_telemetry.py'),
        os.path.join(spec_dir, 'rthook/pyi_rthook_kivy.py'),
    ],
    excludes=excludes,
    binaries_excludes=binaries_excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MemScreen',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application - no console window
    disable_windowedtraceback=False,
    argv_emulation=False,
    target_arch=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    [],
    [],
    strip=False,
    upx=True,
    name='MemScreen',
)
