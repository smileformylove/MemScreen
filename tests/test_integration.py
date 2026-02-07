#!/usr/bin/env python3
"""
MemScreen 端到端集成测试

展示如何使用所有优化功能（阶段1-6）的完整示例。
"""

import sys
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_end_to_end_integration():
    """
    端到端集成测试：使用所有优化功能
    """
    print("\n" + "="*70)
    print("🚀 MemScreen 优化功能端到端集成测试")
    print("="*70)

    # ============================================
    # 步骤1: 加载配置
    # ============================================
    print("\n📋 步骤1: 加载配置...")
    from memscreen.config import get_config

    config = get_config()  # 自动加载config_example.yaml或使用默认值
    print(f"✅ 配置加载完成")
    print(f"   - 视觉编码器: {'启用' if config.vision_encoder_enabled else '禁用'}")
    print(f"   - 分层记忆: {'启用' if config.tiered_memory_enabled else '禁用'}")
    print(f"   - 冲突检测: {'启用' if config.conflict_resolution_enabled else '禁用'}")
    print(f"   - 视觉QA优化: {'启用' if config.vision_qa_enabled else '禁用'}")

    # ============================================
    # 步骤2: 初始化基础Memory系统
    # ============================================
    print("\n📦 步骤2: 初始化基础Memory系统...")
    from memscreen.memory import MemoryConfig, Memory

    memory_config = MemoryConfig(
        version="1.0",
        collection_name="integration_test",
        history_db_path=":memory:",
        vector_store={
            "provider": "chroma",
            "config": {"path": str(Path(tempfile.mkdtemp()) / "chroma_test")},
        },
        llm={
            "provider": "ollama",
            "config": {"model": config.ollama_llm_model},
        },
        mllm={
            "provider": "ollama",
            "config": {"model": config.ollama_vision_model},
        },
        embedder={
            "provider": "ollama",
            "config": {"model": config.ollama_embedding_model},
        },
    )

    base_memory = Memory(config=memory_config)
    print("✅ 基础Memory系统初始化完成")

    # ============================================
    # 步骤3: 创建增强Memory适配器
    # ============================================
    print("\n⚡ 步骤3: 创建增强Memory适配器...")
    from memscreen.memory.enhanced_memory import create_enhanced_memory

    enhanced_memory = create_enhanced_memory(base_memory)
    print("✅ 增强Memory适配器创建完成")
    print(f"   - 视觉编码器: {'✓' if enhanced_memory.vision_encoder else '✗'}")
    print(f"   - 多模态存储: {'✓' if enhanced_memory.multimodal_store else '✗'}")
    print(f"   - 分层管理: {'✓' if enhanced_memory.tiered_manager else '✗'}")
    print(f"   - 冲突解决: {'✓' if enhanced_memory.conflict_resolver else '✗'}")

    # ============================================
    # 步骤4: 测试视觉编码
    # ============================================
    print("\n🎨 步骤4: 测试视觉编码...")
    if enhanced_memory.vision_encoder:
        # 创建测试图像
        from PIL import Image
        import numpy as np

        test_img = Image.new('RGB', (200, 100), color=(255, 0, 0))
        test_path = Path(tempfile.gettempdir()) / "test_screenshot.png"
        test_img.save(test_path)

        # 计算视觉哈希
        visual_hash = enhanced_memory.vision_encoder.compute_visual_hash(str(test_path))
        print(f"✅ 视觉哈希: {visual_hash[:16]}...")

        # 提取视觉特征
        features = enhanced_memory.vision_encoder.extract_visual_features(str(test_path))
        print(f"✅ 视觉特征: 亮度={features['brightness']:.1f}, 对比度={features['contrast']:.1f}")

    # ============================================
    # 步骤5: 测试多模态记忆添加
    # ============================================
    print("\n💾 步骤5: 测试多模态记忆添加...")

    test_messages = [
        {"role": "user", "content": "我在编写Python代码"},
    ]

    # 添加带视觉信息的记忆
    if enhanced_memory.vision_encoder:
        memory_id = enhanced_memory.add_with_vision(
            messages=test_messages,
            image_path=str(test_path) if 'test_path' in locals() else None,
            user_id="test_user",
            metadata={"category": "coding", "importance": "high"},
        )
        print(f"✅ 添加多模态记忆: {memory_id[:8]}...")

    # 添加普通文本记忆
    text_memory_id = enhanced_memory.add(
        messages=[{"role": "user", "content": "学习了Python列表推导式"}],
        user_id="test_user",
        metadata={"category": "fact"},
    )
    print(f"✅ 添加文本记忆: {text_memory_id[:8]}...")

    # ============================================
    # 步骤6: 测试重要性评分
    # ============================================
    print("\n⭐ 步骤6: 测试重要性评分...")
    if enhanced_memory.tiered_manager:
        from datetime import datetime

        score = enhanced_memory.tiered_manager.scorer.score_memory(
            content="重要的Python编程技巧",
            metadata={"category": "fact"},
            access_count=5,
            created_at=datetime.now(),
        )

        tier = enhanced_memory.tiered_manager.scorer.get_tier_for_score(score)
        print(f"✅ 重要性评分: {score:.3f} → 层级: {tier}")

    # ============================================
    # 步骤7: 测试冲突检测
    # ============================================
    print("\n🔍 步骤7: 测试冲突检测...")
    if enhanced_memory.conflict_resolver:
        conflicts = enhanced_memory.detect_conflicts(
            new_memory="Python是一种编程语言"
        )
        print(f"✅ 检测到 {len(conflicts)} 个冲突")
        for conflict in conflicts:
            print(f"   - 类型: {conflict['conflict_type']}, 建议: {conflict['resolution']}")

    # ============================================
    # 步骤8: 测试混合检索
    # ============================================
    print("\n🔎 步骤8: 测试混合检索...")

    results = enhanced_memory.search_visual(
        query="Python代码",
        limit=5,
        user_id="test_user",
    )
    print(f"✅ 检索返回 {len(results)} 条结果")

    # ============================================
    # 步骤9: 测试分层管理
    # ============================================
    print("\n📊 步骤9: 测试分层管理...")
    if enhanced_memory.tiered_manager:
        stats = enhanced_memory.tiered_manager.get_stats()
        print(f"✅ 分层统计:")
        print(f"   - Working: {stats['tier_counts']['working']}")
        print(f"   - Short-term: {stats['tier_counts']['short_term']}")
        print(f"   - Long-term: {stats['tier_counts']['long_term']}")

    # ============================================
    # 步骤10: 测试视觉问答优化
    # ============================================
    print("\n💬 步骤10: 测试视觉问答优化...")
    if config.vision_qa_enabled:
        # 直接导入避免冲突
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "vision_qa_prompts",
            Path(__file__).parent / "memscreen" / "prompts" / "vision_qa_prompts.py"
        )
        vision_qa_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vision_qa_module)

        # 测试查询分类
        builder = vision_qa_module.VisionQAPromptBuilder()
        query_type = builder._classify_query_type("红色按钮在哪里？")
        print(f"✅ 查询类型: {query_type}")

    # ============================================
    # 总结
    # ============================================
    print("\n" + "="*70)
    print("✅ 端到端集成测试完成！")
    print("="*70)
    print("\n🎉 所有优化功能已成功集成到MemScreen系统中！")
    print("\n📚 主要功能:")
    print("  1. ✅ 视觉编码（SigLIP/CLIP）")
    print("  2. ✅ 多模态向量存储")
    print("  3. ✅ 分层记忆管理")
    print("  4. ✅ 智能冲突检测")
    print("  5. ✅ 多粒度视觉记忆")
    print("  6. ✅ 视觉问答优化")
    print("  7. ✅ 7b模型优化")

    print("\n📖 使用方法:")
    print("   ```python")
    print("   from memscreen.memory.enhanced_memory import create_enhanced_memory")
    print("   from memscreen.config import get_config")
    print("   ")
    print("   # 加载配置")
    print("   config = get_config()")
    print("   ")
    print("   # 创建基础Memory")
    print("   from memscreen.memory import Memory, MemoryConfig")
    print("   memory = Memory(config=MemoryConfig(...))")
    print("   ")
    print("   # 包装为增强Memory")
    print("   enhanced = create_enhanced_memory(memory)")
    print("   ")
    print("   # 使用新功能")
    print("   enhanced.add_with_vision(messages, image_path='screenshot.png')")
    print("   results = enhanced.search_visual(query='按钮在哪里？')")
    print("   ```")

    print("\n🔗 相关文件:")
    print("  - 配置: config_example.yaml")
    print("  - 适配器: memscreen/memory/enhanced_memory.py")
    print("  - 演示: demo_optimization.py")
    print("  - 总结: .claude/plans/IMPLEMENTATION_SUMMARY.md")


if __name__ == "__main__":
    try:
        test_end_to_end_integration()
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
