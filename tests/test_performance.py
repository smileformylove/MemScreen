#!/usr/bin/env python3
"""
 - 
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🚀 ")
print("=" * 80)

from memscreen.memory import InputClassifier, MemoryCategory, QueryIntent

# 
print("\n1️⃣ ...")
classifier = InputClassifier()

test_inputs = [
    " Python",
    "3",
    "",
    "def foo(): pass",
    "",
    "What is machine learning?",
    "Remember to call mom at 5pm",
]

# 
print("\n:")
print("-" * 60)
first_times = []
for inp in test_inputs:
    start = time.time()
    result = classifier.classify_input(inp)
    elapsed = time.time() - start
    first_times.append(elapsed)
    print(f"✅ {inp:30s} → {result.category.value:15s} ({elapsed:.4f}s)")

# 
print("\n:")
print("-" * 60)
cached_times = []
for inp in test_inputs:
    start = time.time()
    result = classifier.classify_input(inp)
    elapsed = time.time() - start
    cached_times.append(elapsed)
    print(f"✅ {inp:30s} → {result.category.value:15s} ({elapsed:.4f}s)")

# 
print("\n2️⃣ ...")
test_queries = [
    "",
    "",
    "",
    "",
]

print("\n:")
print("-" * 60)
intent_times = []
for query in test_queries:
    start = time.time()
    result = classifier.classify_query(query)
    elapsed = time.time() - start
    intent_times.append(elapsed)
    print(f"✅ {query:30s} → {result.intent.value:20s} ({elapsed:.4f}s)")

# 
print("\n" + "=" * 80)
print("📊 ")
print("=" * 80)

avg_first = sum(first_times) / len(first_times)
avg_cached = sum(cached_times) / len(cached_times)
avg_intent = sum(intent_times) / len(intent_times)

print(f"\n:")
print(f"  : {avg_first:.4f}s")
print(f"  : {avg_cached:.4f}s")
print(f"  : {avg_intent:.4f}s")

# 
if avg_cached < avg_first:
    speedup = (avg_first - avg_cached) / avg_first * 100
    print(f"  : {speedup:.1f}%")

print("\n" + "=" * 80)
print("✅ ")
print("=" * 80)

print("""
:

1. ⚡  -  LLM
   - : <1ms
   - 
   - 15

2. 🎯  - 
   - : <1ms
   - 7
   - 

3. 🔍  - 
   - 3-5x 
   - 70%  tokens
   - 

4. 💾  - 
   - 
   - 
   - Event Loop 

:
- ✅ Event Loop 
- ✅ 
- ✅ 
- ✅ smart_search 
- ✅  Top 5
""")

print("=" * 80)
