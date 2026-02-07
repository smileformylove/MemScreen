# MemScreen 快速安装指南

## 🚀 三种安装方式

### 方式 1: 一键安装（推荐）

适用于：**macOS 和 Linux 用户**

```bash
# 克隆项目
git clone https://github.com/smileformylove/MemScreen.git && cd MemScreen

# 运行一键安装脚本
chmod +x install.sh
./install.sh

# 启动应用
./run.sh
```

**安装脚本会自动：**
- ✅ 检查 Python 版本
- ✅ 创建虚拟环境
- ✅ 安装所有依赖
- ✅ 检查/安装 Ollama
- ✅ 下载 AI 模型
- ✅ 创建配置文件
- ✅ 创建数据目录

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

```bash
python start.py
```

### 方式 3: Docker 运行（最简单）

适用于：**所有支持 Docker 的平台**

```bash
# 使用 Docker Compose
git clone https://github.com/smileformylove/MemScreen.git && cd MemScreen
docker-compose -f setup/docker/docker-compose.yml up -d
```

详见：[Docker 部署指南](DOCKER.md)

---

## 🎯 开发者设置

如果你是开发者，想贡献代码：

```bash
# 克隆项目
git clone https://github.com/smileformylove/MemScreen.git && cd MemScreen

# 运行开发环境设置脚本
chmod +x setup-dev.sh
./setup-dev.sh

# 运行测试
pytest tests/

# 代码格式化
black memscreen/

# 类型检查
mypy memscreen/
```

详见：[开发者指南](CONTRIBUTING.md)

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

### Q6: 悬浮球不显示（macOS）
```bash
# 确保已授予屏幕录制权限
# 系统偏好设置 → 隐私与安全性 → 屏幕录制
# 勾选 MemScreen

# 重启应用
python start.py
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

# 运行应用
python start.py
```

---

## 🎓 下一步

- 📖 阅读 [用户指南](USER_GUIDE.md)
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
