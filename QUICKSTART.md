# 🚀 MemScreen v0.1 - 快速启动指南

## 最简单的启动方式

```bash
python3 start.py
```

就这么简单！UI会立即打开。✨

---

## 其他启动方式

### 方式1: Python启动脚本（推荐）
```bash
python3 start.py
```
- ✅ 最简单
- ✅ 不需要Ollama
- ✅ 使用模拟内存
- ✅ 所有UI功能可用

### 方式2: Bash启动脚本
```bash
./run_ui.sh
```
- ✅ 检查依赖
- ✅ 提供错误提示
- ⚠️  需要先安装依赖

---

## UI功能

启动后，你会看到5个标签页：

### 🔴 Recording（录制）
- 屏幕截图录制
- 实时预览
- 视频保存

### 💬 Chat（聊天）
- AI对话界面
- 需要Ollama运行
- 问答功能

### 🎬 Video（视频）
- 浏览录制的视频
- 播放控制
- 时间线导航

### 🔍 Search（搜索）
- 搜索屏幕内容
- 语义搜索
- 需要完整Memory系统

### ⚙️ Settings（设置）
- 配置选项
- 模型选择
- 路径设置

---

## 安装依赖（如果需要）

如果遇到 `ModuleNotFoundError`：

```bash
pip3 install --user -e .
```

或使用虚拟环境（推荐）：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
python3 start.py
```

---

## 推荐工作流

**首次使用**：
1. `python3 start.py` - 启动UI
2. 尝试Recording功能
3. 录制一段屏幕
4. 在Video标签查看

**日常使用**：
1. `python3 start.py` - 启动
2. 录制屏幕
3. 搜索内容
4. 与AI对话（需要Ollama）

就这么简单！🎉
