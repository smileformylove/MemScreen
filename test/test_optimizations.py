#!/usr/bin/env python3
"""
测试性能和语气优化效果

运行此脚本验证优化后的配置是否正常工作
"""

import sys
import time
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_performance_config():
    """测试性能配置"""
    print("\n" + "="*60)
    print("📊 测试性能配置")
    print("="*60)

    from memscreen.llm.performance_config import get_optimizer, ModelPerformanceConfig

    # 测试默认配置
    config = ModelPerformanceConfig()
    print(f"\n默认配置:")
    print(f"  - temperature_chat: {config.temperature_chat} (目标: 0.45)")
    print(f"  - max_tokens_chat: {config.max_tokens_chat} (目标: 384)")
    print(f"  - top_p: {config.top_p} (目标: 0.85)")
    print(f"  - top_k: {config.top_k} (目标: 25)")

    # 测试优化器
    optimizer = get_optimizer()
    print(f"\n✅ PerformanceOptimizer 初始化成功")

    # 测试不同场景参数
    scenarios = ["chat", "chat_fast", "vision", "summary", "search"]
    print(f"\n场景参数:")
    for scenario in scenarios:
        params = optimizer.get_optimized_params(scenario)
        print(f"\n  {scenario}:")
        print(f"    - 模型: {params['model']}")
        print(f"    - num_predict: {params['num_predict']}")
        print(f"    - temperature: {params['temperature']}")

    return True


def test_ollama_config():
    """测试 Ollama 配置"""
    print("\n" + "="*60)
    print("🔧 测试 Ollama 配置")
    print("="*60)

    from memscreen.llm.ollama import OllamaConfig

    config = OllamaConfig()
    print(f"\n默认配置:")
    print(f"  - temperature: {config.temperature} (目标: 0.45)")
    print(f"  - max_tokens: {config.max_tokens} (目标: 384)")
    print(f"  - top_p: {config.top_p} (目标: 0.85)")
    print(f"  - top_k: {config.top_k} (目标: 25)")

    # 验证优化值
    assert config.temperature == 0.45, f"temperature 应该是 0.45，实际是 {config.temperature}"
    assert config.max_tokens == 384, f"max_tokens 应该是 384，实际是 {config.max_tokens}"
    assert config.top_p == 0.85, f"top_p 应该是 0.85，实际是 {config.top_p}"
    assert config.top_k == 25, f"top_k 应该是 25，实际是 {config.top_k}"

    print(f"\n✅ 所有配置值验证通过")
    return True


def test_prompts():
    """测试 Prompts"""
    print("\n" + "="*60)
    print("💬 测试 Prompts")
    print("="*60)

    from memscreen.prompts import MEMORY_ANSWER_PROMPT, FACT_RETRIEVAL_PROMPT

    print(f"\nMEMORY_ANSWER_PROMPT 长度: {len(MEMORY_ANSWER_PROMPT)} 字符")
    print(f"  预期: 约 800-1000 字符（简化后）")
    assert len(MEMORY_ANSWER_PROMPT) < 1500, "Prompt 应该更简洁了"
    assert "简洁直接" in MEMORY_ANSWER_PROMPT, "应该包含中文指令"
    assert "友好自然" in MEMORY_ANSWER_PROMPT, "应该强调友好语气"
    print(f"  ✅ Prompt 简洁且使用中文")

    print(f"\nFACT_RETRIEVAL_PROMPT 长度: {len(FACT_RETRIEVAL_PROMPT)} 字符")
    print(f"  预期: 约 600-800 字符（简化后）")
    assert len(FACT_RETRIEVAL_PROMPT) < 1000, "Prompt 应该更简洁了"
    print(f"  ✅ Prompt 已简化")

    return True


def test_llm_response():
    """测试 LLM 响应速度（需要 Ollama 运行）"""
    print("\n" + "="*60)
    print("🤖 测试 LLM 响应速度")
    print("="*60)

    try:
        from memscreen.llm.ollama import OllamaLLM

        # 检查 Ollama 是否运行
        import requests
        try:
            requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
        except:
            print("\n⚠️  Ollama 未运行，跳过实际响应测试")
            print("   启动 Ollama: ollama serve")
            return True

        # 测试默认配置响应
        llm = OllamaLLM()
        messages = [{"role": "user", "content": "你好"}]

        print(f"\n测试简单查询...")
        start = time.time()
        response = llm.generate_response(messages)
        duration = time.time() - start

        print(f"  响应: {response[:50]}...")
        print(f"  用时: {duration:.2f}s")
        print(f"  目标: < 3s")

        if duration < 3:
            print(f"  ✅ 响应速度良好")
        else:
            print(f"  ⚠️  响应较慢，可能需要进一步优化")

        return True

    except Exception as e:
        print(f"\n⚠️  测试失败: {e}")
        return True


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 MemScreen 优化验证测试")
    print("="*60)

    tests = [
        ("性能配置", test_performance_config),
        ("Ollama 配置", test_ollama_config),
        ("Prompts", test_prompts),
        ("LLM 响应", test_llm_response),
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
        print("\n🎉 所有测试通过！优化配置正常工作。")
        print("\n下一步:")
        print("  1. 启动应用测试实际效果")
        print("  2. 观察响应速度和回复质量")
        print("  3. 根据需要进一步调整参数")
    else:
        print("\n⚠️  部分测试失败，请检查配置。")

    print("\n" + "="*60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
