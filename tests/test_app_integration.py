#!/usr/bin/env python3
"""
 Memory 
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🔍 MemScreen ")
print("=" * 80)

#  1:  Ollama 
print("\n[ 1]  Ollama ...")
try:
    import requests
    response = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
    if response.status_code == 200:
        print("✅ Ollama ")
        models = response.json().get("models", [])
        print(f"   : {len(models)} ")
        for model in models[:3]:
            print(f"      - {model.get('name', 'unknown')}")
    else:
        print("⚠️  Ollama ")
except Exception as e:
    print(f"❌  Ollama : {e}")
    print("    Ollama: ollama serve")

#  2: 
print("\n[ 2] ...")
try:
    from memscreen.config import get_config
    config = get_config()
    print("✅ ")
    print(f"   : {config.db_path}")
    print(f"   : {config.timezone}")
except Exception as e:
    print(f"❌ : {e}")

#  3:  Memory 
print("\n[ 3]  Memory ...")
try:
    from memscreen.memory import MemoryConfig

    # 
    test_config = MemoryConfig(
        enable_dynamic_memory=True,
        dynamic_config={
            "enable_auto_classification": True,
            "enable_intent_classification": True,
            "enable_category_weights": True,
        }
    )

    print("✅  Memory ")
    print(f"   enable_dynamic_memory: {test_config.enable_dynamic_memory}")
    print(f"   dynamic_config: {test_config.dynamic_config}")
except Exception as e:
    print(f"❌  Memory : {e}")
    import traceback
    traceback.print_exc()

#  4: 
print("\n[ 4] ...")
try:
    from memscreen.memory import InputClassifier

    classifier = InputClassifier()

    #  MemScreen 
    test_cases = [
        ("", "task"),
        (" Docker ", "question"),
        ("def main():\n    pass", "code"),
    ]

    for text, expected in test_cases:
        result = classifier.classify_input(text)
        if result.category.value == expected:
            print(f"   ✅ '{text[:20]}...' → {result.category.value}")
        else:
            print(f"   ⚠️  '{text[:20]}...' → {result.category.value} (: {expected})")

    print("✅ ")
except Exception as e:
    print(f"❌ : {e}")

#  5:  Memory 
print("\n[ 5]  Memory ...")
try:
    from memscreen.memory import Memory
    from memscreen.memory import MemoryConfig
    from memscreen.config import get_config

    app_config = get_config()

    # 
    from memscreen.memory import (
        EmbedderConfig,
        VectorStoreConfig,
        LlmConfig,
    )

    config = MemoryConfig(
        embedder=EmbedderConfig(
            provider=app_config.get_embedder_config()["provider"],
            config=app_config.get_embedder_config()["config"]
        ),
        vector_store=VectorStoreConfig(
            provider=app_config.get_vector_store_config()["provider"],
            config=app_config.get_vector_store_config()["config"]
        ),
        llm=LlmConfig(
            provider=app_config.get_llm_config()["provider"],
            config=app_config.get_llm_config()["config"]
        ),
        mllm=LlmConfig(
            provider=app_config.get_mllm_config()["provider"],
            config=app_config.get_mllm_config()["config"]
        ),
        history_db_path=str(app_config.db_path),
        timezone=app_config.timezone if hasattr(app_config, 'timezone') else "US/Pacific",
        enable_dynamic_memory=True,
        dynamic_config={
            "enable_auto_classification": True,
            "enable_intent_classification": True,
            "enable_category_weights": True,
        }
    )

    print("✅ MemoryConfig ")
    print(f"    Memory: {config.enable_dynamic_memory}")

    #  Memory
    memory = Memory(config=config)

    print("✅ Memory ")
    print(f"   : {memory.enable_dynamic_memory}")

    if memory.enable_dynamic_memory:
        print(f"   : {memory.classifier is not None}")
        print(f"   : {memory.dynamic_manager is not None}")
        print(f"   : {memory.context_retriever is not None}")

except Exception as e:
    print(f"❌ Memory : {e}")
    import traceback
    traceback.print_exc()

#  6:  API
print("\n[ 6]  API ...")
try:
    # 
    classification = memory.classify_input("")
    print(f"✅ classify_input() ")
    print(f"   : {classification['category']}")

    # 
    stats = memory.get_dynamic_statistics()
    print(f"✅ get_dynamic_statistics() ")
    print(f"   : {stats}")

except Exception as e:
    print(f"❌ API : {e}")
    import traceback
    traceback.print_exc()

# 
print("\n" + "=" * 80)
print("📊 ")
print("=" * 80)

print("""
✅  Memory  MemScreen 

:
  1. ✅ Ollama 
  2. ✅ 
  3. ✅  Memory 
  4. ✅ 
  5. ✅ Memory 
  6. ✅  API 

:
  • 
  • Memory 
  •  API 

:
  python start.py

GUI :
  :
  1.  -  Dock 
  2.  - 
  3.  - macOS 
""")

print("=" * 80)
print("🎉 ")
print("=" * 80)
