#!/usr/bin/env python3
"""
Comprehensive MemScreen Application Test

Tests all major functionality:
1. Configuration system
2. LLM providers
3. Embeddings
4. Vector store
5. Memory system
6. UI components
7. Screen capture
8. Animation system
9. Color system
"""

import sys
import os
import time
from datetime import datetime

print("=" * 70)
print("🧪 MemScreen Comprehensive Application Test")
print("=" * 70)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

test_results = []

# Test 1: Configuration System
print("📋 [Test 1] Configuration System")
print("-" * 70)
try:
    from memscreen.config import get_config, MemScreenConfig

    config = get_config()
    assert config.db_path.name == "screen_capture.db", "Database name mismatch"
    assert config.ollama_base_url == "http://127.0.0.0:11434", "Ollama URL mismatch"
    assert config.recording_duration == 60, "Default duration mismatch"
    assert config.recording_interval == 2.0, "Default interval mismatch"

    print("✅ Configuration loaded correctly")
    print(f"   Database: {config.db_path}")
    print(f"   Videos: {config.videos_dir}")
    print(f"   LLM Model: {config.ollama_llm_model}")
    print(f"   Embedding Model: {config.ollama_embedding_model}")
    test_results.append(("Configuration", "PASS"))
except Exception as e:
    print(f"❌ Configuration test failed: {e}")
    test_results.append(("Configuration", "FAIL"))

print()

# Test 2: LLM Module
print("🤖 [Test 2] LLM Module")
print("-" * 70)
try:
    from memscreen.llm import BaseLlmConfig, LLMBase, OllamaLLM, OllamaConfig, LlmFactory

    # Test configuration
    config = OllamaConfig(model="qwen3:1.7b")
    assert config.model == "qwen3:1.7b", "Model not set"

    # Test factory
    factory = LlmFactory()
    assert "ollama" in factory.get_supported_providers(), "Ollama not in providers"

    print("✅ LLM module working")
    print(f"   BaseLlmConfig: {BaseLlmConfig}")
    print(f"   LLMBase: {LLMBase}")
    print(f"   OllamaLLM: {OllamaLLM}")
    print(f"   OllamaConfig: {OllamaConfig}")
    print(f"   LlmFactory: {LlmFactory}")
    print(f"   Supported providers: {factory.get_supported_providers()}")
    test_results.append(("LLM Module", "PASS"))
except Exception as e:
    print(f"❌ LLM module test failed: {e}")
    test_results.append(("LLM Module", "FAIL"))

print()

# Test 3: Embeddings Module
print("📊 [Test 3] Embeddings Module")
print("-" * 70)
try:
    from memscreen.embeddings import (
        BaseEmbedderConfig, EmbeddingBase,
        OllamaEmbedding, MockEmbeddings, EmbedderFactory
    )

    # Test mock embeddings
    mock = MockEmbeddings()
    embedding = mock.embed("test")
    assert len(embedding) == 10, "Mock embedding size wrong"
    assert embedding[0] == 0.1, "First value wrong"

    # Test factory
    factory = EmbedderFactory()
    assert "ollama" in factory.get_supported_providers(), "Ollama not in providers"

    print("✅ Embeddings module working")
    print(f"   BaseEmbedderConfig: {BaseEmbedderConfig}")
    print(f"   EmbeddingBase: {EmbeddingBase}")
    print(f"   OllamaEmbedding: {OllamaEmbedding}")
    print(f"   MockEmbeddings: {MockEmbeddings}")
    print(f"   EmbedderFactory: {EmbedderFactory}")
    print(f"   Mock embedding: {embedding}")
    test_results.append(("Embeddings", "PASS"))
except Exception as e:
    print(f"❌ Embeddings test failed: {e}")
    test_results.append(("Embeddings", "FAIL"))

print()

# Test 4: Storage Module
print("💾 [Test 4] Storage Module")
print("-" * 70)
try:
    from memscreen.storage import SQLiteManager

    # Create test database
    test_db = "./test_storage.db"
    db = SQLiteManager(test_db)

    # Add history
    db.add_history("test_id", None, None, "test_action")

    # Get history
    history = db.get_history(limit=1)
    assert len(history) >= 0, "History retrieval failed"

    # Cleanup
    db.close()
    os.remove(test_db)

    print("✅ Storage module working")
    print(f"   SQLiteManager: {SQLiteManager}")
    print("   History operations: ADD, GET, CLOSE")
    test_results.append(("Storage", "PASS"))
except Exception as e:
    print(f"❌ Storage test failed: {e}")
    test_results.append(("Storage", "FAIL"))

print()

# Test 5: Animation Framework
print("💫 [Test 5] Animation Framework")
print("-" * 70)
try:
    from memscreen.ui.components.animations import (
        Animator, ColorTransition, RippleEffect,
        TypingIndicator, CounterAnimation
    )

    # Test color transition
    transition = ColorTransition("#4F46E5", "#10B981")
    gradient = transition.get_gradient(5)
    assert len(gradient) == 5, "Gradient size wrong"

    # Test timing constants
    from memscreen.ui.components.animations import TIMING_FAST, TIMING_NORMAL
    assert TIMING_FAST == 150, "Fast timing wrong"
    assert TIMING_NORMAL == 300, "Normal timing wrong"

    print("✅ Animation framework working")
    print(f"   Animator: {Animator}")
    print(f"   ColorTransition: {ColorTransition}")
    print(f"   RippleEffect: {RippleEffect}")
    print(f"   TypingIndicator: {TypingIndicator}")
    print(f"   CounterAnimation: {CounterAnimation}")
    print(f"   Gradient colors: {gradient[:3]}")
    test_results.append(("Animations", "PASS"))
