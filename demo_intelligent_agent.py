#!/usr/bin/env python3
"""
智能 Agent 演示 - 自动判断和调度
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🤖 智能 Agent 演示 - 自动输入判断和调度")
print("=" * 80)

from memscreen.memory import (
    Memory,
    MemoryConfig,
    InputClassifier,
    MemoryCategory,
    QueryIntent,
)
from memscreen.agent import IntelligentAgent, AgentConfig

# 模拟 Memory 和 LLM 客户端
class MockMemory:
    """模拟 Memory 系统"""

    def __init__(self):
        self.classifier = InputClassifier()
        self.memories = []

    def add(self, text, metadata=None):
        self.memories.append({"text": text, "metadata": metadata})
        print(f"   [Memory] 已存储: {text[:30]}...")

    def smart_search(self, query, **filters):
        return {
            "results": [
                {"id": "1", "memory": "示例记忆 1", "score": 0.9},
                {"id": "2", "memory": "示例记忆 2", "score": 0.8},
            ]
        }

    def get_memories_by_category(self, category, **filters):
        return {
            "results": [f"类别 {category} 的记忆"]
        }

    def add_with_classification(self, text, **filters):
        return {
            "classification": {"category": "task"},
            "memory_id": "123"
        }


class MockLLM:
    """模拟 LLM 客户端"""

    def generate_response(self, messages):
        return "这是一个模拟的 LLM 响应"


async def demo_intelligent_agent():
    """演示智能 Agent 的功能"""

    # 创建 Memory 和 LLM
    memory = MockMemory()
    llm = MockLLM()

    # 创建智能 Agent
    agent = IntelligentAgent(
        memory_system=memory,
        llm_client=llm,
        config=AgentConfig(
            name="智能助手",
            version="2.0.0",
        ),
        enable_classification=True,
    )

    print("\n✅ 智能 Agent 已初始化")
    print(f"   - 名称: {agent.config.name}")
    print(f"   - 版本: {agent.config.version}")
    print(f"   - 分类功能: {agent.enable_classification}")

    # 测试不同类型的输入
    print("\n" + "=" * 80)
    print("📝 测试不同类型的输入")
    print("=" * 80)

    test_inputs = [
        ("你好！", "问候"),
        ("什么是递归？", "问题"),
        ("记得明天下午3点开会", "任务"),
        ("def hello(): print('hi')", "代码"),
        ("如何部署到服务器？", "查找步骤"),
        ("我们之前讨论过什么？", "搜索对话"),
    ]

    for input_text, description in test_inputs:
        print(f"\n{'=' * 60}")
        print(f"输入: {input_text}")
        print(f"类型: {description}")
        print('=' * 60)

        # 处理输入
        result = await agent.process_input(input_text)

        # 显示结果
        print(f"✅ 处理完成")
        print(f"   处理器: {result.get('handler', 'unknown')}")
        print(f"   成功: {result.get('success', False)}")

        if result.get('data'):
            data = result['data']
            if isinstance(data, dict):
                if 'response' in data:
                    print(f"   响应: {data['response'][:50]}...")
                elif 'results' in data:
                    print(f"   结果数: {len(data['results'])} 个记忆")

    # 显示统计信息
    print("\n" + "=" * 80)
    print("📊 调度统计")
    print("=" * 80)

    stats = agent.get_dispatch_stats()
    print(f"\n总调度次数: {stats['total_dispatches']}")
    print(f"\n类别分布:")
    for cat, count in stats['category_counts'].items():
        print(f"  - {cat}: {count} 次")

    if stats['intent_counts']:
        print(f"\n意图分布:")
        for intent, count in stats['intent_counts'].items():
            print(f"  - {intent}: {count} 次")


def demo_classification():
    """演示输入分类功能"""

    print("\n" + "=" * 80)
    print("🔍 输入分类演示")
    print("=" * 80)

    classifier = InputClassifier()

    print("\n问题类输入:")
    questions = [
        "什么是 Python？",
        "如何使用 Docker？",
        "为什么程序崩溃了？",
    ]
    for q in questions:
        result = classifier.classify_input(q)
        print(f"  '{q}' → {result.category.value} (置信度: {result.confidence:.2f})")

    print("\n任务类输入:")
    tasks = [
        "记得明天提交报告",
        "需要完成代码审查",
        "别忘了给客户打电话",
    ]
    for t in tasks:
        result = classifier.classify_input(t)
        print(f"  '{t}' → {result.category.value} (置信度: {result.confidence:.2f})")

    print("\n代码类输入:")
    codes = [
        "def main(): pass",
        "```python\nprint('hello')\n```",
        "const add = (a, b) => a + b;",
    ]
    for c in codes:
        result = classifier.classify_input(c)
        print(f"  '{c[:25]}...' → {result.category.value}")

    print("\n流程类输入:")
    procedures = [
        "步骤1：安装依赖\n步骤2：运行配置",
        "First, create a virtual environment. Then, install requirements.",
        "如何配置环境：1. 打开设置 2. 选择环境 3. 保存",
    ]
    for p in procedures:
        result = classifier.classify_input(p)
        print(f"  '{p[:30]}...' → {result.category.value}")


def demo_intent_classification():
    """演示查询意图识别"""

    print("\n" + "=" * 80)
    print("🎯 查询意图识别演示")
    print("=" * 80)

    classifier = InputClassifier()

    print("\n检索事实意图:")
    fact_queries = [
        "什么是机器学习？",
        "告诉我关于 Python 的信息",
        "解释 REST API 的概念",
    ]
    for q in fact_queries:
        result = classifier.classify_query(q)
        print(f"  '{q}' → {result.intent.value}")
        print(f"     目标类别: {[c.value for c in result.target_categories]}")

    print("\n查找步骤意图:")
    procedure_queries = [
        "如何部署应用？",
        "怎么配置虚拟环境？",
        "步骤说明：设置数据库",
    ]
    for q in procedure_queries:
        result = classifier.classify_query(q)
        print(f"  '{q}' → {result.intent.value}")
        print(f"     目标类别: {[c.value for c in result.target_categories]}")

    print("\n搜索对话意图:")
    conversation_queries = [
        "我们讨论了关于性能优化的什么内容？",
        "之前提到过关于数据库的配置吗？",
        "我们上次谈到的问题解决了吗？",
    ]
    for q in conversation_queries:
        result = classifier.classify_query(q)
        print(f"  '{q}' → {result.intent.value}")
        print(f"     目标类别: {[c.value for c in result.target_categories]}")


if __name__ == "__main__":
    # 演示分类
    demo_classification()

    # 演示意图识别
    demo_intent_classification()

    # 演示智能 Agent
    print("\n" + "=" * 80)
    print("🚀 启动智能 Agent 演示")
    print("=" * 80)
    asyncio.run(demo_intelligent_agent())

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80)

    print("""
智能 Agent 的关键特性:

1. 🎯 自动输入分类
   - 识别输入类型（问题、任务、代码、流程等）
   - 识别查询意图（检索事实、查找步骤、搜索对话等）
   - 提取元数据（优先级、语言、URL 等）

2. 🤖 智能调度
   - 根据分类自动选择处理器
   - 问题 → 搜索 Memory
   - 任务 → 添加到任务列表
   - 代码 → 代码助手
   - 流程 → 查找或执行步骤

3. 📊 自适应学习
   - 记录调度统计
   - 分析类别分布
   - 优化处理策略

4. 🔌 可扩展
   - 注册自定义类别处理器
   - 添加调度规则
   - 集成新技能

使用方法:
    from memscreen.agent import IntelligentAgent
    from memscreen.memory import Memory

    # 创建 Memory（启用动态功能）
    memory = Memory(config=MemoryConfig(enable_dynamic_memory=True))

    # 创建智能 Agent
    agent = IntelligentAgent(
        memory_system=memory,
        llm_client=your_llm_client,
        enable_classification=True
    )

    # 处理输入（自动分类和调度）
    result = await agent.process_input("记得明天开会")
""")

    print("=" * 80)
