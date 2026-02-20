#!/usr/bin/env python3
"""
 Agent  - 
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🤖  Agent  - ")
print("=" * 80)

from memscreen.memory import (
    Memory,
    MemoryConfig,
    InputClassifier,
    MemoryCategory,
    QueryIntent,
)
from memscreen.agent import IntelligentAgent, AgentConfig

#  Memory  LLM 
class MockMemory:
    """ Memory """

    def __init__(self):
        self.classifier = InputClassifier()
        self.memories = []

    def add(self, text, metadata=None):
        self.memories.append({"text": text, "metadata": metadata})
        print(f"   [Memory] : {text[:30]}...")

    def smart_search(self, query, **filters):
        return {
            "results": [
                {"id": "1", "memory": " 1", "score": 0.9},
                {"id": "2", "memory": " 2", "score": 0.8},
            ]
        }

    def get_memories_by_category(self, category, **filters):
        return {
            "results": [f" {category} "]
        }

    def add_with_classification(self, text, **filters):
        return {
            "classification": {"category": "task"},
            "memory_id": "123"
        }


class MockLLM:
    """ LLM """

    def generate_response(self, messages):
        return " LLM "


async def demo_intelligent_agent():
    """ Agent """

    #  Memory  LLM
    memory = MockMemory()
    llm = MockLLM()

    #  Agent
    agent = IntelligentAgent(
        memory_system=memory,
        llm_client=llm,
        config=AgentConfig(
            name="",
            version="2.0.0",
        ),
        enable_classification=True,
    )

    print("\n✅  Agent ")
    print(f"   - : {agent.config.name}")
    print(f"   - : {agent.config.version}")
    print(f"   - : {agent.enable_classification}")

    # 
    print("\n" + "=" * 80)
    print("📝 ")
    print("=" * 80)

    test_inputs = [
        ("", ""),
        ("", ""),
        ("3", ""),
        ("def hello(): print('hi')", ""),
        ("", ""),
        ("", ""),
    ]

    for input_text, description in test_inputs:
        print(f"\n{'=' * 60}")
        print(f": {input_text}")
        print(f": {description}")
        print('=' * 60)

        # 
        result = await agent.process_input(input_text)

        # 
        print(f"✅ ")
        print(f"   : {result.get('handler', 'unknown')}")
        print(f"   : {result.get('success', False)}")

        if result.get('data'):
            data = result['data']
            if isinstance(data, dict):
                if 'response' in data:
                    print(f"   : {data['response'][:50]}...")
                elif 'results' in data:
                    print(f"   : {len(data['results'])} ")

    # 
    print("\n" + "=" * 80)
    print("📊 ")
    print("=" * 80)

    stats = agent.get_dispatch_stats()
    print(f"\n: {stats['total_dispatches']}")
    print(f"\n:")
    for cat, count in stats['category_counts'].items():
        print(f"  - {cat}: {count} ")

    if stats['intent_counts']:
        print(f"\n:")
        for intent, count in stats['intent_counts'].items():
            print(f"  - {intent}: {count} ")


def demo_classification():
    """"""

    print("\n" + "=" * 80)
    print("🔍 ")
    print("=" * 80)

    classifier = InputClassifier()

    print("\n:")
    questions = [
        " Python",
        " Docker",
        "",
    ]
    for q in questions:
        result = classifier.classify_input(q)
        print(f"  '{q}' → {result.category.value} (: {result.confidence:.2f})")

    print("\n:")
    tasks = [
        "",
        "",
        "",
    ]
    for t in tasks:
        result = classifier.classify_input(t)
        print(f"  '{t}' → {result.category.value} (: {result.confidence:.2f})")

    print("\n:")
    codes = [
        "def main(): pass",
        "```python\nprint('hello')\n```",
        "const add = (a, b) => a + b;",
    ]
    for c in codes:
        result = classifier.classify_input(c)
        print(f"  '{c[:25]}...' → {result.category.value}")

    print("\n:")
    procedures = [
        "1\n2",
        "First, create a virtual environment. Then, install requirements.",
        "1.  2.  3. ",
    ]
    for p in procedures:
        result = classifier.classify_input(p)
        print(f"  '{p[:30]}...' → {result.category.value}")


def demo_intent_classification():
    """"""

    print("\n" + "=" * 80)
    print("🎯 ")
    print("=" * 80)

    classifier = InputClassifier()

    print("\n:")
    fact_queries = [
        "",
        " Python ",
        " REST API ",
    ]
    for q in fact_queries:
        result = classifier.classify_query(q)
        print(f"  '{q}' → {result.intent.value}")
        print(f"     : {[c.value for c in result.target_categories]}")

    print("\n:")
    procedure_queries = [
        "",
        "",
        "",
    ]
    for q in procedure_queries:
        result = classifier.classify_query(q)
        print(f"  '{q}' → {result.intent.value}")
        print(f"     : {[c.value for c in result.target_categories]}")

    print("\n:")
    conversation_queries = [
        "",
        "",
        "",
    ]
    for q in conversation_queries:
        result = classifier.classify_query(q)
        print(f"  '{q}' → {result.intent.value}")
        print(f"     : {[c.value for c in result.target_categories]}")


if __name__ == "__main__":
    # 
    demo_classification()

    # 
    demo_intent_classification()

    #  Agent
    print("\n" + "=" * 80)
    print("🚀  Agent ")
    print("=" * 80)
    asyncio.run(demo_intelligent_agent())

    print("\n" + "=" * 80)
    print("✅ ")
    print("=" * 80)

    print("""
 Agent :

1. 🎯 
   - 
   - 
   - URL 

2. 🤖 
   - 
   -  →  Memory
   -  → 
   -  → 
   -  → 

3. 📊 
   - 
   - 
   - 

4. 🔌 
   - 
   - 
   - 

:
    from memscreen.agent import IntelligentAgent
    from memscreen.memory import Memory

    #  Memory
    memory = Memory(config=MemoryConfig(enable_dynamic_memory=True))

    #  Agent
    agent = IntelligentAgent(
        memory_system=memory,
        llm_client=your_llm_client,
        enable_classification=True
    )

    # 
    result = await agent.process_input("")
""")

    print("=" * 80)
