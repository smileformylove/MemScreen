#!/usr/bin/env python3
"""
MemScreen 优化功能演示脚本

展示所有6个阶段的新功能：
1. 视觉检索增强
2. 分层记忆管理
3. 冲突处理优化
4. 多粒度视觉记忆
5. 视觉问答优化
6. 7b模型优化
"""

import sys
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def demo_vision_encoder():
    """演示1：视觉编码器"""
    print("\n" + "="*60)
    print("🎯 阶段1：视觉编码器演示")
    print("="*60)

    from memscreen.embeddings.vision_encoder import VisionEncoder, VisionEncoderConfig

    # 创建配置
    config = VisionEncoderConfig(
        model_type="clip",  # 使用CLIP进行演示
        cache_size=10,
    )

    # 初始化编码器
    encoder = VisionEncoder(config)

    print(f"✅ 视觉编码器已初始化")
    print(f"   - 模型类型: {config.model_type}")
    print(f"   - 嵌入维度: {config.embedding_dims}")
    print(f"   - 缓存大小: {config.cache_size}")

    # 创建测试图像
    from PIL import Image
    import numpy as np

    test_img = Image.new('RGB', (100, 100), color='red')
    test_path = Path(tempfile.gettempdir()) / "test_image.png"
    test_img.save(test_path)

    print(f"\n✅ 创建测试图像: {test_path}")

    # 计算视觉哈希
    visual_hash = encoder.compute_visual_hash(str(test_path))
    print(f"\n✅ 视觉哈希: {visual_hash}")

    # 提取视觉特征
    features = encoder.extract_visual_features(str(test_path))
    print(f"\n✅ 视觉特征:")
    print(f"   - 亮度: {features['brightness']:.2f}")
    print(f"   - 对比度: {features['contrast']:.2f}")
    print(f"   - 宽高比: {features['aspect_ratio']:.2f}")
    print(f"   - 布局密度: {features['layout_density']:.2f}")
    print(f"   - 主色调: {features['dominant_colors']}")

    # 清理
    test_path.unlink()


def demo_multimodal_store():
    """演示2：多模态向量存储"""
    print("\n" + "="*60)
    print("🎯 阶段2：多模态向量存储演示")
    print("="*60)

    from memscreen.vector_store.multimodal_chroma import MultimodalChromaDB

    # 创建临时数据库
    import tempfile
    db_path = tempfile.mkdtemp()

    # 初始化存储
    store = MultimodalChromaDB(
        collection_name="demo_multimodal",
        text_embedding_dims=512,
        vision_embedding_dims=768,
        path=db_path,
    )

    print(f"✅ 多模态向量存储已初始化")
    print(f"   - 文本向量维度: 512")
    print(f"   - 视觉向量维度: 768")
    print(f"   - 数据库路径: {db_path}")

    # 插入数据
    ids = ["mem1", "mem2", "mem3"]
    text_embeddings = [[0.1] * 512, [0.2] * 512, [0.3] * 512]
    vision_embeddings = [[0.15] * 768, [0.25] * 768, [0.35] * 768]
    payloads = [
        {"content": "编程界面", "category": "coding"},
        {"content": "浏览器", "category": "browsing"},
        {"content": "文档编辑", "category": "document"},
    ]

    store.insert_multimodal(
        ids=ids,
        text_embeddings=text_embeddings,
        vision_embeddings=vision_embeddings,
        payloads=payloads,
    )

    print(f"\n✅ 插入了 {len(ids)} 条多模态记忆")

    # 混合搜索
    query_text = [0.2] * 512
    query_vision = [0.25] * 768

    results = store.search_hybrid(
        query_text_embedding=query_text,
        query_vision_embedding=query_vision,
        limit=2,
    )

    print(f"\n✅ 混合搜索返回 {len(results)} 条结果")
    for i, r in enumerate(results, 1):
        if r.payload:
            print(f"   {i}. {r.payload.get('content', 'N/A')} (score={r.score:.3f})")

    # 获取统计
    stats = store.get_stats()
    print(f"\n✅ 存储统计:")
    print(f"   - 文本记忆: {stats['text_count']}")
    print(f"   - 视觉记忆: {stats['vision_count']}")
    print(f"   - 总记忆数: {stats['total_count']}")

    # 清理
    store.reset()
    import shutil
    shutil.rmtree(db_path)


