# 🚀 MemScreen 启动指南

## 方法1: 使用启动脚本（推荐）

```bash
./run_ui.sh
```

这个脚本会：
- ✅ 检查Python环境
- ✅ 验证依赖是否安装
- ✅ 自动安装缺失的依赖
- ✅ 启动UI界面

---

## 方法2: 使用Python模块

```bash
python3 -m memscreen.ui
```

---

## 方法3: 使用安装的命令

```bash
memscreen-ui
```

**注意**: 如果这个命令报错，请使用方法1或方法2。

---

## 🔍 诊断问题

如果遇到问题，运行诊断脚本：

```bash
python3 diagnose.py
```

这会检查：
- Python版本和路径
- 所有必需的依赖
- memscreen包是否正确安装
- 各个模块是否可以导入

---

## ⚙️  安装依赖

### 方法1: 使用虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .

# 运行应用
./run_ui.sh
```

### 方法2: 使用 --user 标志

```bash
pip3 install --user -e .
```

### 方法3: 使用 --break-system-packages（不推荐）

```bash
pip3 install --break-system-packages -e .
```

**注意**: 如果遇到 `externally-managed-environment` 错误，说明你使用的是Homebrew或系统管理的Python。请使用方法1（虚拟环境）。

---

## ❓ 常见问题

### 1. error: externally-managed-environment

**症状**: 安装依赖时出现此错误

**原因**: 使用Homebrew或系统管理的Python，不允许直接用pip安装包

**解决方法**（按推荐顺序）:

**方法A: 使用虚拟环境（最推荐）**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
./run_ui.sh
```

**方法B: 使用 --user 标志**
```bash
pip3 install --user -e .
```

**方法C: 使用 --break-system-packages**
```bash
pip3 install --break-system-packages -e .
```

### 2. ModuleNotFoundError: No module named 'pydantic'

**解决方法**:
```bash
# 如果使用虚拟环境
source venv/bin/activate
pip install pydantic

# 或者使用 --user
pip3 install --user pydantic
```

### 3. 找不到命令 memscreen-ui

**解决方法**: 使用 `python3 -m memscreen.ui` 或 `./run_ui.sh`

### 4. tkinter 相关错误
```bash
# macOS
brew install python-tk

# Ubuntu/Debian
sudo apt-get install python3-tk
```

### 5. Ollama 连接失败
```bash
# 启动 Ollama 服务
ollama serve
```

---

## 📝 验证安装

运行以下命令验证：

```bash
# 测试UI模块
python3 -c "from memscreen.ui import MemScreenApp; print('✅ UI OK')"

# 测试配置
python3 -c "from memscreen.config import get_config; print('✅ Config OK')"

# 测试截图
python3 -c "from PIL import ImageGrab; img = ImageGrab.grab(); print('✅ Screenshot OK')"
```

---

## 🎯 快速开始

### 首次使用（推荐：使用虚拟环境）

```bash
# 1. 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装MemScreen
pip install -e .

# 3. 启动Ollama（可选，用于AI功能）
ollama serve

# 4. 启动MemScreen UI
./run_ui.sh
```

### 或者不使用虚拟环境

```bash
# 1. 安装依赖
pip3 install --user -e .

# 2. 启动Ollama（可选）
ollama serve

# 3. 启动MemScreen
python3 -m memscreen.ui
```

就这么简单！🎉
