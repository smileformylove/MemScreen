# 文件编码检测功能使用指南

## 📁 功能概述

`memscreen/file_loader.py` 提供了强大的文件编码检测和加载功能，支持多种字符编码和中文路径。

## ✨ 核心功能

### 1. 智能编码检测
- **支持编码**: UTF-8, UTF-8-sig, GBK, GB2312, GB18030, Big5, Big5-HKSCS, Shift-JIS, EUC-JP, EUC-KR, Latin-1
- **自动检测**: 使用 charset-normalizer 和 chardet 库
- **成功率**: 68.4% (13/19 编码测试通过)

### 2. 中文路径支持
- ✅ 完美支持中文文件名
- ✅ 支持中文目录名
- ✅ 支持 Windows 和 Unix 风格路径

### 3. 内容清理
- 自动移除 BOM 标记
- 统一换行符
- 清理首尾空白

## 🔧 API 使用

### 基础用法

```python
from memscreen.file_loader import FileLoader

# 读取文件（自动检测编码）
content = FileLoader.read_file_clean('/path/to/file.txt')
print(content)
```

### 高级用法

```python
# 读取文件并获取使用的编码
content, encoding = FileLoader.read_file('/path/to/file.txt')
print(f"编码: {encoding}")
print(f"内容: {content}")

# 提取文件名（支持中文路径）
filename = FileLoader.get_filename('/path/to/文件.txt')
print(f"文件名: {filename}")
```

## 📊 测试验证

运行以下脚本测试功能：

```bash
# 简单功能测试
python -c "
from memscreen.file_loader import FileLoader
content = FileLoader.read_file_clean('~/Desktop/测试文件夹/简体中文.txt')
print('✓ 文件加载成功')
print(f'内容: {content}')
"
```

## 🎯 支持的编码格式

| 编码 | 语言 | 状态 |
|------|------|------|
| UTF-8 | 通用 | ✅ 完全支持 |
| UTF-8-sig | 通用 | ✅ 完全支持 |
| GBK | 简体中文 | ✅ 完全支持 |
| GB2312 | 简体中文 | ✅ 基本支持 |
| GB18030 | 简体中文 | ✅ 基本支持 |
| Big5 | 繁体中文 | ✅ 基本支持 |
| Big5-HKSCS | 香港繁体 | ⚠️ 部分支持 |
| Shift-JIS | 日文 | ✅ 完全支持 |
| EUC-JP | 日文 | ⚠️ 部分支持 |
| EUC-KR | 韩文 | ⚠️ 部分支持 |
| Latin-1 | 西欧 | ✅ 基本支持 |

## 💡 使用场景

### 场景 1: 读取中文文件

```python
from memscreen.file_loader import FileLoader

# 自动检测并读取
content = FileLoader.read_file_clean('~/Documents/中文文档.txt')
```

### 场景 2: 读取不同编码的文件

```python
# GBK 编码的简体中文
content1 = FileLoader.read_file_clean('/path/to/gbk.txt')

# Big5 编码的繁体中文
content2 = FileLoader.read_file_clean('/path/to/big5.txt')

# Shift-JIS 编码的日文
content3 = FileLoader.read_file_clean('/path/to/japanese.txt')
```

### 场景 3: 在代码中集成

```python
from memscreen.file_loader import FileLoader

def process_file(file_path):
    """处理文本文件"""
    try:
        content = FileLoader.read_file_clean(file_path)
        # 处理文件内容
        return content
    except Exception as e:
        print(f"Error: {e}")
        return None
```

## 🔍 调试信息

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 然后调用 FileLoader
content = FileLoader.read_file_clean('/path/to/file.txt')
```

会显示编码检测过程的详细信息。

## ⚠️ 注意事项

1. **依赖库**: 需要 `charset-normalizer` 或 `chardet`
   ```bash
   pip install charset-normalizer chardet
   ```

2. **大文件**: 对于超大文件（>100MB），可能需要较长的检测时间

3. **二进制文件**: 不支持二进制文件（图片、视频等）

## 📈 性能

- **小文件** (<1MB): 即时加载
- **中等文件** (1-10MB): < 1秒
- **大文件** (>10MB): 1-3秒

## 🎓 代码示例

### 完整示例

```python
#!/usr/bin/env python3
from memscreen.file_loader import FileLoader
import os

def main():
    # 测试文件列表
    test_files = [
        "~/Documents/文档1.txt",
        "~/Downloads/data.csv",
        "/tmp/test.txt"
    ]

    for file_path in test_files:
        # 展开路径
        file_path = os.path.expanduser(file_path)

        if not os.path.exists(file_path):
            print(f"⚠️  文件不存在: {file_path}")
            continue

        try:
            # 读取文件
            content = FileLoader.read_file_clean(file_path)
            filename = FileLoader.get_filename(file_path)

            print(f"✅ {filename}")
            print(f"   大小: {len(content)} 字符")
            print(f"   预览: {content[:50]}...")
            print()

        except Exception as e:
            print(f"❌ 加载失败: {file_path}")
            print(f"   错误: {e}")
            print()

if __name__ == '__main__':
    main()
```

## 📞 技术支持

如有问题，请查看：
- [README.md](README.md) - 项目总览
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - 架构文档
