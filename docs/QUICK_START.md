# MemScreen 快速启动指南

## 🚀 三种安装方式

### 方式 1: 一键安装（推荐）

适用于：**macOS 和 Linux 用户**

```bash
# 克隆项目
git clone https://github.com/smileformylove/MemScreen.git && cd MemScreen

# 运行一键安装脚本
chmod +x install.sh
./install.sh

# 启动应用（默认 Kivy UI）
python start.py

# 或启动 Flutter UI（可选）
./scripts/start_flutter.sh
```

**安装脚本会自动：**
- ✅ 检查 Python 版本
- ✅ 创建虚拟环境
- ✅ 安装所有依赖
- ✅ 检查/安装 Ollama
- ✅ 下载 AI 模型
- ✅ 创建配置文件
- ✅ 创建数据目录

---

### 方式 2: 手动安装

适用于：**所有平台（Windows/macOS/Linux）**

#### 1️⃣ 安装 Python

确保安装了 **Python 3.8 或更高版本**

```bash
# 检查 Python 版本
python3 --version  # macOS/Linux
python --version   # Windows
```

#### 2️⃣ 安装 Ollama

**macOS:**
```bash
brew install ollama
# 或者从官网下载: https://ollama.com/download
```

**Linux:**
```bash
curl https://ollama.com/install.sh | sh
```

**Windows:**
从官网下载安装包：https://ollama.com/download

#### 3️⃣ 克隆并安装

```bash
# 克隆项目
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen

# 创建虚拟环境
python3 -m venv venv      # macOS/Linux
python -m venv venv       # Windows

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 4️⃣ 下载 AI 模型

```bash
# 启动 Ollama 服务
ollama serve

# 在另一个终端下载模型
ollama pull qwen2.5vl:3b          # 视觉模型 (~3GB)
ollama pull mxbai-embed-large     # 嵌入模型 (~500MB)
```

#### 5️⃣ 启动应用

**默认 Kivy UI（推荐）：**
```bash
python start.py
```

**可选 Flutter UI：**
```bash
./start_flutter.sh
```

---

### 方式 3: Docker 运行（最简单）

适用于：**所有支持 Docker 的平台**

```bash
# 使用 Docker Compose
git clone https://github.com/smileformylove/MemScreen.git && cd MemScreen
docker-compose -f setup/docker/docker-compose.yml up -d
```

详见：[Docker 部署指南](DOCKER.md)

---

## 🎯 Flutter 前端（可选）

MemScreen 支持双前端架构：

### 默认：Kivy UI
- 原生 Python 桌面应用
- 使用 `python start.py` 启动
- macOS 悬浮球模式
- 完整功能支持

### 可选：Flutter UI
- 跨平台桌面/移动客户端
- 通过 HTTP 与后端通信
- **启动方式：**
  ```bash
  ./start_flutter.sh
  ```
- 自动处理：
  - 激活虚拟环境
  - 启动 API 后端
  - 安装 Flutter 依赖
  - 启动 Flutter 应用
- **功能特性：**
  - 📱 Chat 界面（流式对话、模型切换、历史记录）
  - 📊 Process 分析（会话列表、分析、删除）
  - 🎥 Recording（全屏/单屏/区域录制）
  - 🎬 Videos（视频列表、播放、删除）
  - ⚙️ Settings（API 配置、关于信息）

详见：[Flutter 文档](FLUTTER.md)

---

## 🐛 常见问题

### Q1: Python 版本太低
```bash
# macOS
brew install python3

# Ubuntu
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# Windows
# 从 https://www.python.org/downloads/ 下载安装
```

### Q2: 虚拟环境激活失败
```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# 如果遇到 PowerShell 执行策略限制：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q3: Ollama 服务无法启动
```bash
# 检查 Ollama 是否已安装
which ollama  # macOS/Linux
where ollama  # Windows

# 手动启动 Ollama
ollama serve

# 查看日志
tail -f ~/.ollama/logs/server.log
```

### Q4: 模型下载失败
```bash
# 使用代理（如果在墙内）
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# 重新下载
ollama pull qwen2.5vl:3b
```

### Q5: 依赖安装失败
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像源（中国用户）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q6: 悬浮球不显示（macOS Kivy）
```bash
# 确保已授予屏幕录制权限
# 系统偏好设置 → 隐私与安全性 → 屏幕录制
# 勾选 MemScreen

# 重启应用
python start.py
```

### Q7: Flutter 连接后端失败
```bash
# 确保后端正在运行
# 后端默认运行在 http://127.0.0.1:8765

# 检查后端状态
curl http://127.0.0.1:8765/health

# 在 Flutter 中重新配置 API URL
# Settings → API URL → 输入正确的地址
```

---

## 📝 验证安装

运行以下命令验证安装：

```bash
# 检查 Python
python --version

# 检查依赖
pip list | grep memscreen

# 检查 Ollama
ollama list

# 检查模型
ollama list | grep qwen2.5vl
ollama list | grep mxbai-embed-large

# 运行应用（Kivy）
python start.py

# 或运行应用（Flutter）
./start_flutter.sh
```

---

## 📚 下一步

- 📖 阅读 [用户指南](USER_GUIDE.md)
- 📱 查看 [Flutter 文档](FLUTTER.md)
- 📚 查看 [完整文档](../README.md)
- 💬 加入 [讨论区](https://github.com/smileformylove/MemScreen/discussions)
- 🐛 [报告问题](https://github.com/smileformylove/MemScreen/issues)

---

## 📞 获取帮助

- **Email**: jixiangluo85@gmail.com
- **GitHub Issues**: https://github.com/smileformylove/MemScreen/issues
- **Discussions**: https://github.com/smileformylove/MemScreen/discussions

---

**祝您使用愉快！🦉**
