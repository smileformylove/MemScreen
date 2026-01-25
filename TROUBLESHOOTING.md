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

如果缺少依赖，运行：

```bash
pip3 install -e .
```

这会安装所有必需的包（根据pyproject.toml）。

---

## ❓ 常见问题

### 1. ModuleNotFoundError: No module named 'pydantic'

**解决方法**:
```bash
pip3 install pydantic
```

### 2. 找不到命令 memscreen-ui

**解决方法**: 使用 `python3 -m memscreen.ui` 或 `./run_ui.sh`

### 3. tkinter 相关错误

**解决方法**:
```bash
# macOS
brew install python-tk

# Ubuntu/Debian
sudo apt-get install python3-tk
```

### 4. Ollama 连接失败

**解决方法**:
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

1. **安装依赖**（首次使用）
   ```bash
   pip3 install -e .
   ```

2. **启动Ollama**（需要AI功能）
   ```bash
   ollama serve
   ```

3. **启动MemScreen**
   ```bash
   ./run_ui.sh
   ```

就这么简单！🎉
