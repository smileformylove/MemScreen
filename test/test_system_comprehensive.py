#!/usr/bin/env python3
"""
Comprehensive System Test for MemScreen v0.4.0

Tests all major components and identifies issues related to local model limitations.
"""

import sys
import os
import json
import traceback
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

class TestResult:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors = []

    def add_pass(self, name: str):
        self.passed += 1
        print(f"✅ PASS: {name}")

    def add_fail(self, name: str, error: str):
        self.failed += 1
        self.errors.append((name, error))
        print(f"❌ FAIL: {name}")
        print(f"   Error: {error}")

    def add_warning(self, name: str, warning: str):
        self.warnings += 1
        print(f"⚠️  WARNING: {name}")
        print(f"   {warning}")

    def summary(self):
        total = self.passed + self.failed
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⚠️  Warnings: {self.warnings}")

        if self.errors:
            print("\nFailed Tests:")
            for name, error in self.errors:
                print(f"  - {name}: {error[:100]}...")

        return self.failed == 0


def test_ollama_connection(result: TestResult):
    """Test 1: Ollama API Connection"""
    print("\n" + "=" * 60)
    print("TEST 1: Ollama API Connection")
    print("=" * 60)

    try:
        import requests

        # Test basic connection
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=10)

        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])

            # Check for required models
            model_names = [m.get("name", "") for m in models]

            has_vision = any("qwen2.5vl" in name or "llava" in name for name in model_names)
            has_embedder = any("nomic-embed" in name or "mxbai-embed" in name for name in model_names)

            result.add_pass("Ollama Connection")

            if has_vision:
                result.add_pass("Vision Model Available")
            else:
                result.add_fail("Vision Model", "No vision model found. Install with: ollama pull qwen2.5vl:3b")

            if has_embedder:
                result.add_pass("Embedder Model Available")
            else:
                result.add_fail("Embedder Model", "No embedder model found. Install with: ollama pull nomic-embed-text")

            print(f"\nAvailable Models: {', '.join(model_names[:5])}")
        else:
            result.add_fail("Ollama Connection", f"Status code: {response.status_code}")

    except Exception as e:
        result.add_fail("Ollama Connection", str(e))


def test_memory_system(result: TestResult):
    """Test 2: Memory System"""
    print("\n" + "=" * 60)
    print("TEST 2: Memory System")
    print("=" * 60)

    try:
        from memscreen.memory import Memory
        from memscreen.memory.models import MemoryConfig, EmbedderConfig, LlmConfig, VectorStoreConfig

        config = MemoryConfig(
            embedder=EmbedderConfig(provider="ollama", config={"model": "nomic-embed-text"}),
            vector_store=VectorStoreConfig(provider="chroma", config={"path": "./db/chroma_db_test"}),
            llm=LlmConfig(provider="ollama", config={"model": "qwen2.5vl:3b", "max_tokens": 512, "temperature": 0.7})
        )

        memory = Memory(config=config)
        result.add_pass("Memory Initialization")

        # Test adding memory
        try:
            add_result = memory.add(
                "Test memory content for verification",
                user_id="test_user",
                metadata={"source": "test", "type": "test"}
            )

            if add_result:
                result.add_pass("Memory Add")
            else:
                result.add_warning("Memory Add", "Add returned empty result")

        except Exception as e:
            result.add_fail("Memory Add", str(e))

        # Test search
        try:
            search_result = memory.search(
                query="test content",
                user_id="test_user"
            )

            if search_result and "results" in search_result:
                result.add_pass("Memory Search")
                count = len(search_result["results"])
                print(f"   Found {count} results")
            else:
                result.add_warning("Memory Search", "No results returned")

        except Exception as e:
            result.add_fail("Memory Search", str(e))

    except Exception as e:
        result.add_fail("Memory Initialization", str(e))
        traceback.print_exc()