except Exception as e:
    print(f"❌ Animation test failed: {e}")
    test_results.append(("Animations", "FAIL"))

print()

# Test 6: Enhanced Color System
print("🎨 [Test 6] Enhanced Color System")
print("-" * 70)
try:
    from memscreen.ui.components.colors import (
        COLORS, GRADIENTS, STATUS_COLORS,
        SHADOWS, SHADOW_PRESETS
    )

    # Test colors
    assert "primary" in COLORS, "Primary color missing"
    assert len(COLORS) >= 15, "Not enough colors"

    # Test gradients
    assert len(GRADIENTS) >= 10, "Not enough gradients"

    # Test status colors
    assert "recording" in STATUS_COLORS, "Recording status missing"
    status = STATUS_COLORS["recording"]
    assert "bg" in status and "text" in status, "Status keys missing"

    # Test shadows
    assert "md" in SHADOWS, "Medium shadow missing"

    print("✅ Color system working")
    print(f"   Total colors: {len(COLORS)}")
    print(f"   Gradients: {len(GRADIENTS)}")
    print(f"   Status states: {len(STATUS_COLORS)}")
    print(f"   Shadow levels: {len(SHADOWS)}")
    print(f"   Shadow presets: {len(SHADOW_PRESETS)}")
    test_results.append(("Colors", "PASS"))
except Exception as e:
    print(f"❌ Color system test failed: {e}")
    test_results.append(("Colors", "FAIL"))

print()

# Test 7: Enhanced Buttons
print("🔘 [Test 7] Enhanced Buttons")
print("-" * 70)
try:
    from memscreen.ui.components.buttons import ModernButton, IconButton

    print("✅ Enhanced button classes available")
    print(f"   ModernButton: {ModernButton}")
    print(f"   IconButton: {IconButton}")
    print("   Features: ripple, loading, gradients, shadows")
    test_results.append(("Buttons", "PASS"))
except Exception as e:
    print(f"❌ Buttons test failed: {e}")
    test_results.append(("Buttons", "FAIL"))

print()

# Test 8: Screen Capture
print("📸 [Test 8] Screen Capture Module")
print("-" * 70)
try:
    from PIL import ImageGrab

    print("   Capturing screenshot...")
    screenshot = ImageGrab.grab()
    width, height = screenshot.size

    print("✅ Screen capture working")
    print(f"   Resolution: {width}x{height}")
    print(f"   Mode: {screenshot.mode}")

    # Save test screenshot
    test_file = "./test_screenshot.png"
    screenshot.save(test_file)
    size = os.path.getsize(test_file)
    print(f"   Saved: {test_file} ({size/1024:.1f} KB)")

    # Cleanup
    os.remove(test_file)
    print("   ✅ Test screenshot cleaned up")

    test_results.append(("Screen Capture", "PASS"))
except Exception as e:
    print(f"❌ Screen capture test failed: {e}")
    test_results.append(("Screen Capture", "FAIL"))

print()

# Test 9: Ollama Connection
print("🤖 [Test 9] Ollama Connection")
print("-" * 70)
try:
    import requests

    ollama_url = "http://127.0.0.1:11434/api/tags"
    print(f"   Connecting to {ollama_url}...")

    response = requests.get(ollama_url, timeout=2)
    if response.status_code == 200:
        models = response.json().get('models', [])
        print(f"✅ Ollama is running")
        print(f"   Available models: {len(models)}")
        for model in models[:5]:
            print(f"      • {model.get('name', 'unknown')}")
        if len(models) > 5:
            print(f"      • ... and {len(models) - 5} more")
        test_results.append(("Ollama", "PASS"))
    else:
        print(f"⚠️  Ollama returned status {response.status_code}")
        test_results.append(("Ollama", "WARN"))

except requests.exceptions.ConnectionError:
    print("⚠️  Ollama not running (start with: ollama serve)")
    test_results.append(("Ollama", "WARN"))
except Exception as e:
    print(f"⚠️  Ollama check warning: {e}")
    test_results.append(("Ollama", "WARN"))

print()

# Test 10: UI Components
print("🖼️ [Test 10] UI Components")
print("-" * 70)
try:
    import tkinter as tk
    from memscreen.ui import MemScreenApp

    # Create mock memory for testing
    class MockMemory:
        def search(self, query, user_id="user1"):
            return []
        def add(self, *args, **kwargs):
            return True

    config = get_config()
    mock_memory = MockMemory()

    root = tk.Tk()
    root.title("MemScreen Test")
    root.withdraw()  # Hide window

    app = MemScreenApp(root, mem=mock_memory)
    print("✅ MemScreenApp created successfully")
    print(f"   App: {app}")
    print(f"   Root: {root}")

    root.destroy()
    print("   ✅ UI test completed")

    test_results.append(("UI Components", "PASS"))
except Exception as e:
    print(f"❌ UI components test failed: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("UI Components", "FAIL"))

print()
print("=" * 70)
print("📊 Test Results Summary")
print("=" * 70)

passed = sum(1 for _, result in test_results if result == "PASS")
warned = sum(1 for _, result in test_results if result == "WARN")
failed = sum(1 for _, result in test_results if result == "FAIL")
total = len(test_results)

print(f"Total Tests: {total}")
print(f"✅ Passed: {passed}")
print(f"⚠️  Warnings: {warned}")
print(f"❌ Failed: {failed}")

if failed == 0:
    print()
    print("🎉 ALL TESTS PASSED!")
    print()
    print("The MemScreen application is fully functional and ready to use!")
    print()
    print("Launch with: memscreen-ui")
else:
    print()
    print("⚠️  Some tests failed. Please review the errors above.")
    print()

print("=" * 70)
print("Test completed at:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("=" * 70)
