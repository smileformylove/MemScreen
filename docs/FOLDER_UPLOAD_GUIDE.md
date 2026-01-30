# 文件夹批量上传功能使用指南

## 概述

MemScreen 现在支持文件夹批量上传功能，可以一次性上传整个文件夹中的所有文本文件。

## 主要特性

- ✅ **跨平台支持** - 适用于 macOS、Windows、Linux
- ✅ **递归扫描** - 自动处理所有子文件夹
- ✅ **智能过滤** - 只上传文本文件，自动忽略二进制文件
- ✅ **中文支持** - 完美支持中文路径和文件名
- ✅ **编码检测** - 自动识别 UTF-8、GBK、Big5 等多种编码
- ✅ **实时进度** - 显示上传进度和统计信息
- ✅ **批量保存** - 自动保存到内存系统

## 使用方法

### 1. 启动应用

```bash
python -m memscreen.ui.kivy_app
```

### 2. 点击"Load Folder"按钮

在聊天界面，找到蓝色的 **"📁 Load Folder"** 按钮，点击它。

### 3. 选择文件夹

会弹出一个文件夹选择对话框：
- 导航到您要上传的文件夹
- 点击该文件夹选中它
- 点击 **"Upload Folder"** 按钮

### 4. 查看进度

上传过程中会显示进度弹窗：
- **进度条** - 显示整体进度
- **当前文件** - 正在处理的文件名（支持中文）
- **统计信息** - 成功/失败/跳过的文件数量

### 5. 查看结果

上传完成后，聊天界面会显示摘要：
- 成功上传的文件数量
- 失败的文件数量（如果有）
- 总文件大小

## 支持的文件类型

### 文本文件（会自动上传）

- 文档：`.txt`, `.md`, `.markdown`, `.rst`
- 代码：`.py`, `.js`, `.ts`, `.java`, `.c`, `.cpp`, `.h`, `.go`, `.rs`
- 配置：`.json`, `.yaml`, `.yml`, `.xml`, `.toml`, `.ini`, `.cfg`
- 脚本：`.sh`, `.bash`, `.zsh`, `.ps1`, `.bat`
- 数据：`.csv`, `.log`, `.sql`
- 网页：`.html`, `.css`, `.scss`
- 其他：`.tex`, `.bib`

### 二进制文件（自动忽略）

- 图片：`.png`, `.jpg`, `.gif`, `.svg`
- 视频：`.mp4`, `.avi`, `.mov`
- 压缩包：`.zip`, `.tar`, `.gz`, `.rar`
- 可执行文件：`.exe`, `.dll`, `.so`

### 自动忽略的文件夹

以下文件夹会被自动跳过：
- `__pycache__`, `.git`, `.svn`, `node_modules`
- `venv`, `.venv`, `env`, `.env`
- `.idea`, `.vscode`, `dist`, `build`, `target`

## 限制设置

为了防止意外选择过大的文件夹，设置了以下默认限制：

- **最大文件数**: 100 个
- **最大总大小**: 50 MB

如果需要修改这些限制，可以在 `memscreen/ui/kivy_app.py` 中调整 `_process_folder_batch()` 方法的参数。

## 中文路径支持

### 完美支持

- ✅ 中文文件夹名：`/用户/文档/中文文件夹/`
- ✅ 中文文件名：`测试文档.txt`, `配置文件.json`
- ✅ 混合编码：UTF-8、GBK、GB2312、Big5 等
- ✅ 深层嵌套：无限层级子文件夹

### 编码自动检测

系统会自动检测文件编码，支持：
- UTF-8 (with/without BOM)
- GBK / GB2312 / GB18030 (简体中文)
- Big5 / Big5-HKSCS (繁体中文)
- Shift-JIS / EUC-JP (日文)
- EUC-KR (韩文)
- Latin-1 (西文)

## 使用示例

### 示例 1: 上传代码项目

```
项目文件夹/
├── README.md          ← 会上传
├── requirements.txt   ← 会上传
├── src/
│   ├── main.py       ← 会上传
│   └── utils.py      ← 会上传
├── tests/
│   └── test_main.py  ← 会上传
├── .git/             ← 自动忽略
└── __pycache__/      ← 自动忽略
```

### 示例 2: 上传文档集合

```
文档/
├── 中文笔记/
│   ├── 第一章.md     ← 会上传
│   └── 第二章.md     ← 会上传
├── 代码示例/
│   ├── example.py    ← 会上传
│   └── config.json   ← 会上传
└── 参考资料/
    └── 论文.txt      ← 会上传
```

## 故障排除

### 问题：文件夹选择后没有反应

**解决方案**:
- 确保选择的是一个文件夹（不是文件）
- 确保文件夹中有支持的文本文件
- 查看控制台日志了解详细信息

### 问题：某些文件上传失败

**可能原因**:
- 文件权限受限（无法读取）
- 文件编码损坏
- 文件大小超过限制

**解决方案**:
- 检查文件权限：`ls -l filename`
- 尝试用文本编辑器打开文件
- 查看控制台错误日志

### 问题：进度弹窗卡住

**解决方案**:
- 点击 Cancel 按钮取消
- 重启应用
- 检查文件夹中是否有异常大的文件

### 问题：中文路径显示乱码

**解决方案**:
- 确保系统locale设置正确
- macOS: 检查 Terminal 的字符编码设置
- Windows: 使用 PowerShell 或 CMD UTF-8 模式

## 技术细节

### 架构

```
UI 层 (Kivy)
  ↓
FolderProcessor (批量处理)
  ↓
FileLoader (编码检测)
  ↓
Memory 系统 (存储)
```

### 性能

- **小文件** (< 1 KB): 即时加载
- **中等文件** (1-10 MB): < 1 秒/文件
- **大文件** (> 10 MB): 1-3 秒/文件

### 线程安全

- 文件处理在后台线程执行
- UI 更新在主线程执行（使用 Clock.schedule_once）
- 使用线程锁保护共享数据

## 开发者信息

### 测试

运行单元测试：

```bash
# 运行所有测试
python test/test_folder_processor.py

# 运行手动测试
python test/test_batch_upload_manual.py
```

### API 使用

在代码中使用 FolderProcessor：

```python
from memscreen.file_processor import FolderProcessor

# 创建处理器
processor = FolderProcessor(
    root_folder='/path/to/folder',
    callback=lambda current, total, filename, status: print(f"{current}/{total}: {filename}")
)

# 批量处理
results = processor.process_folder(
    recursive=True,
    max_files=100,
    max_size_mb=50
)

# 查看结果
print(f"成功: {results['success_count']}")
print(f"失败: {results['failed_count']}")
```

## 更新日志

### v0.4.0 (2025-01-30)

- ✨ 新增文件夹批量上传功能
- ✨ 支持递归扫描子文件夹
- ✨ 智能文件类型过滤
- ✨ 实时进度显示
- ✨ 完美中文路径支持
- 🐛 修复 macOS AppleScript 兼容性问题
- 🔄 重构文件上传逻辑
- 📝 添加完整的单元测试

## 反馈

如有问题或建议，请：
1. 查看控制台日志
2. 运行测试脚本验证
3. 提交 Issue 到项目仓库
