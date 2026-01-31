#!/usr/bin/env python3
"""
Test script to demonstrate intelligent model routing.
"""

from memscreen.llm.model_router import get_router, ComplexityAnalyzer, ModelTier

def test_routing():
    """Test the intelligent routing system."""
    print("=" * 70)
    print("🧠 Intelligent Model Routing Test")
    print("=" * 70)
    print()

    # Sample available models
    available_models = [
        "gemma2:2b",         # Tiny
        "qwen2.5vl:3b",      # Small
        "llama3.2:3b",       # Small
        "qwen2:7b",          # Medium
        "gemma2:9b",         # Medium
        "qwen2.5:14b",       # Large
    ]

    # Create router
    router = get_router(available_models)

    # Test queries of different complexity levels
    test_queries = [
        # Greetings - should route to TINY tier
        ("你好", "Simple greeting"),
        ("Hi there!", "Simple greeting in English"),
        ("嗨！", "Casual greeting"),

        # Simple questions - should route to SMALL tier
        ("今天天气怎么样？", "Simple question"),
        ("什么是 Python？", "Factual question"),
        ("几点了？", "Time query"),

        # Conversational - should route to SMALL tier
        ("你觉得怎么样？", "Opinion question"),
        ("可以帮助我吗？", "Help request"),

        # Complex reasoning - should route to MEDIUM tier
        ("为什么我的程序运行慢？分析可能的原因", "Reasoning task"),
        ("总结一下今天的工作内容", "Summary task"),
        ("对比两种方法的优缺点", "Comparison task"),

        # Creative - should route to MEDIUM tier
        ("帮我写一封邮件", "Creative task"),
        ("创作一个故事", "Creative writing"),

        # Very complex - should route to LARGE tier
        ("分析整个系统的架构设计，找出性能瓶颈并提供优化建议", "Complex analysis"),
        ("深入研究这个问题的根本原因，并给出长期解决方案", "Deep reasoning"),
    ]

    print("Testing intelligent model routing:")
    print("-" * 70)
    print()

    for query, description in test_queries:
        # Get route
        model, config = router.route(query)
        analysis = router.analyzer.analyze(query)

        print(f"📝 Query: {query}")
        print(f"   Type: {description}")
        print(f"   → Selected Model: {model}")
        print(f"   → Tier: {config.tier.value}")
        print(f"   → Complexity Score: {analysis.complexity_score:.2f}/1.0")
        print(f"   → Est. Latency: {config.avg_latency_ms}ms")
        print(f"   → Quality Score: {config.quality_score:.2f}")
        print()

    print("=" * 70)
    print("✅ Routing test completed!")
    print("=" * 70)
    print()

    # Show tier distribution
    print("Model Tier Distribution:")
    print("-" * 70)
    for tier in [ModelTier.TINY, ModelTier.SMALL, ModelTier.MEDIUM, ModelTier.LARGE]:
        models = router.tier_models.get(tier, [])
        print(f"{tier.value.upper():8} tier: {len(models)} models")
        for model in models:
            config = router.model_configs.get(model)
            if config:
                print(f"           - {model:25} (quality: {config.quality_score:.2f}, latency: {config.avg_latency_ms}ms)")
        print()

    print()
    print("💡 Key Benefits:")
    print("  • Fast responses for simple queries (270M-1B models)")
    print("  • Balanced performance for daily tasks (1B-3B models)")
    print("  • High quality for complex questions (3B-7B models)")
    print("  • Best-in-class for reasoning tasks (7B+ models)")
    print("  • Automatic selection - no manual switching needed!")
    print()


def test_query_analysis():
    """Test the complexity analyzer."""
    print("=" * 70)
    print("🔍 Query Complexity Analysis")
    print("=" * 70)
    print()

    analyzer = ComplexityAnalyzer()

    test_cases = [
        ("你好！", "Simple greeting"),
        ("昨天我看到一个有趣的视频，里面讲到了人工智能的发展历程。", "Contextual statement"),
        ("为什么我的代码运行这么慢？请分析可能的原因并提供解决方案。", "Complex reasoning"),
        ("帮我写一首关于春天的诗", "Creative task"),
        ("请搜索所有包含'Python'的文件", "Command"),
        ("什么是API？", "Factual question"),
        ("对比一下 Python 和 JavaScript 的优缺点", "Comparison task"),
    ]

    for query, description in test_cases:
        analysis = analyzer.analyze(query)

        print(f"Query: {query}")
        print(f"Type: {description}")
        print(f"Complexity: {analysis.complexity_score:.2f}/1.0")
        print(f"Tier: {analysis.tier.value}")
        print(f"Characteristics:")
        print(f"  - Greeting: {analysis.is_greeting}")
        print(f"  - Question: {analysis.is_question}")
        print(f"  - Command: {analysis.is_command}")
        print(f"  - Conversational: {analysis.is_conversational}")
        print(f"  - Reasoning required: {analysis.reasoning_required}")
        print(f"  - Creative required: {analysis.creative_required}")
        print(f"  - Factual required: {analysis.factual_required}")
        print(f"  - Keywords: {', '.join(analysis.keywords)}")
        print(f"  - Est. tokens: {analysis.estimated_tokens:.0f}")
        print("-" * 70)
        print()


if __name__ == "__main__":
    print("\n🚀 MemScreen Intelligent Model Routing Demo")
    print("Testing smart model selection based on query complexity...\n")

    try:
        # Test routing
        test_routing()

        # Test analysis
        test_query_analysis()

        print("=" * 70)
        print("✅ All tests completed successfully!")
        print("=" * 70)
        print()
        print("📊 Summary:")
        print("  The intelligent routing system automatically selects the best model")
        print("  based on query complexity, ensuring fast yet high-quality responses.")
        print()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
