#!/usr/bin/env python3
"""
Quick Diagnostics and Fixes for MemScreen

Identifies and fixes common issues with local model limitations.
"""

import sys
import os
import subprocess
import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))


def print_header(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def check_ollama():
    """Check if Ollama is running and configured correctly"""
    print_header("1. Checking Ollama")

    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)

        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            model_names = [m.get("name", "") for m in models]

            print("✅ Ollama is running")
            print(f"   Available models: {len(model_names)}")

            # Check for required models
            has_vision = any("qwen2.5vl" in name or "llava" in name for name in model_names)
            has_embedder = any("nomic-embed" in name or "mxbai-embed" in name for name in model_names)

            if has_vision:
                print("✅ Vision model found")
            else:
                print("❌ Vision model missing")
                print("   Fix: ollama pull qwen2.5vl:3b")

            if has_embedder:
                print("✅ Embedder model found")
            else:
                print("❌ Embedder model missing")
                print("   Fix: ollama pull nomic-embed-text")

            return True, has_vision and has_embedder
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False, False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama")
        print("   Fix: Start Ollama with 'ollama serve'")
        return False, False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, False


def check_model_performance():
    """Test model response time and quality"""
    print_header("2. Testing Model Performance")

    try:
        import time

        prompt = "Say 'Hello' in one word."

        start = time.time()
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "qwen2.5vl:3b",
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 10}
            },
            timeout=30
        )
        elapsed = time.time() - start

        if response.status_code == 200:
            data = response.json()
            text = data.get("response", "").strip()

            print(f"✅ Model responded in {elapsed:.1f}s")
            print(f"   Response: {text}")

            if elapsed > 20:
                print("⚠️  Response is slow (>20s)")
                print("   Consider: Using a smaller model or faster hardware")
            elif elapsed < 5:
                print("✅ Response is fast (<5s)")
            else:
                print("✅ Response time is normal (5-20s)")

            return True
        else:
            print(f"❌ Model error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_token_limits():
    """Test if model handles longer prompts correctly"""
    print_header("3. Testing Token Limits")

    try:
        import time

        # Test with increasing prompt lengths
        test_cases = [
            ("Short (10 words)", "Summarize this in one sentence: AI is helpful technology."),
            ("Medium (50 words)", "Summarize this: " + "AI is " * 25 + "helpful technology for everyone."),
            ("Long (200 words)", "Summarize this: " + "AI transforms technology and society. " * 20),
        ]

        results = []

        for name, prompt in test_cases:
            start = time.time()
            response = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": "qwen2.5vl:3b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 50, "temperature": 0.6}
                },
                timeout=60
            )
            elapsed = time.time() - start

            if response.status_code == 200:
                data = response.json()
                text = data.get("response", "")
                print(f"✅ {name}: {elapsed:.1f}s, {len(text)} chars")
                results.append(True)
            else:
                print(f"❌ {name}: Failed")
                results.append(False)

        if all(results):
            print("✅ All token limits passed")
            return True
        else:
            print("⚠️  Some token limits failed")
            print("   Consider: Keeping prompts under 200 words for reliability")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_json_handling():
    """Test if model can generate valid JSON"""
    print_header("4. Testing JSON Generation")

    try:
        import json
        import time

        prompt = """Respond with valid JSON only:
{"status": "ok", "message": "test"}"""

        start = time.time()
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "qwen2.5vl:3b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 100}
            },
            timeout=30
        )
        elapsed = time.time() - start

        if response.status_code == 200:
            data = response.json()
            text = data.get("response", "").strip()

            print(f"   Model response: {text[:100]}...")

            # Try to parse
            try:
                parsed = json.loads(text)
                print(f"✅ Valid JSON generated in {elapsed:.1f}s")
                print(f"   Parsed: {parsed}")
                return True
            except json.JSONDecodeError:
                print("⚠️  Invalid JSON (common with small models)")
                print("   Recommendation: Use text-based formats instead of JSON")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_vision_capability():
    """Test vision model with a simple screenshot"""
    print_header("5. Testing Vision Model")

    try:
        from PIL import ImageGrab
        import base64
        import time

        # Capture screen
        print("   Capturing screen...")
        screenshot = ImageGrab.grab()

        # Encode
        import io
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Test vision
        prompt = "What do you see in this image? Answer in one sentence."

        start = time.time()
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "qwen2.5vl:3b",
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
                "options": {"num_predict": 100, "temperature": 0.6}
            },
            timeout=90
        )
        elapsed = time.time() - start

        if response.status_code == 200:
            data = response.json()
            text = data.get("response", "").strip()

            if text:
                print(f"✅ Vision model works ({elapsed:.1f}s)")
                print(f"   Analysis: {text[:100]}...")
                return True
            else:
                print("⚠️  Vision model returned empty response")
                return False
        else:
            print(f"❌ Vision model error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def provide_recommendations(ollama_ok, models_ok):
    """Provide specific recommendations based on test results"""
    print_header("Recommendations")

    if not ollama_ok:
        print("\n🔧 CRITICAL: Fix Ollama first")
        print("   1. Start Ollama: ollama serve")
        print("   2. Install models:")
        print("      ollama pull qwen2.5vl:3b")
        print("      ollama pull nomic-embed-text")
        return

    if not models_ok:
        print("\n🔧 Install Missing Models")
        print("   Vision model: ollama pull qwen2.5vl:3b")
        print("   Embedder: ollama pull nomic-embed-text")
        return

    print("\n✅ System is properly configured!")
    print("\n📝 Tips for Best Performance:")
    print("   1. Use simple, direct prompts")
    print("   2. Limit to 3-5 search results")
    print("   3. Keep summaries under 200 words")
    print("   4. Be patient (10-60s per request)")
    print("   5. Avoid complex JSON - use text formats")

    print("\n🎯 Recommended Queries:")
    print("   ✅ '看看屏幕上有什么'")
    print("   ✅ '搜索Python代码'")
    print("   ✅ '总结今天的录制内容'")
    print("   ❌ '生成详细的分析报告...' (too complex)")

    print("\n⚠️  Known Limitations:")
    print("   • Small models (3B) have reasoning limits")
    print("   • Complex tasks may fail or timeout")
    print("   • Use agent_executor_v2.py for better handling")

    print("\n🚀 For Better Performance:")
    print("   • Upgrade to 7B model if you have 16GB+ RAM")
    print("   • Use optimized prompts (see optimize_local_models.py)")
    print("   • Consider cloud APIs for complex tasks")


def main():
    print_header("MemScreen Diagnostics & Fixes")

    # Run checks
    ollama_ok, models_ok = check_ollama()

    if ollama_ok and models_ok:
        check_model_performance()
        check_token_limits()
        check_json_handling()
        check_vision_capability()

    # Provide recommendations
    provide_recommendations(ollama_ok, models_ok)

    print_header("Diagnostics Complete")
    print("\nRun this script whenever you encounter issues:\n")
    print("  python diagnose_and_fix.py\n")
    print("For optimization tips:\n")
    print("  python optimize_local_models.py\n")


if __name__ == "__main__":
    main()
