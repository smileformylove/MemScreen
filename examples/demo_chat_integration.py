#!/usr/bin/env python3
"""
AI Chat  Agent 
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("💬 AI Chat ")
print("=" * 80)

from memscreen.memory import (
    Memory,
    MemoryConfig,
    InputClassifier,
    MemoryCategory,
)
from memscreen.agent import IntelligentAgent, AgentConfig

#  Memory  LLM
class MockMemoryWithClassification:
    def __init__(self):
        self.classifier = InputClassifier()
        self.memories = []

    def add(self, text, metadata=None):
        self.memories.append({"text": text, "metadata": metadata})
        print(f"   [Memory] ")

    def smart_search(self, query, **filters):
        return {"results": [
            {"memory": f" '{query}'  1", "score": 0.9},
            {"memory": f" '{query}'  2", "score": 0.8},
        ]}

    def add_with_classification(self, text, **filters):
        return {"classification": {"category": "task"}, "memory_id": "123"}

    def get_memories_by_category(self, category, **filters):
        return {"results": [f" {category} "]}


class MockLLMClient:
    def generate_response(self, messages, **kwargs):
        content = messages[-1].get("content", "") if messages else ""
        return f" '{content[:30]}...' "


class MockChatPresenter:
    """ ChatPresenter"""

    def __init__(self):
        self.memory = MockMemoryWithClassification()
        self.llm = MockLLMClient()

        #  Agent
        self.intelligent_agent = IntelligentAgent(
            memory_system=self.memory,
            llm_client=self.llm,
            enable_classification=True,
        )

        print("✅ ChatPresenter  Agent")

    def process_message(self, user_message: str):
        """ Agent """
        print(f"\n: {user_message}")

        #  Agent 
        result = asyncio.run(
            self.intelligent_agent.process_input(user_message)
        )

        # 
        response = self._format_response(result)
        print(f": {response}")

        # 
        print(f"   [: {result.get('handler', 'unknown')}]")

    def _format_response(self, result):
        """ Agent """
        if not result.get("success"):
            return ""

        handler = result.get("handler", "")
        data = result.get("data", {})

        if handler == "greet":
            return data.get("response", "")

        elif handler == "smart_search":
            memories = data.get("results", [])
            if memories:
                response = f" {len(memories)} \n"
                for item in memories[:3]:
                    response += f"  - {item.get('memory', '')}\n"
                return response
            return ""

        elif handler in ["manage_task", "add_task"]:
            return ""

        elif handler == "code_assistant":
            return data.get("response", "")

        else:
            return ""


def demo_chat():
    """ AI Chat """

    print("\n" + "=" * 80)
    print("💬 AI Chat ")
    print("=" * 80)

    #  ChatPresenter
    chat = MockChatPresenter()

    print("\n📝 :")
    print("=" * 60)

    #  1: 
    print("\n[ 1] ")
    chat.process_message("")

    #  2: 
    print("\n[ 2] ")
    chat.process_message("")

    #  3: 
    print("\n[ 3] ")
    chat.process_message("3")

    #  4: 
    print("\n[ 4] ")
    chat.process_message("def hello(): return 'world'")

    #  5: 
    print("\n[ 5] ")
    chat.process_message("")

    #  6: 
    print("\n[ 6] ")
    chat.process_message("")

    print("\n" + "=" * 80)


def demo_classification_in_action():
    """ Agent """

    print("\n" + "=" * 80)
    print("🔍 ")
    print("=" * 80)

    classifier = InputClassifier()

    examples = [
        ("", "task", ""),
        ("", "question", ""),
        ("def foo(): pass", "code", ""),
        ("", "question", ""),
        ("", "greeting", ""),
    ]

    print("\n →  → :")
    print("-" * 60)

    for text, expected_cat, expected_handler in examples:
        # 
        classification = classifier.classify_input(text)

        # 
        intent = classifier.classify_query(text)

        print(f"\n: {text}")
        print(f"  ↓ : {classification.category.value} (: {classification.confidence:.2f})")
        print(f"  ↓ : {intent.intent.value}")
        print(f"  ↓ : {expected_handler}")
        print(f"  ✅  if-else")


if __name__ == "__main__":
    # 
    demo_classification_in_action()

    #  Chat 
    demo_chat()

    print("\n" + "=" * 80)
    print("✅ ")
    print("=" * 80)

    print("""
 Agent  AI Chat 

:
  1. 🎯 
     -  → question
     -  → task
     -  → code
     -  → procedure
     -  → greeting

  2. 🤖 
     - 
     -  →  Memory
     -  → 
     -  → 
     -  → 

  3. 📊 
     - 3-5x 
     - 70%  tokens
     - 

  4. 🔌 
     - 
     - 
     - 

:
    from memscreen.presenters import ChatPresenter

    # ChatPresenter  Agent
    # 
    # 
""")

    print("=" * 80)
