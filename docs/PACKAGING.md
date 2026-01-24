# MemScreen 打包与安装指南

## 📦 项目结构

```
MemScreen/
├── pyproject.toml          # 项目构建配置
├── MANIFEST.in             # 包含文件清单
├── README.md              # 项目文档
├── LICENSE                # MIT 许可证
├── PACKAGING.md           # 本文档
├── memscreen/             # Python 包目录
│   ├── __init__.py       # 包初始化
│   ├── memscreen.py       # 主程序（屏幕录制）
│   ├── chat_ui.py        # 聊天界面
│   ├── screenshot_ui.py   # 截图浏览器
│   ├── process_mining.py # 流程挖掘分析
│   ├── memory.py         # 记忆核心
│   ├── chroma.py         # 向量数据库
│   ├── telemetry.py      # 键盘鼠标追踪
│   ├── utils.py          # 工具函数
│   ├── prompts.py        # AI 提示词
│   └── test_memory.py   # 测试脚本
└── dist/                 # 构建输出目录（git忽略）
    ├── memscreen-0.1.0-py3-none-any.whl
    └── memscreen-0.1.0.tar.gz
```

## 🚀 安装方式

### 方式 1: 从 PyPI 安装（推荐）

```bash
pip install memscreen
```

### 方式 2: 从 GitHub 直接安装

```bash
pip install git+https://github.com/smileformylove/MemScreen.git
```

### 方式 3: 从本地 wheel 文件安装

```bash
# 构建（可选，如果已有 wheel 可跳过）
python -m build

# 安装
pip install dist/memscreen-0.1.0-py3-none-any.whl
```

### 方式 4: 开发模式安装（可编辑）

```bash
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
pip install -e .
```

## 📋 命令行工具

安装完成后，会自动创建以下命令行入口点：

| 命令 | 功能 | 说明 |
|------|------|------|
| `memscreen` | 屏幕录制 | 启动屏幕录制和记录 |
| `memscreen-chat` | 聊天界面 | 与你的屏幕历史进行对话 |
| `memscreen-screenshots` | 截图浏览器 | 浏览和搜索已捕获的屏幕 |
| `memscreen-process-mining` | 流程挖掘 | 分析工作模式和键盘鼠标活动 |

## 🔧 系统要求

- **Python**: >= 3.8
- **操作系统**: macOS / Linux / Windows
- **硬件**:
  - RAM: 4GB+（推荐 8GB+）
  - GPU: 可选，但强烈推荐用于 AI 加速
- **其他**: 需要安装 [Ollama](https://ollama.com) 并运行本地模型

## 📦 依赖项

所有依赖项会在安装时自动安装：

```
torch>=2.0.0          # PyTorch 深度学习框架
torchvision>=0.15.0   # 计算机视觉
pydantic>=2.0.0       # 数据验证
ttkthemes>=3.0.0      # GUI 主题
ollama>=0.3.0         # 本地 LLM 客户端
mss>=9.0.0           # 屏幕捕获
matplotlib>=3.0.0     # 数据可视化
openai>=1.0.0         # AI API 客户端
opencv-python>=4.0.0   # 图像处理
Pillow>=9.0.0         # 图像处理
numpy>=1.20.0         # 数值计算
easyocr>=1.0.0        # OCR 文本识别
pynput>=1.6.0         # 键盘鼠标监听
```

## 🛠️ 开发者指南

### 构建项目

```bash
# 安装构建工具
pip install --upgrade build setuptools wheel

# 构建 wheel 和源码包
python -m build

# 输出在 dist/ 目录：
# - memscreen-0.1.0-py3-none-any.whl
# - memscreen-0.1.0.tar.gz
```

### 发布到 PyPI

```bash
# 1. 安装 twine
pip install twine

# 2. 检查包元数据
twine check dist/*

# 3. 上传到测试 PyPI（可选）
twine upload --repository testpypi dist/*

# 4. 上传到正式 PyPI
twine upload dist/*
```

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

包括：
- pytest（测试）
- black（代码格式化）
- flake8（代码检查）

## 📚 使用示例

### 启动屏幕录制
```bash
# 默认设置
memscreen

# 自定义设置
memscreen --duration 120 --interval 5 --screenshot-interval 1.0
```

### 与屏幕对话
```bash
memscreen-chat
```

### 浏览截图
```bash
memscreen-screenshots
```

### 分析工作模式
```bash
memscreen-process-mining
```

## ⚠️ 注意事项

1. **首次使用前**需要拉取本地 AI 模型：
   ```bash
   ollama pull qwen3:1.7b
   ollama pull qwen2.5vl:3b
   ollama pull mxbai-embed-large:latest
   ```

2. **权限要求**：
   - 屏幕录制需要操作系统级权限
   - macOS: 系统偏好设置 → 安全性与隐私 → 屏幕录制
   - Windows: 管理员权限可能需要
   - Linux: 通常自动获得权限

3. **GPU 加速**（可选）：
   ```bash
   # 安装 CUDA 版本的 PyTorch
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

## 🐛 故障排除

### 问题：导入错误
```bash
# 解决方案：重新安装
pip uninstall memscreen
pip install memscreen --force-reinstall
```

### 问题：权限被拒绝（macOS）
```bash
# 解决方案：添加屏幕录制权限
# 系统偏好设置 → 安全性与隐私 → 隐私 → 屏幕录制
# 添加 Terminal 或 Python 到允许列表
```

### 问题：Ollama 连接失败
```bash
# 确保 Ollama 正在运行
ollama serve

# 检查模型是否已下载
ollama list
```

## 📖 更多信息

- **完整文档**: [README.md](README.md)
- **项目主页**: https://github.com/smileformylove/MemScreen
- **问题反馈**: https://github.com/smileformylove/MemScreen/issues
- **许可证**: MIT
