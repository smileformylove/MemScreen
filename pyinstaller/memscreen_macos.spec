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

# Collect cv2 configuration files and data
import sys
from pathlib import Path
cv2_package = None
for site_path in sys.path:
    potential_cv2 = os.path.join(site_path, 'cv2')
    if os.path.exists(potential_cv2) and os.path.isfile(os.path.join(potential_cv2, '__init__.py')):
        cv2_package = potential_cv2
        break

if cv2_package:
    # Add cv2 config files
    cv2_datas = []
    for item in ['config.py', 'version.py', 'load_config_py3.py', 'config-3.py']:
        item_path = os.path.join(cv2_package, item)
        if os.path.exists(item_path):
            cv2_datas.append((item_path, 'cv2'))

    # Add cv2 data directory
    cv2_data_dir = os.path.join(cv2_package, 'data')
    if os.path.exists(cv2_data_dir):
        cv2_datas.append((cv2_data_dir, 'cv2/data'))

    datas.extend(cv2_datas)
    print(f"Adding cv2 config files: {len(cv2_datas)} files")

# Collect cv2's SDL2 library from .dylibs directory
import sys
from pathlib import Path
cv2_dylibs = None
sdl2_lib_path = None

# Try multiple methods to find cv2's SDL2
# Method 1: Search in sys.path
for site_path in sys.path:
    potential_path = os.path.join(site_path, 'cv2', '.dylibs', 'libSDL2-2.0.0.dylib')
    if os.path.exists(potential_path):
        sdl2_lib_path = potential_path
        cv2_dylibs = os.path.join(site_path, 'cv2', '.dylibs')
        print(f"Found SDL2 via sys.path: {sdl2_lib_path}")
        break

# Method 2: Use importlib to find cv2 package location
if not sdl2_lib_path:
    try:
        import importlib.util
        cv2_spec = importlib.util.find_spec('cv2')
        if cv2_spec and cv2_spec.origin:
            cv2_package_dir = os.path.dirname(cv2_spec.origin)
            sdl2_lib_path = os.path.join(cv2_package_dir, '.dylibs', 'libSDL2-2.0.0.dylib')
            if os.path.exists(sdl2_lib_path):
                cv2_dylibs = os.path.join(cv2_package_dir, '.dylibs')
                print(f"Found SDL2 via importlib: {sdl2_lib_path}")
    except:
        pass

binaries = []
if sdl2_lib_path and os.path.exists(sdl2_lib_path):
    binaries.append((sdl2_lib_path, 'cv2/.dylibs'))
    print(f"✓ Adding cv2's SDL2 library: {sdl2_lib_path}")
else:
    print("⚠ Warning: SDL2 library not found - recording feature may not work in packaged app")
    print("  The app will need manual SDL2 copying after build")

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
    'pynput',
    'pynput.keyboard',
    'pynput.keyboard._darwin',
    'pynput.mouse',
    'pynput.mouse._darwin',
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
    'cv2.cuda',
    'cv2.gapi',
    'cv2.typing',  # Exclude problematic cv2.typing module
    'cv2.mat_wrapper',  # Exclude problematic cv2.mat_wrapper
]

a = Analysis(
    [os.path.join(project_root, 'start.py')],
    pathex=[project_root],
    binaries=binaries,  # Include binaries with cv2's SDL2
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[os.path.join(spec_dir, 'hooks')],
    hooksconfig={},
    runtime_hooks=[
        os.path.join(spec_dir, 'rthook/pyi_rthook_chromadb.py'),
        os.path.join(spec_dir, 'rthook/pyi_rthook_disable_telemetry.py'),
        os.path.join(spec_dir, 'rthook/pyi_rthook_kivy.py'),
        os.path.join(spec_dir, 'rthook/pyi_rthook_cv2.py'),  # Add cv2 runtime hook
    ],
    excludes=excludes,
    # Exclude problematic cv2 modules to avoid recursion
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
        'NSAppleMusicUsageDescription': 'MemScreen needs access to your screen to provide AI-powered visual memory.',
        'LSBackgroundOnly': False,  # Run as foreground app, not background
        'LSUIElement': False,  # Show in dock and allow focus
        'NSSupportsAutomaticTermination': False,  # Prevent auto-termination
    },
)
