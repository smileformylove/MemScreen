#!/usr/bin/env python3
"""
Diagnose MemScreen installation and dependencies
"""

import sys
from pathlib import Path

print("=" * 70)
print("🔍 MemScreen Installation Diagnostic")
print("=" * 70)
print()

# Python info
print("📍 Python Information:")
print(f"   Executable: {sys.executable}")
print(f"   Version: {sys.version}")
print(f"   Path: {sys.path[:3]}")
print()

# Check dependencies
print("📦 Checking Dependencies...")
dependencies = [
    "pydantic",
    "tkinter",
    "ttkthemes",
    "PIL",
    "cv2",
    "numpy",
    "ollama",
    "chromadb",
]

missing = []
for dep in dependencies:
    try:
        if dep == "tkinter":
            import tkinter
        elif dep == "PIL":
            from PIL import Image
        elif dep == "cv2":
            import cv2
        else:
            __import__(dep)
        print(f"   ✅ {dep}")
    except ImportError as e:
        print(f"   ❌ {dep} - {e}")
        missing.append(dep)

print()

# Check memscreen package
print("📦 Checking MemScreen Package...")
try:
    import memscreen
    print(f"   ✅ memscreen imported")
    print(f"   Location: {Path(memscreen.__file__).parent}")
except ImportError as e:
    print(f"   ❌ memscreen - {e}")
    missing.append("memscreen")

print()

# Check if memscreen.ui can be imported
print("🖼️  Checking memscreen.ui...")
try:
    from memscreen.ui import MemScreenApp
    print(f"   ✅ memscreen.ui.MemScreenApp")
except ImportError as e:
    print(f"   ❌ memscreen.ui - {e}")

print()

# Check if unified_ui can be imported
print("🔄 Checking unified_ui...")
try:
    from memscreen.unified_ui import main
    print(f"   ✅ unified_ui.main")
except ImportError as e:
    print(f"   ❌ unified_ui - {e}")
    print(f"   Error details: {type(e).__name__}")

print()

# Summary
print("=" * 70)
if missing:
    print("⚠️  Missing Dependencies:")
    for dep in missing:
        print(f"   - {dep}")
    print()
    print("Install with:")
    print("   pip3 install -e .")
else:
    print("✅ All dependencies installed!")
print("=" * 70)
