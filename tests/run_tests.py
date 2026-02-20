#!/usr/bin/env python3
"""
MemScreen  - 


"""

import sys
import os
import subprocess
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_command(cmd, description):
    """"""
    print(f"\n{'=' * 60}")
    print(f"🧪 {description}")
    print('=' * 60)
    print(f": {' '.join(cmd)}\n")

    result = subprocess.run(cmd, shell=False)

    if result.returncode == 0:
        print(f"✅ {description} - ")
        return True
    else:
        print(f"❌ {description} - ")
        return False


def test_performance():
    """"""
    return run_command(
        [sys.executable, "tests/test_performance.py"],
        ""
    )


def test_visual_memory():
    """"""
    return run_command(
        [sys.executable, "tests/test_visual_memory.py"],
        ""
    )


def test_dynamic_memory():
    """ Memory """
    return run_command(
        [sys.executable, "tests/test_dynamic_memory.py"],
        " Memory "
    )


def test_memory_integration():
    """ Memory """
    return run_command(
        [sys.executable, "tests/test_memory_integration.py"],
        "Memory "
    )


def test_app_integration():
    """"""
    return run_command(
        [sys.executable, "tests/test_app_integration.py"],
        ""
    )


def test_audio():
    """"""
    return run_command(
        [sys.executable, "test_audio_recording.py"],
        ""
    )


def test_all():
    """"""
    print("\n" + "=" * 60)
    print("🧪 MemScreen ")
    print("=" * 60)

    tests = [
        ("", test_performance),
        ("", test_visual_memory),
        (" Memory ", test_dynamic_memory),
        ("Memory ", test_memory_integration),
        ("", test_app_integration),
    ]

    results = []
    for name, test_func in tests:
        results.append((name, test_func()))

    # 
    print("\n" + "=" * 60)
    print("📊 ")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ " if result else "❌ "
        print(f"{name:20s} {status}")

    print(f"\n: {passed}/{total} ")
    print("=" * 60)

    return passed == total


def main():
    parser = argparse.ArgumentParser(
        description="MemScreen ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
:
  # 
  python run_tests.py

  # 
  python run_tests.py --performance

  # 
  python run_tests.py --visual

  # 
  python run_tests.py --performance --visual
        """
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help=""
    )

    parser.add_argument(
        "--performance",
        action="store_true",
        help=""
    )

    parser.add_argument(
        "--visual",
        action="store_true",
        help=""
    )

    parser.add_argument(
        "--dynamic",
        action="store_true",
        help=" Memory "
    )

    parser.add_argument(
        "--integration",
        action="store_true",
        help=""
    )

    parser.add_argument(
        "--audio",
        action="store_true",
        help=""
    )

    args = parser.parse_args()

    # 
    if not any([args.all, args.performance, args.visual, args.dynamic,
               args.integration, args.audio]):
        args.all = True

    print("=" * 60)
    print("🧪 MemScreen ")
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
