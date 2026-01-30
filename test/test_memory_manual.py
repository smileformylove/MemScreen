#!/usr/bin/env python3
"""
手动测试记忆系统功能

按照以下步骤测试：
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_memory_search():
    """测试记忆搜索功能"""
    print("\n" + "="*60)
    print("🔍 测试记忆搜索")
    print("="*60)

    from memscreen import Memory
    from memscreen.memory.models import MemoryConfig

    try:
        # 初始化记忆系统
        config = MemoryConfig()
        memory = Memory(config=config)

        # 测试搜索
        print("\n1. 测试搜索所有记忆...")
        result = memory.search(
            query="屏幕",
            user_id="default_user",
            limit=10,
            threshold=0.0  # 低阈值以显示所有记忆
        )

        if result and "results" in result:
            memories = result["results"]
            print(f"   ✅ 找到 {len(memories)} 条记忆")

            for i, mem in enumerate(memories[:5], 1):
                if isinstance(mem, dict):
                    content = mem.get("memory", mem.get("content", str(mem)))
                    metadata = mem.get("metadata", {})
                    mem_type = metadata.get("type", metadata.get("source", "unknown"))
                    score = mem.get("score", 0)

                    # 截断过长的内容
                    if len(content) > 100:
                        content = content[:100] + "..."

                    print(f"\n   记忆 {i}:")
                    print(f"     类型: {mem_type}")
                    print(f"     相关性: {score:.2f}")
                    print(f"     内容: {content}")
        else:
            print("   ⚠️  未找到任何记忆")
            print("   💡 提示：请先进行一些屏幕录制或对话，然后再测试搜索")

        print("\n" + "="*60)
        print("测试完成！")
        print("="*60)

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_test_instructions():
    """显示测试步骤"""
    print("\n" + "="*60)
    print("📋 MemScreen 记忆系统测试指南")
    print("="*60)

    print("""
## 测试步骤

### 1️⃣ 录制屏幕内容
   a) 点击 "Recording" 标签
   b) 点击 "Start Recording" 按钮
   c) 在屏幕上做一些操作（打开文件、编辑代码等）
   d) 点击 "Stop Recording"

   ✅ 预期：控制台显示 "[RecordingPresenter] ✅ Successfully added to memory"

### 2️⃣ 进行对话
   a) 点击 "AI Chat" 标签
   b) 输入："我刚才在做什么？"
   c) 等待 AI 回复

   ✅ 预期：AI 应该能够回答你刚才录制的内容
   ✅ 预期：控制台显示 "[Chat] Found X relevant memories"

### 3️⃣ 测试连续对话
   输入以下问题测试：
   - "我在写什么代码？"
   - "用的是哪个编辑器？"
   - "今天做了什么？"

   ✅ 预期：AI 应该能够记住之前的对话和录制内容

### 4️⃣ 测试自动保存
   每次对话后，对话应该自动保存到记忆系统

   ✅ 预期：控制台显示 "[Chat] Saved conversation to memory"

## 检查记忆是否正常工作

运行此脚本查看所有记忆：
   python3 test/test_memory_manual.py

## 常见问题

### Q: AI 说"没有找到相关记录"
A: 确保已经完成了屏幕录制，并且等待几秒让录制保存完成

### Q: 控制台显示 "Found 0 relevant memories"
A: 尝试使用更通用的关键词，如"屏幕"、"录制"、"代码"等

### Q: AI 不记得之前的对话
A: 检查控制台是否有 "Saved conversation to memory" 消息

## 成功标志

✅ 录制后能保存到记忆系统
✅ 对话后能自动保存
✅ AI 能检索到相关记忆
✅ AI 使用友好的中文回复
✅ 回复简洁直接（1-2句话）

""")

    print("="*60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="测试 MemScreen 记忆系统")
    parser.add_argument("--test", action="store_true", help="执行记忆搜索测试")
    parser.add_argument("--guide", action="store_true", help="显示测试指南")

    args = parser.parse_args()

    if args.guide:
        show_test_instructions()
    elif args.test:
        test_memory_search()
    else:
        # 默认显示指南
        show_test_instructions()
        print("\n💡 提示：使用 --test 参数执行记忆搜索测试")
        print("   或者使用 --guide 参数重新显示此指南")
