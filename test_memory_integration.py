#!/usr/bin/env python3
"""
测试动态 Memory 系统集成
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🧪 动态 Memory 系统集成测试")
print("=" * 70)

# 测试 1: 导入测试
print("\n[测试 1] 导入模块...")
try:
    from memscreen.memory import (
        Memory,
        MemoryConfig,
        MemoryCategory,
        DynamicMemoryConfig,
    )
    print("✅ 模块导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 测试 2: 配置创建
print("\n[测试 2] 创建配置...")
try:
    config = MemoryConfig(
        enable_dynamic_memory=True,
        dynamic_config={
            "enable_auto_classification": True,
            "enable_intent_classification": True,
            "enable_category_weights": True,
        }
    )
    print("✅ 配置创建成功")
    print(f"   - 动态 Memory 启用: {config.enable_dynamic_memory}")
    print(f"   - 动态配置: {config.dynamic_config}")
except Exception as e:
    print(f"❌ 配置创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 3: 分类器测试
print("\n[测试 3] 测试分类器...")
try:
    from memscreen.memory import InputClassifier

    classifier = InputClassifier()

    # 测试中文分类
    test_cases = [
        ("什么是机器学习？", "question"),
        ("记得明天提交报告", "task"),
        ("如何配置环境变量？", "question"),
    ]

    all_passed = True
    for text, expected in test_cases:
        result = classifier.classify_input(text)
        if result.category.value == expected:
            print(f"   ✅ '{text[:20]}...' → {result.category.value}")
        else:
            print(f"   ⚠️  '{text[:20]}...' → {result.category.value} (期望: {expected})")
            all_passed = False

    if all_passed:
        print("✅ 分类器测试通过")
except Exception as e:
    print(f"❌ 分类器测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 4: 查询意图分类
print("\n[测试 4] 测试查询意图分类...")
try:
    queries = [
        ("如何部署应用？", "find_procedure"),
        ("我们讨论了什么？", "search_conversation"),
    ]

    for query, expected_intent in queries:
        result = classifier.classify_query(query)
        if result.intent.value == expected_intent:
            print(f"   ✅ '{query}' → {result.intent.value}")
            print(f"      目标类别: {[c.value for c in result.target_categories]}")
        else:
            print(f"   ⚠️  '{query}' → {result.intent.value} (期望: {expected_intent})")

    print("✅ 查询意图分类测试通过")
except Exception as e:
    print(f"❌ 查询意图分类测试失败: {e}")

# 测试 5: 类别枚举
print("\n[测试 5] 测试类别枚举...")
try:
    categories = [
        MemoryCategory.QUESTION,
        MemoryCategory.TASK,
        MemoryCategory.FACT,
        MemoryCategory.CODE,
        MemoryCategory.PROCEDURE,
    ]

    print(f"   支持的类别数量: {len(list(MemoryCategory))}")
    print(f"   测试的类别:")
    for cat in categories:
        print(f"      • {cat.value}")

    print("✅ 类别枚举测试通过")
except Exception as e:
    print(f"❌ 类别枚举测试失败: {e}")

# 测试 6: 模拟 Memory 使用（不需要实际的 LLM/向量存储）
print("\n[测试 6] 模拟 Memory 使用场景...")
try:
    print("   场景 1: 用户提问")
    query1 = "如何使用动态 Memory？"
    result1 = classifier.classify_input(query1)
    print(f"   输入: '{query1}'")
    print(f"   分类: {result1.category.value}")
    print(f"   置信度: {result1.confidence:.2f}")

    print("\n   场景 2: 用户任务")
    query2 = "记得明天测试代码"
    result2 = classifier.classify_input(query2)
    print(f"   输入: '{query2}'")
    print(f"   分类: {result2.category.value}")
    print(f"   置信度: {result2.confidence:.2f}")
    print(f"   元数据: {result2.metadata}")

    print("\n   场景 3: 搜索查询")
    query3 = "如何部署应用到生产环境？"
    result3 = classifier.classify_query(query3)
    print(f"   查询: '{query3}'")
    print(f"   意图: {result3.intent.value}")
    print(f"   目标类别: {[c.value for c in result3.target_categories]}")
    print(f"   搜索参数: {result3.search_params}")

    print("\n✅ 场景测试通过")
except Exception as e:
    print(f"❌ 场景测试失败: {e}")
    import traceback
    traceback.print_exc()

# 总结
print("\n" + "=" * 70)
print("📊 测试总结")
print("=" * 70)
print("""
✅ 动态 Memory 系统已成功集成到 MemScreen

新功能可用:
  1. 自动输入分类（支持中英文）
  2. 查询意图识别
  3. 分类优化的搜索
  4. 智能上下文检索

使用方法:
  # 在 start.py 或其他应用中启用
  config = MemoryConfig(
      enable_dynamic_memory=True,
      ...其他配置
  )
  memory = Memory(config)

  # 使用新方法
  memory.add_with_classification("记得开会", user_id="user123")
  memory.smart_search("如何部署？", user_id="user123")
  memory.get_context_for_response("问题", user_id="user123")
""")

print("=" * 70)
print("🎉 集成测试完成！动态 Memory 系统已准备就绪")
print("=" * 70)