def demo_importance_scorer():
    """演示3：重要性评分器"""
    print("\n" + "="*60)
    print("🎯 阶段3：重要性评分演示")
    print("="*60)

    from memscreen.memory.importance_scorer import ImportanceScorer

    scorer = ImportanceScorer()

    print(f"✅ 重要性评分器已初始化")

    # 评分示例
    memories = [
        {
            "content": "Python是一种编程语言",
            "metadata": {"category": "fact"},
            "access_count": 10,
            "created_at": __import__('datetime').datetime.now(),
        },
        {
            "content": "嗨",
            "metadata": {"category": "greeting"},
            "access_count": 1,
            "created_at": __import__('datetime').datetime.now(),
        },
    ]

    for i, mem in enumerate(memories, 1):
        score = scorer.score_memory(
            content=mem["content"],
            metadata=mem["metadata"],
            access_count=mem["access_count"],
            created_at=mem["created_at"],
        )
        tier = scorer.get_tier_for_score(score)
        print(f"\n✅ 记忆{i}:")
        print(f"   - 内容: {mem['content']}")
        print(f"   - 类别: {mem['metadata']['category']}")
        print(f"   - 访问次数: {mem['access_count']}")
        print(f"   - 重要性分数: {score:.3f}")
        print(f"   - 记忆层级: {tier}")


def demo_conflict_resolver():
    """演示4：冲突解决器"""
    print("\n" + "="*60)
    print("🎯 阶段4：冲突检测演示")
    print("="*60)

    import hashlib
    import json

    # 创建模拟嵌入模型和LLM
    class MockEmbedder:
        def embed(self, text, action):
            # 返回固定向量用于演示
            return [0.1] * 512

    class MockLLM:
        def generate_response(self, messages, **kwargs):
            # 返回模拟冲突分析
            import json
            return json.dumps({
                "type": "equivalent",
                "confidence": 0.9,
                "reasoning": "Similar meaning",
                "suggestion": "skip"
            })

    from memscreen.memory.conflict_resolver import ConflictResolver

    resolver = ConflictResolver(
        embedding_model=MockEmbedder(),
        llm=MockLLM(),
    )

    print(f"✅ 冲突解决器已初始化")

    # 冲突检测示例
    new_memory = "Python是一种编程语言"
    existing_memories = [
        {
            "id": "mem1",
            "data": "Python is a programming language",
            "hash": hashlib.md5("Python is a programming language".encode()).hexdigest(),
            "embedding": [0.1] * 512,
        },
        {
            "id": "mem2",
            "data": "JavaScript is a programming language",
            "embedding": [0.2] * 512,
        },
    ]

    import hashlib
    conflicts = resolver.detect_conflict(new_memory, existing_memories)

    print(f"\n✅ 检测到 {len(conflicts)} 个冲突")

    for conflict in conflicts:
        print(f"\n   冲突类型: {conflict['conflict_type']}")
        print(f"   置信度: {conflict['confidence']:.2f}")
        print(f"   建议操作: {conflict['resolution']}")

        # 解决冲突
        resolution = resolver.resolve_conflict(conflict, new_memory)
        print(f"   解决动作: {resolution['action']}")
        print(f"   原因: {resolution['reason']}")


def demo_tiered_memory():
    """演示5：分层记忆管理"""
    print("\n" + "="*60)
    print("🎯 阶段5：分层记忆管理演示")
    print("="*60)

    from memscreen.memory.tiered_memory_manager import TieredMemoryManager, TieredMemoryConfig

    # 创建模拟组件
    class MockEmbedder:
        def embed(self, text, action):
            return [0.1] * 512

    class MockLLM:
        def generate_response(self, messages, **kwargs):
            return "Summary"

    # 创建临时存储
    import tempfile
    db_path = tempfile.mkdtemp()

    config = TieredMemoryConfig(
        enable_working_memory=False,  # 第一阶段禁用
        short_term_days=7,
    )

    manager = TieredMemoryManager(
        vector_store=None,  # 演示不需要实际存储
        embedding_model=MockEmbedder(),
        llm=MockLLM(),
        config=config,
    )

    print(f"✅ 分层记忆管理器已初始化")
    print(f"   - Working Memory: {'启用' if config.enable_working_memory else '禁用'}")
    print(f"   - Short-term: {config.short_term_days}天")
    print(f"   - 容量: {config.working_capacity}/{config.short_term_capacity}")

    # 重要性评分示例
    from datetime import datetime

    scores = [
        (0.8, "重要代码片段"),
        (0.5, "普通对话"),
        (0.3, "旧的笔记"),
    ]

    print(f"\n✅ 记忆层级分配:")
    for score, desc in scores:
        tier = manager.scorer.get_tier_for_score(score)
        print(f"   - 分数 {score:.1f}: {desc} → {tier}")


