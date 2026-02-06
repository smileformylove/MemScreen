# Bin Directory - 可执行脚本

本目录包含 MemScreen 的所有可执行启动脚本。

## 📋 脚本列表

| 脚本 | 说明 | 使用场景 |
|------|------|----------|
| `run_ui.sh` | 主UI启动脚本 | 从源码运行MemScreen |
| `run_memscreen.sh` | 安装版启动脚本 | Ubuntu安装版使用 |

## 🚀 快速启动

### 方式1：使用根目录快捷脚本
```bash
./run.sh
```

### 方式2：直接运行
```bash
./bin/run_ui.sh
```

### 方式3：使用Python
```bash
python3 start.py
```

## 📝 与其他脚本目录的区别

- **`bin/`** - 可执行启动脚本（用户日常使用）
- **`scripts/`** - 维护和安装脚本（开发者/安装时使用）
- **`install/`** - 平台安装脚本（首次安装使用）
- **`packaging/`** - 打包构建脚本（打包发布使用）
