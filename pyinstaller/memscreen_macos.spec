# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MemScreen on macOS
Creates a standalone .app bundle with all dependencies included.
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
]

a = Analysis(
    [os.path.join(project_root, 'start.py')],
    pathex=[project_root],
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
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'assets/logo.icns') if os.path.exists(os.path.join(project_root, 'assets/logo.icns')) else None,
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

# Create .app bundle structure
app = BUNDLE(
    exe,
    coll,
    name='MemScreen.app',
    icon=os.path.join(project_root, 'assets/logo.icns') if os.path.exists(os.path.join(project_root, 'assets/logo.icns')) else None,
    bundle_identifier='com.smileformylove.MemScreen',
    info_plist={
        'CFBundleName': 'MemScreen',
        'CFBundleDisplayName': 'MemScreen',
        'CFBundleVersion': '0.5.0',
        'CFBundleShortVersionString': '0.5.0',
        'CFBundleIdentifier': 'com.smileformylove.MemScreen',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'NSMicrophoneUsageDescription': 'MemScreen needs microphone access for audio recording.',
        'NSCameraUsageDescription': 'MemScreen needs camera access for video recording.',
    },
)