def demo_vision_qa():
    """演示6：视觉问答优化"""
    print("\n" + "="*60)
    print("🎯 阶段6：视觉问答优化演示")
    print("="*60)

    # 直接导入避免与prompts.py冲突
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "vision_qa_prompts",
        Path(__file__).parent / "memscreen" / "prompts" / "vision_qa_prompts.py"
    )
    vision_qa_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vision_qa_module)

    VisionQAPromptBuilder = vision_qa_module.VisionQAPromptBuilder
    builder = VisionQAPromptBuilder()

    print(f"✅ 视觉问答Prompt构建器已初始化")

    # 模拟视觉上下文
    visual_context = [
        {
            "description": "用户在VSCode中编写Python代码",
            "timestamp": "2026-02-06T10:30:00",
            "granularity": "scene",
            "score": 0.9,
            "scene_type": "coding",
        },
        {
            "description": "浏览器显示技术文档",
            "timestamp": "2026-02-06T10:25:00",
            "granularity": "scene",
            "score": 0.7,
            "scene_type": "browsing",
        },
    ]

    # 测试不同查询类型
    queries = [
        "红色按钮在哪里？",
        "屏幕上有什么内容？",
        "用户在做什么？",
    ]

    for query in queries:
        query_type = builder._classify_query_type(query)
        print(f"\n✅ 查询: {query}")
        print(f"   - 查询类型: {query_type}")

    # 构建Prompt
    messages = builder.build_prompt_for_7b(
        query="红色按钮在哪里？",
        visual_context=visual_context,
        conversation_history=[],
    )

    print(f"\n✅ 生成的Prompt消息数: {len(messages)}")
    print(f"   - 系统提示长度: {len(messages[0]['content'])} 字符")
    if len(messages) > 1:
        print(f"   - 用户上下文长度: {len(messages[1]['content'])} 字符")


def demo_context_optimizer():
    """演示7：上下文优化器"""
    print("\n" + "="*60)
    print("🎯 阶段7：7b模型上下文优化演示")
    print("="*60)

    from memscreen.memory.vision_context_optimizer import VisionContextOptimizer

    optimizer = VisionContextOptimizer()

    print(f"✅ 视觉上下文优化器已初始化")

    # 创建模拟视觉记忆
    from datetime import datetime, timedelta

    now = datetime.now()
    visual_memories = [
        {
            "description": "最近的编程界面" * 10,  # 长描述
            "timestamp": (now - timedelta(minutes=5)).isoformat(),
            "score": 0.9,
            "created_at": (now - timedelta(minutes=5)).isoformat(),
        },
        {
            "description": "较旧的文档" * 10,
            "timestamp": (now - timedelta(days=2)).isoformat(),
            "score": 0.7,
            "created_at": (now - timedelta(days=2)).isoformat(),
        },
        {
            "description": "很旧的对话" * 10,
            "timestamp": (now - timedelta(days=10)).isoformat(),
            "score": 0.5,
            "created_at": (now - timedelta(days=10)).isoformat(),
        },
    ]

    print(f"\n✅ 原始上下文: {len(visual_memories)} 条记忆")

    # 优化上下文
    optimized = optimizer.optimize_context_for_7b(
        visual_memories=visual_memories,
        query="编程界面",
        max_tokens=1000,  # 较小的限制用于演示
    )

    print(f"✅ 优化后上下文: {len(optimized)} 条记忆")

    for i, mem in enumerate(optimized, 1):
        original_len = len(mem.get('description', ''))
        compressed_len = len(mem.get('description', ''))
        print(f"   {i}. 压缩: {original_len} → {compressed_len} 字符")


def main():
    """运行所有演示"""
    print("\n" + "="*60)
    print("🚀 MemScreen 优化功能演示")
    print("="*60)
    print("\n将依次演示所有6个阶段的新功能...\n")

    try:
        demo_vision_encoder()
        demo_multimodal_store()
        demo_importance_scorer()
        demo_conflict_resolver()
        demo_tiered_memory()
        demo_vision_qa()
        demo_context_optimizer()

        print("\n" + "="*60)
        print("✅ 所有演示完成！")
        print("="*60)
        print("\n主要特性：")
        print("  ✅ SigLIP/CLIP 视觉编码")
        print("  ✅ 多模态向量存储")
        print("  ✅ 分层记忆管理")
        print("  ✅ 智能冲突检测")
        print("  ✅ 多粒度视觉记忆")
        print("  ✅ 视觉问答优化")
        print("  ✅ 7b模型优化")
        print("\n详细文档: .claude/plans/IMPLEMENTATION_SUMMARY.md")
        print()

    except Exception as e:
        print(f"\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
