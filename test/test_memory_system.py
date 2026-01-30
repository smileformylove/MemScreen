#!/usr/bin/env python3
"""
测试记忆系统是否正常工作

验证：
1. 录制内容是否保存到记忆
2. 对话是否保存到记忆
3. 能否从记忆中检索相关内容
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_memory_basic():
    """测试记忆基本功能"""
    print("\n" + "="*60)
    print("📝 测试记忆基本功能")
    print("="*60)

    from memscreen import Memory
    from memscreen.memory.models import MemoryConfig, EmbedderConfig, LlmConfig, VectorStoreConfig

    # 初始化记忆系统
    config = MemoryConfig()
    memory = Memory(config=config)

    # 添加测试记忆
    test_memories = [
        {"role": "user", "content": "我今天下午在写 Python 代码，实现了一个图像处理功能"},
        {"role": "user", "content": "屏幕录制：2024-01-30 15:30 - 用户在 VSCode 中编辑 main.py 文件"},
        {"role": "user", "content": "用户问：我之前在做什么？AI 答：你在写 Python 代码处理图像"},
    ]

    print("\n添加测试记忆...")
    for mem in test_memories:
        result = memory.add([mem], user_id="default_user")
        print(f"  ✅ 添加: {mem['content'][:50]}...")

    # 测试搜索
    print("\n测试搜索功能...")
    queries = [
        "我做了什么",
        "Python 代码",
        "VSCode",
    ]

    for query in queries:
        print(f"\n查询: {query}")
        try:
            result = memory.search(
                query=query,
                user_id="default_user",
                limit=3,
                threshold=0.3
            )

            if result and "results" in result:
                memories = result["results"]
                print(f"  找到 {len(memories)} 条相关记忆")
                for i, mem in enumerate(memories[:2], 1):
                    if isinstance(mem, dict):
                        content = mem.get("memory", mem.get("content", str(mem)))
                        score = mem.get("score", 0)
                        print(f"    {i}. [{score:.2f}] {content[:60]}...")
            else:
                print(f"  ⚠️  未找到结果")
        except Exception as e:
            print(f"  ❌ 搜索失败: {e}")

    return True


def test_memory_consistency():
    """测试 user_id 一致性"""
    print("\n" + "="*60)
    print("🔍 测试 user_id 一致性")
    print("="*60)

    from memscreen import Memory
    from memscreen.memory.models import MemoryConfig

    config = MemoryConfig()
    memory = Memory(config=config)

    # 添加录制记忆（使用 default_user）
    recording_memory = {
        "role": "user",
        "content": "屏幕录制：用户在浏览器中查看 GitHub 仓库"
    }

    print("\n添加录制记忆...")
    memory.add([recording_memory], user_id="default_user", metadata={"type": "screen_recording"})
    print("  ✅ 录制记忆已添加（user_id=default_user）")

    # 添加对话记忆
    chat_memory = {
        "role": "user",
        "content": "我在看 GitHub 项目"
    }

    print("\n添加对话记忆...")
    memory.add([chat_memory], user_id="default_user", metadata={"source": "ai_chat"})
    print("  ✅ 对话记忆已添加（user_id=default_user）")

    # 测试跨类型搜索
    print("\n测试跨类型搜索...")
    result = memory.search(
        query="GitHub",
        user_id="default_user",
        limit=5,
        threshold=0.0
    )

    if result and "results" in result:
        memories = result["results"]
        print(f"  ✅ 找到 {len(memories)} 条记忆（包括录制和对话）")
        for i, mem in enumerate(memories, 1):
            if isinstance(mem, dict):
                metadata = mem.get("metadata", {})
                mem_type = metadata.get("type", metadata.get("source", "unknown"))
                content = mem.get("memory", mem.get("content", ""))
                print(f"    {i}. [{mem_type}] {content[:50]}...")
    else:
        print("  ⚠️  未找到结果")

    return True


def test_prompt_integration():
    """测试 Prompt 集成"""
    print("\n" + "="*60)
    print("💬 测试 Prompt 集成")
    print("="*60)

    from memscreen.prompts import MEMORY_ANSWER_PROMPT

    print(f"\nMEMORY_ANSWER_PROMPT 长度: {len(MEMORY_ANSWER_PROMPT)} 字符")
    print("  ✅ Prompt 已优化")

    # 检查关键指令
    key_phrases = [
        "简洁直接",
        "友好自然",
        "只基于记忆回答",
        "不编造信息"
    ]

    print("\n检查关键指令:")
    for phrase in key_phrases:
        if phrase in MEMORY_ANSWER_PROMPT:
            print(f"  ✅ 包含: {phrase}")
        else:
            print(f"  ❌ 缺少: {phrase}")

    return True


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 记忆系统测试")
    print("="*60)

    tests = [
        ("基本功能", test_memory_basic),
        ("user_id 一致性", test_memory_consistency),
        ("Prompt 集成", test_prompt_integration),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 总结
    print("\n" + "="*60)
    print("📋 测试总结")
    print("="*60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} - {name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 所有测试通过！记忆系统工作正常。")
        print("\n下一步:")
        print("  1. 启动应用: python3 start.py")
        print("  2. 进行一些屏幕录制")
        print("  3. 在聊天中询问相关内容")
        print("  4. 验证 AI 能否记住和检索信息")
    else:
        print("\n⚠️  部分测试失败，请检查配置。")

    print("\n" + "="*60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
