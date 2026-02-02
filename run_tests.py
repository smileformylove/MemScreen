#!/usr/bin/env python3
"""
MemScreen 测试套件 - 统一测试入口

运行所有测试或选择特定测试类别。
"""

import sys
import os
import subprocess
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'=' * 60}")
    print(f"🧪 {description}")
    print('=' * 60)
    print(f"命令: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, shell=False)

    if result.returncode == 0:
        print(f"✅ {description} - 通过")
        return True
    else:
        print(f"❌ {description} - 失败")
        return False


def test_performance():
    """运行性能测试"""
    return run_command(
        [sys.executable, "tests/test_performance.py"],
        "性能测试"
    )


def test_visual_memory():
    """运行视觉记忆测试"""
    return run_command(
        [sys.executable, "tests/test_visual_memory.py"],
        "视觉记忆测试"
    )


def test_dynamic_memory():
    """运行动态 Memory 测试"""
    return run_command(
        [sys.executable, "tests/test_dynamic_memory.py"],
        "动态 Memory 测试"
    )


def test_memory_integration():
    """运行 Memory 集成测试"""
    return run_command(
        [sys.executable, "tests/test_memory_integration.py"],
        "Memory 集成测试"
    )


def test_app_integration():
    """运行应用集成测试"""
    return run_command(
        [sys.executable, "tests/test_app_integration.py"],
        "应用集成测试"
    )


def test_audio():
    """运行音频录制测试"""
    return run_command(
        [sys.executable, "test_audio_recording.py"],
        "音频录制测试"
    )


def test_all():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 MemScreen 完整测试套件")
    print("=" * 60)

    tests = [
        ("性能测试", test_performance),
        ("视觉记忆测试", test_visual_memory),
        ("动态 Memory 测试", test_dynamic_memory),
        ("Memory 集成测试", test_memory_integration),
        ("应用集成测试", test_app_integration),
    ]

    results = []
    for name, test_func in tests:
        results.append((name, test_func()))

    # 显示总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s} {status}")

    print(f"\n总计: {passed}/{total} 通过")
    print("=" * 60)

    return passed == total


def main():
    parser = argparse.ArgumentParser(
        description="MemScreen 测试套件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行所有测试
  python run_tests.py

  # 运行性能测试
  python run_tests.py --performance

  # 运行视觉记忆测试
  python run_tests.py --visual

  # 运行多个测试
  python run_tests.py --performance --visual
        """
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有测试"
    )

    parser.add_argument(
        "--performance",
        action="store_true",
        help="运行性能测试"
    )

    parser.add_argument(
        "--visual",
        action="store_true",
        help="运行视觉记忆测试"
    )

    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="运行动态 Memory 测试"
    )

    parser.add_argument(
        "--integration",
        action="store_true",
        help="运行集成测试"
    )

    parser.add_argument(
        "--audio",
        action="store_true",
        help="运行音频测试"
    )

    args = parser.parse_args()

    # 如果没有指定任何测试，运行所有测试
    if not any([args.all, args.performance, args.visual, args.dynamic,
               args.integration, args.audio]):
        args.all = True

    print("=" * 60)
    print("🧪 MemScreen 测试套件")
    print("=" * 60)

    success = True

    if args.all:
        success = test_all()
    else:
        if args.performance:
            if not test_performance():
                success = False

        if args.visual:
            if not test_visual_memory():
                success = False

        if args.dynamic:
            if not test_dynamic_memory():
                success = False

        if args.integration:
            if not test_memory_integration():
                success = False
            if not test_app_integration():
                success = False

        if args.audio:
            if not test_audio():
                success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
