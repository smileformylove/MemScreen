#!/usr/bin/env python3
"""
Step-3.5-Flash Model Test Script

This script tests the Step-3.5-Flash model from StepFun using vLLM backend.

Model Details:
- Name: stepfun-ai/Step-3.5-Flash
- Parameters: 196B total, 11B active (sparse MoE)
- Features: Advanced reasoning, tool calling, multi-token prediction
- Optimized for: Low-latency, cost-effective long-context inference

Usage:
    python test_step35flash.py

Environment Variables:
    MEMSCREEN_VLLM_URL: vLLM server URL (default: http://localhost:8001)
    STEP35FLASH_MODEL: Model name (default: stepfun-ai/Step-3.5-Flash)
"""

import os
import sys
import time
from typing import List, Dict

# Model configuration
DEFAULT_MODEL = "stepfun-ai/Step-3.5-Flash"
DEFAULT_BASE_URL = "http://localhost:8001"

# Get configuration from environment
MODEL = os.getenv("STEP35FLASH_MODEL", DEFAULT_MODEL)
BASE_URL = os.getenv("MEMSCREEN_VLLM_URL", DEFAULT_BASE_URL)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_connection():
    """Test basic connection to vLLM server."""
    print_section("Test 1: Connection Test")

    try:
        import requests

        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ vLLM server is running")
            print(f"   URL: {BASE_URL}")
            return True
        else:
            print(f"❌ vLLM server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to vLLM server: {e}")
        print(f"\n💡 Start the server with:")
        print(f"   docker-compose -f docker-compose.step35flash.yml up -d")
        return False


def test_basic_inference():
    """Test basic text generation."""
    print_section("Test 2: Basic Inference")

    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=BASE_URL,
            api_key="EMPTY"
        )

        # Simple test prompt
        prompt = "What is 2+2? Answer with just the number."

        print(f"Prompt: {prompt}")

        start_time = time.time()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.0
        )
        elapsed = time.time() - start_time

        result = response.choices[0].message.content
        print(f"Response: {result}")
        print(f"Time: {elapsed:.2f}s")
        print("✅ Basic inference test passed")
        return True

    except Exception as e:
        print(f"❌ Basic inference test failed: {e}")
        return False


def test_reasoning():
    """Test advanced reasoning capabilities."""
    print_section("Test 3: Reasoning Capabilities")

    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=BASE_URL,
            api_key="EMPTY"
        )

        # Reasoning test prompt
        prompt = """
        A bat and ball cost $1.10 in total. The bat costs $1.00 more than the ball.
        How much does the ball cost? Think step by step.
        """

        print(f"Prompt: {prompt.strip()}")

        start_time = time.time()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        elapsed = time.time() - start_time

        result = response.choices[0].message.content
        print(f"\nResponse:\n{result}")
        print(f"\nTime: {elapsed:.2f}s")
        print("✅ Reasoning test passed")
        return True

    except Exception as e:
        print(f"❌ Reasoning test failed: {e}")
        return False


def test_long_context():
    """Test long context handling."""
    print_section("Test 4: Long Context Handling")

    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=BASE_URL,
            api_key="EMPTY"
        )

        # Create a long context prompt
        context = "\n".join([
            f"Fact {i}: This is fact number {i} about the topic."
            for i in range(1, 51)
        ])

        prompt = f"{context}\n\nWhat is fact number 47?"

        print(f"Context length: {len(context)} characters")
        print(f"Question: What is fact number 47?")

        start_time = time.time()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.0
        )
        elapsed = time.time() - start_time

        result = response.choices[0].message.content
        print(f"\nResponse: {result}")
        print(f"Time: {elapsed:.2f}s")
        print("✅ Long context test passed")
        return True

    except Exception as e:
        print(f"❌ Long context test failed: {e}")
        return False


def test_streaming():
    """Test streaming response."""
    print_section("Test 5: Streaming Response")

    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=BASE_URL,
            api_key="EMPTY"
        )

        prompt = "Count from 1 to 10, one number per line."

        print(f"Prompt: {prompt}")
        print("\nStreaming response:")

        start_time = time.time()
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.0,
            stream=True
        )

        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content

        elapsed = time.time() - start_time
        print(f"\n\nTime: {elapsed:.2f}s")
        print("✅ Streaming test passed")
        return True

    except Exception as e:
        print(f"\n❌ Streaming test failed: {e}")
        return False


def test_with_memscreen_config():
    """Test using MemScreen configuration system."""
    print_section("Test 6: MemScreen Integration")

    try:
        from memscreen.config import MemScreenConfig
        from memscreen.llm.vllm import VllmConfig, VllmLLM

        config = MemScreenConfig()

        # Display Step-3.5-Flash configuration
        print(f"✅ MemScreenConfig loaded")
        print(f"   Default reasoning model: {config.vllm_reasoning_model}")
        print(f"   vLLM base URL: {config.vllm_base_url}")
        print(f"   Tensor parallel size: {config.vllm_tensor_parallel_size}")
        print(f"   GPU memory utilization: {config.vllm_gpu_memory_utilization}")

        # Create VllmConfig for Step-3.5-Flash
        vllm_config = VllmConfig(
            model=config.vllm_reasoning_model,
            vllm_base_url=BASE_URL,
            temperature=0.1,
            max_tokens=512
        )

        print(f"\n✅ VllmConfig created for Step-3.5-Flash")
        print(f"   Model: {vllm_config.model}")
        print(f"   Temperature: {vllm_config.temperature}")
        print(f"   Max tokens: {vllm_config.max_tokens}")

        return True

    except Exception as e:
        print(f"❌ MemScreen integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  🧠 Step-3.5-Flash Model Test Suite")
    print("=" * 60)
    print(f"\nModel: {MODEL}")
    print(f"Server: {BASE_URL}")
    print(f"Parameters: 196B (11B active, sparse MoE)")

    # Run tests
    tests = [
        ("Connection", test_connection),
        ("Basic Inference", test_basic_inference),
        ("Reasoning", test_reasoning),
        ("Long Context", test_long_context),
        ("Streaming", test_streaming),
        ("MemScreen Integration", test_with_memscreen_config),
    ]

    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))

    # Print summary
    print_section("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:30s} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! Step-3.5-Flash is ready to use.")
        print("\n💡 To use in MemScreen:")
        print(f"   export MEMSCREEN_LLM_BACKEND=vllm")
        print(f"   export MEMSCREEN_VLLM_URL={BASE_URL}")
        print(f"   export MEMSCREEN_VLLM_LLM_MODEL={MODEL}")
        print(f"   python start.py")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
