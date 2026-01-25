# 📦 安装 MemScreen

## 快速安装（推荐）

### 使用虚拟环境（最佳实践）

```bash
# 1. 克隆仓库
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen

# 2. 创建虚拟环境
python3 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 安装依赖
pip install -e .

# 5. 启动应用
./run_ui.sh
```

---

## 其他安装方法

### 方法2: 使用 --user 标志

```bash
pip3 install --user -e .
python3 -m memscreen.ui
```

### 方法3: 使用 --break-system-packages

```bash
pip3 install --break-system-packages -e .
python3 -m memscreen.ui
```

**注意**: 方法2和3不建议在Homebrew管理的Python上使用。

---

## 依赖要求

- Python 3.8+
- tkinter (通常随Python安装)
- Ollama (可选，用于AI功能)

---

## 验证安装

```bash
# 运行诊断
python3 diagnose.py

# 测试UI导入
python3 -c "from memscreen.ui import MemScreenApp; print('✅ 安装成功!')"
```

---

## 遇到问题？

查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 获取详细的故障排除指南。

常见问题：
- `externally-managed-environment` → 使用虚拟环境
- `ModuleNotFoundError` → 安装依赖: `pip install -e .`
- `找不到命令` → 使用 `python3 -m memscreen.ui`
