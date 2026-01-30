# 中文路径支持测试指南

## 问题诊断

如果您在使用文件浏览功能时遇到中文路径乱码问题，请按以下步骤进行诊断：

## 1. 基础功能测试

首先运行以下命令测试 FileLoader 是否正常工作：

```bash
python test_chinese_path.py
```

预期输出：
```
============================================================
测试中文路径文件加载
============================================================
文件路径: /tmp/测试目录/测试文件.txt
路径存在: True

✓ 成功读取文件
  文件名: 测试文件.txt
  内容: '简体中文测试内容'
```

## 2. 完整演示测试

运行完整的演示脚本：

```bash
python demo_file_loader.py
```

这会测试：
- ✓ 中文文件名 + GBK 编码
- ✓ 繁体中文 + Big5 编码
- ✓ 日文 + Shift-JIS 编码
- ✓ UTF-8 with BOM
- ✓ Windows 路径处理

## 3. 在应用中测试

启动应用后：

```bash
./run.sh
# 或
python start.py
```

### 测试步骤：

1. **创建测试文件**（如果还没有）：
   ```bash
   mkdir -p ~/桌面/测试目录
   echo "简体中文测试内容" > ~/桌面/测试目录/测试文件.txt
   echo "繁體中文測試" > ~/桌面/测试目录/繁體文件.txt
   echo "こんにちは世界" > ~/桌面/测试目录/日本語.txt
   ```

2. **在应用中加载文件**：
   - 进入 Chat 界面
   - 点击 "Browse Files" 或 "浏览文件" 按钮
   - 导航到包含中文文件名的目录
   - 选择文件并加载

3. **查看调试输出**：
   - 在终端中查看日志输出
   - 应该看到类似这样的输出：
     ```
     [Chat] Opening file dialog at: /Users/xxx
     [Chat] File selection changed: ['/Users/xxx/测试文件.txt']
     [Chat] Raw selected path: '/Users/xxx/测试文件.txt'
     [Chat] Path type: <class 'str'>
     [Chat] ✓ Path exists, loading file...
     [FileLoader] Detected encoding (charset-normalizer): utf-8
     [FileLoader] Successfully read with encoding: utf-8 (score: 0.89)
     [Chat] ✓ File loaded: 测试文件.txt
     ```

## 4. 常见问题排查

### 问题 1: 文件对话框中中文显示为乱码

**原因**：系统字体配置问题

**解决方案**：
- 检查 Kivy 是否正确注册了中文字体
- 查看启动日志中的字体注册信息

### 问题 2: 选择文件后显示 "Path not found"

**原因**：路径编码问题

**检查项**：
```python
# 在终端中运行
import os
path = "/path/to/中文文件.txt"
print(f"Path exists: {os.path.exists(path)}")
print(f"Path bytes: {path.encode('utf-8')}")
```

### 问题 3: 文件内容显示乱码

**原因**：文件编码检测失败

**解决方案**：
- FileLoader 会自动尝试多种编码
- 查看调试输出中的编码检测结果
- 如果检测失败，可以尝试转换为 UTF-8 编码

## 5. 手动编码测试

如果自动检测失败，可以手动测试特定编码：

```python
from memscreen.file_loader import FileLoader

# 读取 GBK 编码文件
content = FileLoader.read_file_clean('/path/to/gbk/file.txt')
print(content)

# 读取 Big5 编码文件
content = FileLoader.read_file_clean('/path/to/big5/file.txt')
print(content)
```

## 6. 日志级别调整

如需更详细的日志，可以修改 `start.py`：

```python
import logging
logging.basicConfig(level=logging.DEBUG)  # 改为 DEBUG 级别
```

## 7. 成功标志

如果一切正常，您应该看到：

✅ 文件对话框中中文文件名显示正确
✅ 选择文件后路径正确显示在日志中
✅ 文件内容正确加载（无乱码）
✅ Chat 界面显示 `[File] 文件名.txt`

## 8. 仍需帮助？

如果以上步骤都完成了但仍有问题，请提供：

1. 终端中的完整日志输出
2. 操作系统的版本信息
3. Python 版本 (`python --version`)
4. 文件的具体路径和编码信息
