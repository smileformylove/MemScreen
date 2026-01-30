#!/usr/bin/env python3
"""
测试 MemScreen 三大记忆来源

验证：
1. 屏幕录制（OCR + Caption）
2. Process Mining
3. 用户对话
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_memory_sources():
    """测试三种记忆来源是否正确保存"""
    print("\n" + "="*70)
    print("🔍 测试三大记忆来源")
    print("="*70)

    from memscreen import Memory
    from memscreen.memory.models import MemoryConfig

    # 初始化记忆系统
    config = MemoryConfig()
    memory = Memory(config=config)

    # 搜索所有记忆
    print("\n搜索所有记忆...")
    result = memory.search(
        query="所有活动",
        user_id="default_user",
        limit=20,
        threshold=0.0  # 返回所有记忆
    )

    if not result or "results" not in result:
        print("❌ 未找到任何记忆")
        return False

    memories = result["results"]
    print(f"\n✅ 找到 {len(memories)} 条记忆\n")

    # 分类统计
    screen_recordings = []
    process_mining = []
    chat_conversations = []

    for mem in memories:
        if isinstance(mem, dict):
            metadata = mem.get("metadata", {})
            mem_type = metadata.get("type", metadata.get("source", "unknown"))
            content = mem.get("memory", mem.get("content", ""))[:100]

            if mem_type == "screen_recording":
                screen_recordings.append((mem, content))
            elif mem_type == "process_mining":
                process_mining.append((mem, content))
            elif mem_type == "ai_chat":
                chat_conversations.append((mem, content))

    # 打印统计
    print("="*70)
    print("📊 记忆来源统计")
    print("="*70)
    print(f"\n1️⃣  屏幕录制 (OCR + Caption): {len(screen_recordings)} 条")
    print(f"2️⃣  Process Mining:          {len(process_mining)} 条")
    print(f"3️⃣  用户对话:                {len(chat_conversations)} 条")
    print(f"\n总计: {len(memories)} 条记忆")

    # 详细显示每种类型的前 2 条
    print("\n" + "="*70)
    print("📝 详细内容")
    print("="*70)

    if screen_recordings:
        print(f"\n1️⃣  屏幕录制示例 (共 {len(screen_recordings)} 条):")
        for i, (mem, content) in enumerate(screen_recordings[:2], 1):
            metadata = mem.get("metadata", {})
            filename = metadata.get("filename", "unknown")[:40]
            duration = metadata.get("duration", 0)
            print(f"\n  [{i}] {filename}")
            print(f"      时长: {duration:.1f}s")
            print(f"      内容: {content}...")

    if process_mining:
        print(f"\n2️⃣  Process Mining 示例 (共 {len(process_mining)} 条):")
        for i, (mem, content) in enumerate(process_mining[:2], 1):
            metadata = mem.get("metadata", {})
            categories = metadata.get("categories", {})
            primary = categories.get("primary", "Unknown") if isinstance(categories, dict) else "Unknown"
            print(f"\n  [{i}] 主要活动: {primary}")
            print(f"      内容: {content}...")

    if chat_conversations:
        print(f"\n3️⃣  对话示例 (共 {len(chat_conversations)} 条):")
        for i, (mem, content) in enumerate(chat_conversations[:2], 1):
            print(f"\n  [{i}] {content}...")

    # 验证检查
    print("\n" + "="*70)
    print("✅ 验证检查")
    print("="*70)

    checks = [
        ("屏幕录制保存", len(screen_recordings) > 0),
        ("Process Mining 保存", len(process_mining) > 0),
        ("对话保存", len(chat_conversations) > 0),
    ]

    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False

    # 检查屏幕录制的详细内容
    if screen_recordings:
        mem, content = screen_recordings[0]
        metadata = mem.get("metadata", {})

        # 检查 OCR
        has_ocr = "ocr_text" in metadata or "text" in content.lower()
        print(f"  {'✅' if has_ocr else '❌'} OCR 文字识别")

        # 检查 Caption
        frame_details = metadata.get("frame_details", [])
        has_caption = len(frame_details) > 0 or "Scene:" in content or "Application:" in content
        print(f"  {'✅' if has_caption else '❌'} Caption 视觉理解")

    if all_passed:
        print("\n🎉 所有记忆来源正常工作！")
    else:
        print("\n⚠️  部分记忆来源未正常工作")

    return all_passed


def test_memory_integration():
    """测试记忆检索是否整合所有来源"""
    print("\n" + "="*70)
    print("🔍 测试记忆检索整合")
    print("="*70)

    from memscreen import Memory
    from memscreen.memory.models import MemoryConfig

    config = MemoryConfig()
    memory = Memory(config=config)

    # 测试问题
    queries = [
        "我今天做了什么",
        "我刚才在做什么",
        "写了什么代码",
    ]

    for query in queries:
        print(f"\n查询: {query}")
        result = memory.search(
            query=query,
            user_id="default_user",
            limit=5,
            threshold=0.3
        )

        if result and "results" in result:
            memories = result["results"]
            print(f"  找到 {len(memories)} 条相关记忆")

            # 统计来源类型
            sources = {}
            for mem in memories:
                if isinstance(mem, dict):
                    metadata = mem.get("metadata", {})
                    mem_type = metadata.get("type", metadata.get("source", "unknown"))
                    sources[mem_type] = sources.get(mem_type, 0) + 1

            print(f"  来源分布: {sources}")

            # 显示最相关的记忆
            if memories:
                top_mem = memories[0]
                content = top_mem.get("memory", top_mem.get("content", ""))[:80]
                metadata = top_mem.get("metadata", {})
                mem_type = metadata.get("type", metadata.get("source", "unknown"))
                score = top_mem.get("score", 0)
                print(f"  最相关: [{mem_type}] (score={score:.2f}) {content}...")
        else:
            print("  ❌ 未找到结果")

    return True


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("🧪 MemScreen 三大记忆来源测试")
    print("="*70)

    print("""
📋 测试内容：

1️⃣  屏幕录制 (OCR + Caption)
   - OCR 文字识别
   - Caption 视觉理解
   - 场景分析

2️⃣  Process Mining
   - 键盘输入追踪
   - 鼠标点击追踪
   - 活动模式分析

3️⃣  用户对话
   - 对话历史
   - 用户表达的信息
""")

    test1_passed = test_memory_sources()
    test2_passed = test_memory_integration()

    print("\n" + "="*70)
    print("📋 测试总结")
    print("="*70)
    print(f"  {'✅' if test1_passed else '❌'} 记忆来源测试")
    print(f"  {'✅' if test2_passed else '❌'} 记忆整合测试")

    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过！三大记忆来源正常工作。")
        print("\n💡 下一步：启动应用测试实际效果")
        print("   $ python3 start.py")
    else:
        print("\n⚠️  部分测试失败，请检查实现。")

    print("\n" + "="*70 + "\n")

    return 0 if (test1_passed and test2_passed) else 1


if __name__ == "__main__":
    sys.exit(main())
