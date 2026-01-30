#!/usr/bin/env python3
"""
手动测试批量上传功能

这个脚本会创建一个测试文件夹，包含各种中文文件名和编码的文件，
然后测试FolderProcessor能否正确处理。
"""

import os
import sys
import tempfile
import shutil

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from memscreen.file_processor import FolderProcessor


def create_test_folder():
    """创建测试文件夹"""
    tmpdir = tempfile.mkdtemp(prefix='memscreen_test_')
    print(f"创建测试文件夹: {tmpdir}")

    # 创建中文子文件夹
    chinese_folder = os.path.join(tmpdir, '中文文档')
    os.makedirs(chinese_folder)

    code_folder = os.path.join(tmpdir, '代码')
    os.makedirs(code_folder)

    # 创建不同编码的文件
    files = [
        # UTF-8 编码
        ('README.md', 'utf-8', '# 项目说明\n\n这是一个测试项目。'),
        ('配置文件.json', 'utf-8', '{"名称": "测试", "值": 123}'),
        (os.path.join(chinese_folder, '笔记.txt'), 'utf-8', '这是中文笔记。\n包含多行内容。'),

        # GBK 编码
        (os.path.join(chinese_folder, '旧文档.txt'), 'gbk', '这是GBK编码的文档。'),

        # Python 代码
        (os.path.join(code_folder, 'script.py'), 'utf-8', '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def hello():
    print("Hello, 世界!")

if __name__ == "__main__":
    hello()
'''),

        # Markdown 文档
        (os.path.join(code_folder, 'guide.md'), 'utf-8', '''# 使用指南

## 简介
这是一个测试文档。

## 功能
- 功能1
- 功能2
'''),
    ]

    for file_path, encoding, content in files:
        full_path = os.path.join(tmpdir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w', encoding=encoding) as f:
            f.write(content)

        print(f"  创建: {file_path} (编码: {encoding})")

    return tmpdir


def test_batch_upload(folder_path):
    """测试批量上传"""
    print("\n" + "=" * 60)
    print("开始批量上传测试")
    print("=" * 60)

    # 创建进度回调
    def progress_callback(current, total, filename, status):
        symbols = {
            'processing': '⏳',
            'success': '✓',
            'failed': '✗',
            'skipped': '⊘'
        }
        symbol = symbols.get(status, '?')
        print(f"  [{current}/{total}] {symbol} {filename}")

    # 创建处理器
    processor = FolderProcessor(
        root_folder=folder_path,
        callback=progress_callback
    )

    # 执行批量处理
    print("\n扫描文件夹...")
    results = processor.process_folder(
        recursive=True,
        max_files=100,
        max_size_mb=50
    )

    # 显示结果
    print("\n" + "=" * 60)
    print("处理结果")
    print("=" * 60)
    print(f"成功: {results['success_count']} 个文件")
    print(f"失败: {results['failed_count']} 个文件")
    print(f"总大小: {results['total_size_mb']:.2f} MB")

    # 显示成功加载的文件详情
    if results['success']:
        print("\n成功加载的文件:")
        for file_data in results['success']:
            print(f"  - {file_data['filename']}")
            print(f"    路径: {file_data['relative_path']}")
            print(f"    编码: {file_data['encoding']}")
            print(f"    大小: {file_data['size']} 字节")
            # 显示内容预览
            preview = file_data['content'][:50]
            if len(file_data['content']) > 50:
                preview += "..."
            print(f"    预览: {preview}")
            print()

    # 显示失败的文件
    if results['failed']:
        print("\n失败的文件:")
        for failed_path in results['failed']:
            print(f"  - {failed_path}")

    # 显示摘要
    print("\n" + processor.get_summary())

    return results


def main():
    """主函数"""
    test_folder = None

    try:
        # 创建测试文件夹
        test_folder = create_test_folder()

        # 测试批量上传
        results = test_batch_upload(test_folder)

        # 验证结果
        print("\n" + "=" * 60)
        print("验证结果")
        print("=" * 60)

        if results['success_count'] > 0:
            print("✓ 测试通过！成功处理了文件。")
            print(f"  成功: {results['success_count']}")
            print(f"  失败: {results['failed_count']}")
            return 0
        else:
            print("✗ 测试失败！没有成功处理任何文件。")
            return 1

    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # 清理测试文件夹
        if test_folder and os.path.exists(test_folder):
            print(f"\n清理测试文件夹: {test_folder}")
            shutil.rmtree(test_folder)
            print("✓ 清理完成")


if __name__ == '__main__':
    sys.exit(main())
