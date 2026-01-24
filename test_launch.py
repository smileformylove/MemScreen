#!/usr/bin/env python3
"""
Quick launch test for MemScreen UI

This script tests that the application can be initialized
and all components are loaded correctly.
"""

import sys
from datetime import datetime

print("=" * 70)
print("🚀 MemScreen Launch Test")
print("=" * 70)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

test_results = []

# Test 1: Import modules
print("📦 [Test 1] Import Modules")
print("-" * 70)
try:
    from memscreen.config import get_config
    from memscreen.memory import Memory
    from memscreen.ui import MemScreenApp
    import tkinter as tk

    print("✅ All modules imported successfully")
    test_results.append(("Imports", "PASS"))
except Exception as e:
    print(f"❌ Import failed: {e}")
    test_results.append(("Imports", "FAIL"))
    sys.exit(1)

print()

# Test 2: Load configuration
print("⚙️  [Test 2] Load Configuration")
print("-" * 70)
try:
    config = get_config()
    print(f"✅ Configuration loaded")
    print(f"   Database: {config.db_path}")
    print(f"   LLM Model: {config.ollama_llm_model}")
    print(f"   Embedding Model: {config.ollama_embedding_model}")
    test_results.append(("Configuration", "PASS"))
except Exception as e:
    print(f"❌ Configuration failed: {e}")
    test_results.append(("Configuration", "FAIL"))
    sys.exit(1)

print()

# Test 3: Initialize Memory
print("🧠 [Test 3] Initialize Memory")
print("-" * 70)
try:
    llm_config = config.get_llm_config()
    memory = Memory.from_config(llm_config)
    print(f"✅ Memory initialized successfully")
    print(f"   Type: {type(memory).__name__}")
    test_results.append(("Memory", "PASS"))
except Exception as e:
    print(f"❌ Memory initialization failed: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("Memory", "FAIL"))
    sys.exit(1)

print()

# Test 4: Initialize UI
print("🖼️  [Test 4] Initialize UI")
print("-" * 70)
try:
    root = tk.Tk()
    root.title("MemScreen Launch Test")
    app = MemScreenApp(root, mem=memory)

    print(f"✅ UI initialized successfully")
    print(f"   App: {type(app).__name__}")
    print(f"   Tabs: Recording, Chat, Video, Search, Settings")

    # Clean up
    root.destroy()

    test_results.append(("UI", "PASS"))
except Exception as e:
    print(f"❌ UI initialization failed: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("UI", "FAIL"))
    sys.exit(1)

print()
print("=" * 70)
print("📊 Test Results Summary")
print("=" * 70)

passed = sum(1 for _, result in test_results if result == "PASS")
total = len(test_results)

print(f"Total Tests: {total}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {total - passed}")

if passed == total:
    print()
    print("🎉 ALL TESTS PASSED!")
    print()
    print("The MemScreen application is ready to launch!")
    print()
    print("Start the application with:")
    print("  memscreen-ui")
    print()
    print("Or directly with Python:")
    print("  python3 -m memscreen.ui")
    print()
else:
    print()
    print("⚠️  Some tests failed.")
    print()

print("=" * 70)
print("Test completed at:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("=" * 70)
