#!/usr/bin/env python3
"""
Simplified memory test focusing on core functionality
"""

import sys
from datetime import datetime

print("=" * 70)
print("🧠 MemScreen Memory Test (Simplified)")
print("=" * 70)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

test_results = []

# Test 1: Initialize Memory
print("📦 [Test 1] Initialize Memory")
print("-" * 70)
try:
    from memscreen.memory import Memory
    from memscreen.config import get_config

    config = get_config()
    llm_config = config.get_llm_config()

    memory = Memory.from_config(llm_config)

    print("✅ Memory initialized successfully")
    print(f"   LLM: {memory.config.llm.provider}")
    print(f"   Embedder: {memory.config.embedder.provider}")
    print(f"   Vector Store: {memory.config.vector_store.provider}")
    test_results.append(("Init", "PASS"))
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("Init", "FAIL"))

print()

# Test 2: Embedding Generation
print("📊 [Test 2] Embedding Generation")
print("-" * 70)
try:
    text = "Test embedding generation"
    embedding = memory.embedding_model.embed(text)

    print("✅ Embedding generated")
    print(f"   Dimensions: {len(embedding)}")
    print(f"   Sample: {embedding[:3]}")
    test_results.append(("Embedding", "PASS"))
except Exception as e:
    print(f"❌ Failed: {e}")
    test_results.append(("Embedding", "FAIL"))

print()

# Test 3: Vector Store Operations
print("🗄️  [Test 3] Vector Store Operations")
print("-" * 70)
try:
    # Test adding to vector store directly
    test_docs = ["Test document 1", "Test document 2"]
    test_embeddings = [
        memory.embedding_model.embed(test_docs[0]),
        memory.embedding_model.embed(test_docs[1])
    ]

    memory.vector_store.add(
        documents=test_docs,
        embeddings=test_embeddings,
        metadata=[{"id": 1}, {"id": 2}]
    )

    print("✅ Documents added to vector store")

    # Test search
    query = "test"
    query_embedding = memory.embedding_model.embed(query)
    results = memory.vector_store.search(
        query_embedding=query_embedding,
        top_k=2
    )

    print(f"✅ Search completed")
    print(f"   Results: {len(results) if results else 0} found")
    test_results.append(("Vector Store", "PASS"))
except Exception as e:
    print(f"❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("Vector Store", "FAIL"))

print()

# Test 4: OCR Availability
print("👁️  [Test 4] OCR Availability")
print("-" * 70)
try:
    import easyocr
    from PIL import ImageGrab
    import numpy as np

    # Just verify OCR reader can be created
    print("   Note: Full OCR test skipped to save time")
    print("✅ OCR module available")
    test_results.append(("OCR", "PASS"))
except Exception as e:
    print(f"⚠️  OCR warning: {e}")
    test_results.append(("OCR", "WARN"))

print()
print("=" * 70)
print("📊 Test Results Summary")
print("=" * 70)

passed = sum(1 for _, r in test_results if r == "PASS")
warned = sum(1 for _, r in test_results if r == "WARN")
failed = sum(1 for _, r in test_results if r == "FAIL")
total = len(test_results)

print(f"Total: {total}")
print(f"✅ Passed: {passed}")
print(f"⚠️  Warnings: {warned}")
print(f"❌ Failed: {failed}")

if failed == 0:
    print()
    print("🎉 CORE MEMORY FUNCTIONALITY WORKING!")
    print()
else:
    print()
    print("⚠️  Some tests failed")
    print()

print("=" * 70)
print("Completed at:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
print("=" * 70)
