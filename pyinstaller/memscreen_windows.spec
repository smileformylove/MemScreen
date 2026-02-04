# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MemScreen on Windows
Creates a standalone executable with all dependencies included.
"""

import os
import sys

block_cipher = None

# Collect all data files and directories
datas = [
    ('assets', 'assets'),
    ('memscreen', 'memscreen'),
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
    'sentence_transformers',
    'openai',
    'pydantic',
    'yaml',
    'pyscreenshot',
    'sounddevice',
    'soundfile',
    'wave',
    'win32com',
    'win32gui',
    'win32con',
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
]

a = Analysis(
    ['start.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MemScreen',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application - no console window
    disable_windowedtraceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo.ico' if os.path.exists('assets/logo.ico') else None,
)
