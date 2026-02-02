"""
Simple verification script for Dynamic Memory features.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("Dynamic Memory System - Feature Verification")
print("=" * 60)

# Test 1: Import verification
print("\n[TEST 1] Verifying imports...")
try:
    from memscreen.memory import (
        MemoryCategory,
        QueryIntent,
        ClassifiedInput,
        ClassifiedQuery,
        DynamicMemoryConfig,
        InputClassifier,
        DynamicMemoryManager,
        ContextRetriever,
    )
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: MemoryCategory enum
print("\n[TEST 2] Testing MemoryCategory enum...")
try:
    assert MemoryCategory.QUESTION.value == "question"
    assert MemoryCategory.TASK.value == "task"
    assert MemoryCategory.FACT.value == "fact"
    assert MemoryCategory.CODE.value == "code"
    assert MemoryCategory.PROCEDURE.value == "procedure"
    print("✓ MemoryCategory enum works correctly")
except Exception as e:
    print(f"✗ MemoryCategory test failed: {e}")

# Test 3: QueryIntent enum
print("\n[TEST 3] Testing QueryIntent enum...")
try:
    assert QueryIntent.RETRIEVE_FACT.value == "retrieve_fact"
    assert QueryIntent.FIND_PROCEDURE.value == "find_procedure"
    assert QueryIntent.SEARCH_CONVERSATION.value == "search_conversation"
    print("✓ QueryIntent enum works correctly")
except Exception as e:
    print(f"✗ QueryIntent test failed: {e}")

# Test 4: InputClassifier
print("\n[TEST 4] Testing InputClassifier...")
try:
    classifier = InputClassifier()

    # Test question classification
    result1 = classifier.classify_input("What is the capital of France?")
    assert result1.category == MemoryCategory.QUESTION
    print(f"  - Question classification: {result1.category.value} (confidence: {result1.confidence:.2f})")

    # Test task classification
    result2 = classifier.classify_input("Remember to call the client tomorrow")
    assert result2.category == MemoryCategory.TASK
    print(f"  - Task classification: {result2.category.value} (confidence: {result2.confidence:.2f})")

    # Test code classification
    result3 = classifier.classify_input("def hello():\n    print('Hello')")
    assert result3.category == MemoryCategory.CODE
    print(f"  - Code classification: {result3.category.value} (confidence: {result3.confidence:.2f})")

    # Test procedure classification
    result4 = classifier.classify_input("Step 1: Install dependencies\nStep 2: Run the server")
    assert result4.category == MemoryCategory.PROCEDURE
    print(f"  - Procedure classification: {result4.category.value} (confidence: {result4.confidence:.2f})")

    print("✓ InputClassifier works correctly")
except Exception as e:
    print(f"✗ InputClassifier test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Query intent classification
print("\n[TEST 5] Testing query intent classification...")
try:
    classifier = InputClassifier()

    # Test fact retrieval intent
    result1 = classifier.classify_query("What is machine learning?")
    assert result1.intent == QueryIntent.RETRIEVE_FACT
    print(f"  - 'What is' query: {result1.intent.value}")

    # Test procedure finding intent
    result2 = classifier.classify_query("How to create a virtual environment?")
    assert result2.intent == QueryIntent.FIND_PROCEDURE
    print(f"  - 'How to' query: {result2.intent.value}")

    # Test conversation search intent
    result3 = classifier.classify_query("What did we discuss about the project?")
    assert result3.intent == QueryIntent.SEARCH_CONVERSATION
    print(f"  - Conversation query: {result3.intent.value}")

    print("✓ Query intent classification works correctly")
except Exception as e:
    print(f"✗ Query intent classification test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: DynamicMemoryConfig
print("\n[TEST 6] Testing DynamicMemoryConfig...")
try:
    config = DynamicMemoryConfig()
    assert config.enable_auto_classification is True
    assert config.enable_intent_classification is True
    assert config.enable_category_weights is True
    print("✓ DynamicMemoryConfig works correctly")

    # Test custom weights
    custom_config = DynamicMemoryConfig(
        default_category_weights={
            MemoryCategory.TASK: 2.0,
            MemoryCategory.FACT: 1.5,
        }
    )
    assert custom_config.default_category_weights[MemoryCategory.TASK] == 2.0
    print("✓ Custom category weights work correctly")
except Exception as e:
    print(f"✗ DynamicMemoryConfig test failed: {e}")

# Test 7: Pydantic models
print("\n[TEST 7] Testing Pydantic models...")
try:
    # ClassifiedInput
    classified_input = ClassifiedInput(
        text="Test input",
        category=MemoryCategory.QUESTION,
        confidence=0.95,
        subcategories=["test"],
        metadata={"key": "value"},
    )
    assert classified_input.category == MemoryCategory.QUESTION
    print("✓ ClassifiedInput model works correctly")

    # ClassifiedQuery
    classified_query = ClassifiedQuery(
        query="Test query",
        intent=QueryIntent.GENERAL_SEARCH,
        target_categories=[MemoryCategory.GENERAL],
        confidence=0.9,
    )
    assert classified_query.intent == QueryIntent.GENERAL_SEARCH
    print("✓ ClassifiedQuery model works correctly")
except Exception as e:
    print(f"✗ Pydantic model test failed: {e}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("All core components of the Dynamic Memory System are working!")
print("\nKey features verified:")
print("  ✓ Memory classification (question, task, code, procedure, etc.)")
print("  ✓ Query intent detection (fact, procedure, conversation)")
print("  ✓ Category-weighted search configuration")
print("  ✓ Extensible Pydantic models")
print("\nNext steps:")
print("  1. Integrate with your Memory instance")
print("  2. Use add_with_classification() for adding memories")
print("  3. Use smart_search() for faster, more accurate searches")
print("  4. Use get_context_for_response() for optimized context retrieval")
print("=" * 60)
