#!/usr/bin/env python3
"""
Unit tests for FolderProcessor
"""

import os
import sys
import tempfile

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from memscreen.file_processor import FolderProcessor


def test_basic_scan():
    """测试基本扫描功能"""
    print("\n=== Test: Basic Scan ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        test_files = [
            'test1.txt',
            'test2.md',
            'test3.py',
            'data.json',
            'image.png',  # 应该被忽略
        ]

        for filename in test_files:
            path = os.path.join(tmpdir, filename)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f'Test content for {filename}')

        # 扫描
        processor = FolderProcessor(tmpdir)
        files = processor.scan_directory(recursive=False)

        # 验证
        assert len(files) == 4, f"Expected 4 files, got {len(files)}"
        print(f"✓ Found {len(files)} text files")
        print(f"  Files: {[os.path.basename(f) for f in files]}")


def test_recursive_scan():
    """测试递归扫描功能"""
    print("\n=== Test: Recursive Scan ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建子目录和文件
        subdir = os.path.join(tmpdir, 'subdir')
        os.makedirs(subdir)

        files = {
            'root.txt': 'Root file',
            'subdir/nested.txt': 'Nested file',
            'subdir/deep.py': 'Deep file',
        }

        for file_path, content in files.items():
            full_path = os.path.join(tmpdir, file_path)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # 递归扫描
        processor = FolderProcessor(tmpdir)
        files = processor.scan_directory(recursive=True)

        # 验证
        assert len(files) == 3, f"Expected 3 files, got {len(files)}"
        print(f"✓ Found {len(files)} files recursively")


def test_chinese_path():
    """测试中文路径支持"""
    print("\n=== Test: Chinese Path ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建中文文件夹和文件
        chinese_folder = os.path.join(tmpdir, '测试文件夹')
        os.makedirs(chinese_folder)

        chinese_file = os.path.join(chinese_folder, '中文文件.txt')
        with open(chinese_file, 'w', encoding='utf-8') as f:
            f.write('测试内容')

        # 扫描
        processor = FolderProcessor(tmpdir)
        files = processor.scan_directory(recursive=True)

        # 验证
        assert len(files) == 1, f"Expected 1 file, got {len(files)}"
        assert '中文文件.txt' in files[0], f"Chinese filename not found in {files[0]}"
        print(f"✓ Chinese path handled correctly")
        print(f"  Path: {files[0]}")


def test_encoding_detection():
    """测试编码检测"""
    print("\n=== Test: Encoding Detection ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建不同编码的文件
        encodings = {
            'test_utf8.txt': ('utf-8', '测试内容'),
            'test_gbk.txt': ('gbk', '测试内容'),
            'test_big5.txt': ('big5', '繁體中文'),
        }

        for filename, (encoding, content) in encodings.items():
            path = os.path.join(tmpdir, filename)
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)

        # 处理
        processor = FolderProcessor(tmpdir)
        results = processor.process_folder(recursive=False)

        # 验证
        assert len(results['success']) == 3, f"Expected 3 successes, got {len(results['success'])}"
        assert len(results['failed']) == 0, f"Expected 0 failures, got {len(results['failed'])}"

        # 检查内容
        for file_data in results['success']:
            assert len(file_data['content']) > 0, "Content should not be empty"
            print(f"✓ {file_data['filename']}: encoding={file_data['encoding']}")


def test_file_filtering():
    """测试文件类型过滤"""
    print("\n=== Test: File Filtering ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建不同类型的文件
        files = {
            'readme.md': 'Markdown',
            'script.py': 'Python',
            'data.json': '{"key": "value"}',
            'config.yaml': 'key: value',
            'image.png': b'\x89PNG\r\n',  # Binary, should be ignored
            'archive.zip': b'PK\x03\x04',  # Binary, should be ignored
        }

        for filename, content in files.items():
            path = os.path.join(tmpdir, filename)
            mode = 'wb' if isinstance(content, bytes) else 'w'
            encoding = None if isinstance(content, bytes) else 'utf-8'
            with open(path, mode) as f:
                if encoding:
                    f.write(content)
                else:
                    f.write(content)

        # 扫描
        processor = FolderProcessor(tmpdir)
        files = processor.scan_directory(recursive=False)

        # 验证
        assert len(files) == 4, f"Expected 4 text files, got {len(files)}"
        print(f"✓ Correctly filtered text files (ignored binary files)")


def test_ignored_folders():
    """测试忽略特定文件夹"""
    print("\n=== Test: Ignored Folders ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建应该被忽略的文件夹
        for folder_name in ['__pycache__', '.git', 'node_modules', 'venv']:
            folder_path = os.path.join(tmpdir, folder_name)
            os.makedirs(folder_path)
            file_path = os.path.join(folder_path, 'test.txt')
            with open(file_path, 'w') as f:
                f.write('Should be ignored')

        # 创建不应该被忽略的文件夹
        normal_folder = os.path.join(tmpdir, 'my_folder')
        os.makedirs(normal_folder)
        normal_file = os.path.join(normal_folder, 'test.txt')
        with open(normal_file, 'w') as f:
            f.write('Should be included')

        # 扫描
        processor = FolderProcessor(tmpdir)
        files = processor.scan_directory(recursive=True)

        # 验证
        assert len(files) == 1, f"Expected 1 file, got {len(files)}"
        assert 'my_folder' in files[0], f"Expected my_folder, got {files[0]}"
        print(f"✓ Correctly ignored system folders")


def test_error_handling():
    """测试错误处理"""
    print("\n=== Test: Error Handling ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建一个正常文件
        normal_file = os.path.join(tmpdir, 'normal.txt')
        with open(normal_file, 'w', encoding='utf-8') as f:
            f.write('Normal content')

        # 创建一个无法读取的文件（权限受限）
        restricted_file = os.path.join(tmpdir, 'restricted.txt')
        with open(restricted_file, 'w', encoding='utf-8') as f:
            f.write('Restricted content')

        # 在Unix系统上移除读权限
        if os.name != 'nt':
            os.chmod(restricted_file, 0o000)

        # 处理
        processor = FolderProcessor(tmpdir)
        results = processor.process_folder(recursive=False)

        # 恢复权限（以便清理）
        if os.name != 'nt':
            os.chmod(restricted_file, 0o644)

        # 验证
        # 至少应该有一个成功
        assert len(results['success']) >= 1, "Should have at least 1 success"
        print(f"✓ Error handling works")
        print(f"  Success: {len(results['success'])}, Failed: {len(results['failed'])}")


def test_get_summary():
    """测试摘要生成"""
    print("\n=== Test: Get Summary ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        for i in range(3):
            path = os.path.join(tmpdir, f'test{i}.txt')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f'Content {i}')

        # 处理
        processor = FolderProcessor(tmpdir)
        processor.process_folder(recursive=False)

        # 获取摘要
        summary = processor.get_summary()
        print(f"\n{summary}")

        # 验证摘要包含关键信息
        assert '3 files' in summary, "Summary should show 3 files"
        assert 'MB' in summary, "Summary should show size in MB"


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Running FolderProcessor Tests")
    print("=" * 50)

    tests = [
        test_basic_scan,
        test_recursive_scan,
        test_chinese_path,
        test_encoding_detection,
        test_file_filtering,
        test_ignored_folders,
        test_error_handling,
        test_get_summary,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ Test failed: {test.__name__}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ Test error: {test.__name__}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
