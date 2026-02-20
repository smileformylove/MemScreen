#!/usr/bin/env python3
"""
 Memory 
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🧪  Memory ")
print("=" * 70)

#  1: 
print("\n[ 1] ...")
try:
    from memscreen.memory import (
        Memory,
        MemoryConfig,
        MemoryCategory,
        DynamicMemoryConfig,
    )
    print("✅ ")
except Exception as e:
    print(f"❌ : {e}")
    sys.exit(1)

#  2: 
print("\n[ 2] ...")
try:
    config = MemoryConfig(
        enable_dynamic_memory=True,
        dynamic_config={
            "enable_auto_classification": True,
            "enable_intent_classification": True,
            "enable_category_weights": True,
        }
    )
    print("✅ ")
    print(f"   -  Memory : {config.enable_dynamic_memory}")
    print(f"   - : {config.dynamic_config}")
except Exception as e:
    print(f"❌ : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

#  3: 
print("\n[ 3] ...")
try:
    from memscreen.memory import InputClassifier

    classifier = InputClassifier()

    # 
    test_cases = [
        ("", "question"),
        ("", "task"),
        ("", "question"),
    ]

    all_passed = True
    for text, expected in test_cases:
        result = classifier.classify_input(text)
        if result.category.value == expected:
            print(f"   ✅ '{text[:20]}...' → {result.category.value}")
        else:
            print(f"   ⚠️  '{text[:20]}...' → {result.category.value} (: {expected})")
            all_passed = False

    if all_passed:
        print("✅ ")
except Exception as e:
    print(f"❌ : {e}")
    import traceback
    traceback.print_exc()

#  4: 
print("\n[ 4] ...")
try:
    queries = [
        ("", "find_procedure"),
        ("", "search_conversation"),
    ]

    for query, expected_intent in queries:
        result = classifier.classify_query(query)
        if result.intent.value == expected_intent:
            print(f"   ✅ '{query}' → {result.intent.value}")
            print(f"      : {[c.value for c in result.target_categories]}")
        else:
            print(f"   ⚠️  '{query}' → {result.intent.value} (: {expected_intent})")

    print("✅ ")
except Exception as e:
    print(f"❌ : {e}")

#  5: 
print("\n[ 5] ...")
try:
    categories = [
        MemoryCategory.QUESTION,
        MemoryCategory.TASK,
        MemoryCategory.FACT,
        MemoryCategory.CODE,
        MemoryCategory.PROCEDURE,
    ]

    print(f"   : {len(list(MemoryCategory))}")
    print(f"   :")
    for cat in categories:
        print(f"      • {cat.value}")

    print("✅ ")
except Exception as e:
    print(f"❌ : {e}")

#  6:  Memory  LLM/
print("\n[ 6]  Memory ...")
try:
    print("    1: ")
    query1 = " Memory"
    result1 = classifier.classify_input(query1)
    print(f"   : '{query1}'")
    print(f"   : {result1.category.value}")
    print(f"   : {result1.confidence:.2f}")

    print("\n    2: ")
    query2 = ""
    result2 = classifier.classify_input(query2)
    print(f"   : '{query2}'")
    print(f"   : {result2.category.value}")
    print(f"   : {result2.confidence:.2f}")
    print(f"   : {result2.metadata}")

    print("\n    3: ")
    query3 = ""
    result3 = classifier.classify_query(query3)
    print(f"   : '{query3}'")
    print(f"   : {result3.intent.value}")
    print(f"   : {[c.value for c in result3.target_categories]}")
    print(f"   : {result3.search_params}")

    print("\n✅ ")
except Exception as e:
    print(f"❌ : {e}")
    import traceback
    traceback.print_exc()

# 
print("\n" + "=" * 70)
print("📊 ")
print("=" * 70)
print("""
✅  Memory  MemScreen

:
  1. 
  2. 
  3. 
  4. 

:
  #  start.py 
  config = MemoryConfig(
      enable_dynamic_memory=True,
      ...
  )
  memory = Memory(config)

  # 
  memory.add_with_classification("", user_id="user123")
  memory.smart_search("", user_id="user123")
  memory.get_context_for_response("", user_id="user123")
""")

print("=" * 70)
print("🎉  Memory ")
print("=" * 70)