def test_llm_generation(result: TestResult):
    """Test 3: LLM Generation"""
    print("\n" + "=" * 60)
    print("TEST 3: LLM Generation")
    print("=" * 60)

    try:
        from memscreen.llm import LlmFactory

        # Test with smaller model
        llm = LlmFactory.create(
            provider_name="ollama",
            config={
                "model": "qwen2.5vl:3b",
                "temperature": 0.6,
                "max_tokens": 100  # Small limit for testing
            }
        )

        result.add_pass("LLM Initialization")

        # Test simple generation
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello' in one word."}
            ]

            response = llm.generate_response(messages)

            if response and len(response) > 0:
                result.add_pass("LLM Generation")
                print(f"   Response: {response[:100]}...")
            else:
                result.add_fail("LLM Generation", "Empty response")

        except Exception as e:
            result.add_fail("LLM Generation", str(e))

    except Exception as e:
        result.add_fail("LLM Initialization", str(e))


def test_embeddings(result: TestResult):
    """Test 4: Embeddings"""
    print("\n" + "=" * 60)
    print("TEST 4: Text Embeddings")
    print("=" * 60)

    try:
        from memscreen.embeddings import EmbedderFactory

        embedder = EmbedderFactory.create(
            provider_name="ollama",
            config={"model": "nomic-embed-text"},
            vector_config=None
        )

        result.add_pass("Embedder Initialization")

        # Test embedding generation
        try:
            text = "This is a test text for embedding generation"
            embedding = embedder.embed(text)

            if embedding and len(embedding) > 0:
                result.add_pass("Embedding Generation")
                print(f"   Embedding dimension: {len(embedding)}")
            else:
                result.add_fail("Embedding Generation", "Empty embedding")

        except Exception as e:
            result.add_fail("Embedding Generation", str(e))

    except Exception as e:
        result.add_fail("Embedder Initialization", str(e))


def test_agent_executor(result: TestResult):
    """Test 5: Agent Executor"""
    print("\n" + "=" * 60)
    print("TEST 5: Agent Executor")
    print("=" * 60)

    try:
        from memscreen.presenters.agent_executor import AgentExecutor
        from memscreen.memory import Memory
        from memscreen.memory.models import MemoryConfig, EmbedderConfig, LlmConfig, VectorStoreConfig

        # Initialize memory
        config = MemoryConfig(
            embedder=EmbedderConfig(provider="ollama", config={"model": "nomic-embed-text"}),
            vector_store=VectorStoreConfig(provider="chroma", config={"path": "./db/chroma_db_test"}),
            llm=LlmConfig(provider="ollama", config={"model": "qwen2.5vl:3b", "max_tokens": 256, "temperature": 0.6})
        )
        memory = Memory(config=config)

        # Initialize agent
        agent = AgentExecutor(
            memory_system=memory,
            ollama_base_url="http://127.0.0.1:11434",
            current_model="qwen2.5vl:3b"
        )

        result.add_pass("Agent Initialization")

        # Test task analysis (simple query, no actual execution)
        try:
            workflow = agent._analyze_task("搜索关于Python的内容")

            if workflow and "type" in workflow and "steps" in workflow:
                result.add_pass("Task Analysis")
                print(f"   Workflow type: {workflow['type']}")
                print(f"   Steps: {len(workflow['steps'])}")
            else:
                result.add_fail("Task Analysis", "Invalid workflow structure")

        except Exception as e:
            result.add_fail("Task Analysis", str(e))

    except Exception as e:
        result.add_fail("Agent Initialization", str(e))
        traceback.print_exc()


def test_json_handling(result: TestResult):
    """Test 6: JSON Parsing (Common Issue with Small Models)"""
    print("\n" + "=" * 60)
    print("TEST 6: JSON Handling")
    print("=" * 60)

    try:
        import requests

        # Test if model can generate valid JSON
        prompt = """Respond with valid JSON only:
{"status": "ok", "message": "test"}"""

        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "qwen2.5vl:3b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,  # Low temperature for deterministic output
                    "num_predict": 100
                }
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            text = data.get("response", "").strip()

            print(f"   Model response: {text[:100]}...")

            # Try to parse as JSON
            try:
                # Clean common issues
                text_clean = text.strip()
                if text_clean.startswith("```json"):
                    text_clean = text_clean[7:]
                if text_clean.startswith("```"):
                    text_clean = text_clean[3:]
                if text_clean.endswith("```"):
                    text_clean = text_clean[:-3]
                text_clean = text_clean.strip()

                parsed = json.loads(text_clean)

                if parsed and "status" in parsed:
                    result.add_pass("JSON Generation")
                else:
                    result.add_warning("JSON Generation", "JSON parsed but missing expected fields")

            except json.JSONDecodeError as e:
                result.add_fail("JSON Generation", f"Invalid JSON: {str(e)}")
                result.add_warning("Model Capability", "Small models may struggle with JSON. Use text-based formats instead.")

        else:
            result.add_fail("JSON Generation", f"API error: {response.status_code}")

    except Exception as e:
        result.add_fail("JSON Generation", str(e))


