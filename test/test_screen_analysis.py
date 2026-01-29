#!/usr/bin/env python3
"""Test script for screen analysis functionality"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from memscreen.memory import get_memory_manager
from memscreen.presenters.agent_executor import AgentExecutor
import time

def test_screen_analysis():
    """Test the screen capture and analysis functionality"""

    print("=" * 60)
    print("Testing Screen Analysis Agent")
    print("=" * 60)

    # Initialize memory system
    print("\n[1/3] Initializing memory system...")
    try:
        from memscreen.memory import Memory
        from memscreen.memory.models import MemoryConfig, EmbedderConfig, LlmConfig, VectorStoreConfig

        config = MemoryConfig(
            embedder=EmbedderConfig(provider="ollama", config={"model": "nomic-embed-text"}),
            vector_store=VectorStoreConfig(provider="chroma", config={"path": "./db/chroma_db"}),
            llm=LlmConfig(provider="ollama", config={"model": "qwen3:1.7b", "max_tokens": 512, "temperature": 0.7})
        )
        memory_system = Memory(config=config)
        print("✅ Memory system initialized")
    except Exception as e:
        print(f"❌ Memory initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Initialize Agent Executor
    print("\n[2/3] Initializing Agent Executor...")
    try:
        agent = AgentExecutor(
            memory_system=memory_system,
            ollama_base_url="http://127.0.0.1:11434",
            current_model="qwen2.5vl:3b"
        )
        print("✅ Agent Executor initialized")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test screen analysis
    print("\n[3/3] Testing screen capture and analysis...")
    print("-" * 60)

    test_queries = [
        "看看屏幕上有什么",
        "分析当前屏幕内容"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test Query {i}: {query}")
        print("-" * 40)

        try:
            result = agent.execute_task(query)

            if result.get("success"):
                print(f"\n✅ Success! Execution time: {result['execution_time']:.2f}s\n")
                print("Response:")
                print("-" * 40)
                print(result["response"])
                print("-" * 40)
            else:
                print(f"\n❌ Failed: {result}")

            time.sleep(2)  # Wait between tests

        except Exception as e:
            print(f"\n❌ Error during execution: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_screen_analysis()
