# -*- mode: python ; coding: utf-8 -*-
"""
MemScreen PyInstaller Spec File
Cross-platform packaging configuration for Windows, macOS, and Linux
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the current directory
block_cipher = None
base_dir = os.path.dirname(os.path.abspath(SPEC))

# App metadata
app_name = 'MemScreen'
app_version = '0.4.0'
app_author = 'Jixiang Luo'
app_description = 'Ask Screen Anything - Your AI-Powered Visual Memory System'

# Collect data files from packages
datas = []
datas += collect_data_files('memscreen', include_py_files=False)

# Add config files
if os.path.exists('config_example.yaml'):
    datas.append(('config_example.yaml', '.'))

# Add documentation files
doc_files = ['README.md', 'GRAPH_MEMORY_GUIDE.md', 'PROCESS_MINING_GUIDE.md']
for doc in doc_files:
    if os.path.exists(doc):
        datas.append((doc, '.'))

# Collect hidden imports
hiddenimports = [
    'memscreen',
    'memscreen.memory',
    'memscreen.llm',
    'memscreen.embeddings',
    'memscreen.vector_store',
    'memscreen.storage',
    'memscreen.ui',
    'memscreen.skills',
    'memscreen.agent',
    'memscreen.presenters',
    'memscreen.utils',
    'kivy',
    'kivy.core',
    'kivy.core.window',
    'kivy.uix',
    'kivy.uix.boxlayout',
    'kivy.uix.button',
    'kivy.uix.label',
    'kivy.uix.scrollview',
    'kivy.uix.textinput',
    'kivy.uix.popup',
    'kivy.uix.gridlayout',
    'kivy.graphics',
    'kivy.lang',
    'kivy.properties',
    'kivy.clock',
    'PIL',
    'PIL.Image',
    'cv2',
    'torch',
    'torchvision',
    'chromadb',
    'ollama',
    'easyocr',
    'pynput',
    'mss',
    'matplotlib',
    'matplotlib.pyplot',
    'pydantic',
    'toolz',
    'pytz',
]

# Collect all submodules
hiddenimports += collect_submodules('memscreen')
hiddenimports += collect_submodules('kivy')

# Binary exclusions (to reduce size)
excludes = [
    'tkinter',
    'test',
    'tests',
    'unittest',
    'IPython',
    'jupyter',
    'notebook',
]

a = Analysis(
    ['start.py'],
    pathex=[base_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed app (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file if available: 'assets/icon.ico' for Windows
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)

# Platform-specific configurations
if sys.platform == 'darwin':
    # macOS: Create .app bundle
    app = BUNDLE(
        coll,
        name=f'{app_name}.app',
        icon=None,  # Add icon: 'assets/icon.icns' for macOS
        bundle_identifier='com.memscreen.app',
        info_plist={
            'CFBundleName': app_name,
            'CFBundleDisplayName': app_name,
            'CFBundleVersion': app_version,
            'CFBundleShortVersionString': app_version,
            'CFBundlePackageType': 'APPL',
            'CFBundleSignature': '????',
            'CFBundleExecutable': app_name,
            'CFBundleIdentifier': 'com.memscreen.app',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.15',
            'NSRequiresAquaSystemAppearance': False,
            'CFBundleGetInfoString': f'{app_description} v{app_version}',
            'CFBundleAuthor': app_author,
            'NSHumanReadableCopyright': f'Copyright © 2024 {app_author}',
        },
    )
elif sys.platform == 'win32':
    # Windows: No special bundle needed
    pass
elif sys.platform.startswith('linux'):
    # Linux: No special bundle needed
    pass