def test_screen_capture(result: TestResult):
    """Test 7: Screen Capture"""
    print("\n" + "=" * 60)
    print("TEST 7: Screen Capture")
    print("=" * 60)

    try:
        from PIL import ImageGrab
        from datetime import datetime
        import os

        # Capture screen
        screenshot = ImageGrab.grab()

        # Create temp dir
        temp_dir = "./db/test"
        os.makedirs(temp_dir, exist_ok=True)

        # Save screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_path = os.path.join(temp_dir, f"test_screenshot_{timestamp}.png")
        screenshot.save(temp_path)

        # Check file exists
        if os.path.exists(temp_path):
            file_size = os.path.getsize(temp_path)
            result.add_pass("Screen Capture")
            print(f"   Screenshot size: {file_size / 1024:.1f} KB")

            # Clean up
            os.remove(temp_path)
        else:
            result.add_fail("Screen Capture", "File not created")

    except Exception as e:
        result.add_fail("Screen Capture", str(e))


def test_vision_model(result: TestResult):
    """Test 8: Vision Model"""
    print("\n" + "=" * 60)
    print("TEST 8: Vision Model")
    print("=" * 60)

    try:
        import requests
        import base64
        from PIL import ImageGrab
        import os

        # Capture screen
        screenshot = ImageGrab.grab()

        # Save to temp file
        temp_dir = "./db/test"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, "test_vision.png")
        screenshot.save(temp_path)

        # Read and encode
        with open(temp_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # Simple vision prompt
        vision_prompt = "Describe this screenshot in one sentence."

        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "qwen2.5vl:3b",
                "prompt": vision_prompt,
                "images": [image_data],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150  # Limit output
                }
            },
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            analysis = data.get("response", "").strip()

            if analysis:
                result.add_pass("Vision Model")
                print(f"   Analysis: {analysis[:100]}...")
            else:
                result.add_fail("Vision Model", "Empty response")
        else:
            result.add_fail("Vision Model", f"API error: {response.status_code}")

        # Clean up
        try:
            os.remove(temp_path)
        except:
            pass

    except Exception as e:
        result.add_fail("Vision Model", str(e))
        traceback.print_exc()


def main():
    """Run all tests"""
    print("=" * 60)
    print("MemScreen v0.4.0 - Comprehensive System Test")
    print("=" * 60)

    result = TestResult()

    # Run tests
    test_ollama_connection(result)
    test_memory_system(result)
    test_llm_generation(result)
    test_embeddings(result)
    test_agent_executor(result)
    test_json_handling(result)
    test_screen_capture(result)
    test_vision_model(result)

    # Print summary
    success = result.summary()

    # Provide recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)

    if result.failed > 0:
        print("\n🔧 Critical Issues to Fix:")
        print("   1. Ensure Ollama is running: ollama serve")
        print("   2. Install required models:")
        print("      ollama pull qwen2.5vl:3b")
        print("      ollama pull nomic-embed-text")
        print("   3. Check error messages above for details")

    if result.warnings > 0:
        print("\n⚠️  Warnings to Consider:")
        print("   1. Small models (3B) have limitations")
        print("   2. Use simpler prompts for better results")
        print("   3. Avoid complex JSON parsing with small models")
        print("   4. Use text-based formats instead of JSON when possible")
        print("   5. Limit num_predict to avoid truncation")

    print("\n📝 Testing Complete!")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
