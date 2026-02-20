#!/usr/bin/env python3
"""
Dynamic Memory System - Interactive Demo

This script demonstrates the new dynamic memory features.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🚀 Dynamic Memory System - Interactive Demo")
print("=" * 70)

# Test imports
print("\n[1/5] Importing modules...")
try:
    from memscreen.memory import (
        MemoryCategory,
        QueryIntent,
        InputClassifier,
        DynamicMemoryConfig,
    )
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Initialize classifier
print("\n[2/5] Initializing classifier...")
classifier = InputClassifier()
print("✓ Classifier ready")

# Demo: Input classification
print("\n" + "=" * 70)
print("📝 INPUT CLASSIFICATION DEMO")
print("=" * 70)

test_inputs = [
    (" Python", "question"),
    ("3", "task"),
    ("def hello():\n    print('Hello')", "code"),
    ("1\n2", "procedure"),
    ("", "conversation"),
]

print("\n:")
for text, expected_category in test_inputs:
    result = classifier.classify_input(text)
    status = "✓" if result.category.value == expected_category else "✗"
    print(f"{status} '{text[:30]}...'")
    print(f"   → : {result.category.value} (: {expected_category})")
    print(f"   → : {result.confidence:.2f}")

# Demo: Query intent classification
print("\n" + "=" * 70)
print("🔍 QUERY INTENT CLASSIFICATION DEMO")
print("=" * 70)

test_queries = [
    ("", "retrieve_fact"),
    ("", "find_procedure"),
    ("", "search_conversation"),
    ("", "locate_code"),
]

print("\n:")
for query, expected_intent in test_queries:
    result = classifier.classify_query(query)
    status = "✓" if result.intent.value == expected_intent else "✗"
    print(f"{status} '{query}'")
    print(f"   → : {result.intent.value}")
    print(f"   → : {[c.value for c in result.target_categories]}")

# Demo: Configuration
print("\n" + "=" * 70)
print("⚙️  DYNAMIC CONFIGURATION DEMO")
print("=" * 70)

config = DynamicMemoryConfig(
    enable_auto_classification=True,
    enable_intent_classification=True,
    enable_category_weights=True,
    default_category_weights={
        MemoryCategory.TASK: 1.5,
        MemoryCategory.FACT: 1.2,
        MemoryCategory.PROCEDURE: 1.3,
    }
)

print("\n:")
print(f"  • : {config.enable_auto_classification}")
print(f"  • : {config.enable_intent_classification}")
print(f"  • : {config.enable_category_weights}")
print(f"  • : {config.default_category_weights[MemoryCategory.TASK]}")
print(f"  • : {config.default_category_weights[MemoryCategory.FACT]}")
print(f"  • : {config.default_category_weights[MemoryCategory.PROCEDURE]}")

# Demo: Categories overview
print("\n" + "=" * 70)
print("📂 MEMORY CATEGORIES")
print("=" * 70)

categories = [
    ("question", ""),
    ("task", ""),
    ("fact", ""),
    ("concept", ""),
    ("code", ""),
    ("procedure", ""),
    ("conversation", ""),
    ("document", ""),
]

print("\n:")
for cat_en, cat_zh in categories:
    print(f"  • {cat_en:12} - {cat_zh}")

# Demo: Intents overview
print("\n" + "=" * 70)
print("🎯 QUERY INTENTS")
print("=" * 70)

intents = [
    ("retrieve_fact", ""),
    ("find_procedure", ""),
    ("search_conversation", ""),
    ("locate_code", ""),
    ("get_tasks", ""),
    ("general_search", ""),
]

print("\n:")
for intent_en, intent_zh in intents:
    print(f"  • {intent_en:18} - {intent_zh}")

# Summary
print("\n" + "=" * 70)
print("📊 PERFORMANCE BENEFITS")
print("=" * 70)

print("\n:")
print("  • : 3-5 ()")
print("  • Token :  70% ()")
print("  • :  ()")
print("  • :  ()")

# Usage examples
print("\n" + "=" * 70)
print("💡 USAGE EXAMPLES")
print("=" * 70)

print("""
# 1.  Memory
from memscreen import Memory
from memscreen.memory import MemoryConfig

config = MemoryConfig(
    llm={"provider": "ollama", "config": {"model": "llama2"}},
    embedder={"provider": "ollama", "config": {"model": "nomic-embed-text"}},
    vector_store={"provider": "chroma", "config": {"path": "./chroma_db"}},
    enable_dynamic_memory=True,  # 
)
memory = Memory(config)

# 2.  Memory
result = memory.add_with_classification(
    "",
    user_id="user123",
)
print(result['classification']['category'])  # "task"

# 3. 
results = memory.smart_search(
    "",
    user_id="user123",
)
#  procedure, workflow, task 

# 4. 
context = memory.get_context_for_response(
    "",
    user_id="user123",
)
# 
""")

print("\n" + "=" * 70)
print("✅  Memory ")
print("=" * 70)
print("\n📚 : docs/DYNAMIC_MEMORY.md")
print("📖 : examples/dynamic_memory_example.py")
print("🧪 : tests/verify_dynamic_memory.py")
print("=" * 70)
