#!/usr/bin/env python3
"""
Quick demo of the intelligent chat routing system.
"""

from memscreen.llm.model_router import get_router

def demo_routing():
    """Demonstrate intelligent model routing."""
    print("\n" + "=" * 70)
    print("🧠 MemScreen 智能模型路由演示")
    print("=" * 70)
    print()
    print("📦 可用模型配置:")
    print("  TINY:   gemma2:2b (2B参数, 80ms延迟)")
    print("  SMALL:  qwen2.5vl:3b (3B参数, 150ms延迟)")
    print("  MEDIUM: qwen2:7b (7B参数, 380ms延迟)")
    print("  LARGE: qwen2.5:14b (14B参数, 800ms延迟)")
    print()
    print("-" * 70)
    print()

    # 模拟不同类型的用户查询
    examples = [
        ("你好", "简单问候"),
        ("今天天气怎么样？", "日常对话"),
        ("为什么我的代码运行这么慢？", "技术问题"),
        ("分析整个系统的性能瓶颈", "复杂推理"),
        ("帮我写一个 Python 脚本", "具体任务"),
    ]

    router = get_router([
        "gemma2:2b",
        "qwen2.5vl:3b",
        "qwen2:7b",
        "qwen2.5:14b",
    ])

    print("💬 实际路由示例:")
    print("-" * 70)

    for query, description in examples:
        model, config = router.route(query)
        params = router.get_optimized_parameters(query, config)

        print(f"\n查询: {query}")
        print(f"类型: {description}")
        print(f"→ 选择的模型: {model} ({config.tier.value})")
        print(f"  预计延迟: {config.avg_latency_ms}ms")
        print(f"  质量分数: {config.quality_score:.2f}/1.0")
        print(f"  Temperature: {params['temperature']}")

    print()
    print("-" * 70)
    print()
    print("💡 优化效果:")
    print("  • 简单问候: 80ms (vs 原来 500-2000ms)")
    print("  • 日常对话: 150ms (vs 原来 500-2000ms)")
    print("  • 复杂问题: 380ms (质量优先)")
    print("  • 深度推理: 800ms (最佳质量)")
    print()
    print("✨ 自动选择最佳模型，无需手动配置！")
    print()

if __name__ == "__main__":
    demo_routing()
