# 📦 MemScreen 下载指南

## 🎉 自动构建系统已启用！

MemScreen 现在使用 GitHub Actions 自动为所有平台构建可执行文件。每次发布新版本时，都会自动生成适用于 **Windows**、**macOS** 和 **Linux** 的安装包。

## 📥 下载预编译版本

### 方法 1：从 GitHub Release 下载（推荐）

1. 访问 [Releases 页面](https://github.com/smileformylove/MemScreen/releases)
2. 找到最新的 Release（例如 v0.4.1）
3. 根据你的操作系统下载对应的文件：
   - **macOS**: `MemScreen-0.4.0-macos.zip`
   - **Windows**: `MemScreen-0.4.0-windows.zip`
   - **Linux**: `MemScreen-0.4.0-linux.zip`

### 方法 2：从 GitHub Actions 下载（开发版本）

如果你想使用最新的开发版本：

1. 访问 [Actions 页面](https://github.com/smileformylove/MemScreen/actions)
2. 点击最近的工作流运行
3. 在页面底部找到 "Artifacts" 部分
4. 下载你需要的平台构建

## 🚀 安装说明

### macOS

```bash
# 1. 下载并解压 MemScreen-0.4.0-macos.zip
# 2. 将 MemScreen.app 拖到应用程序文件夹
# 3. 双击启动

# 或者使用命令行
unzip MemScreen-0.4.0-macos.zip
cp -r MemScreen.app /Applications/
open /Applications/MemScreen.app
```

**首次运行提示**：
- 如果提示"无法打开，因为无法验证开发者"，右键点击应用，选择"打开"
- 应用会自动检查并安装 Ollama 和 AI 模型

### Windows

```powershell
# 1. 下载并解压 MemScreen-0.4.0-windows.zip
# 2. 进入解压目录
cd MemScreen

# 3. 运行应用
.\MemScreen.exe
```

**前提条件**：
- 安装 [Ollama](https://ollama.com/download)
- 下载 AI 模型：
  ```powershell
  ollama pull qwen2.5vl:3b
  ollama pull mxbai-embed-large
  ```

### Linux

```bash
# 1. 下载并解压 MemScreen-0.4.0-linux.zip
tar -xzf MemScreen-0.4.0-linux.zip

# 2. 进入目录
cd MemScreen

# 3. 运行应用
./MemScreen
```

**前提条件**：
- 安装 Ollama:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```
- 下载 AI 模型：
  ```bash
  ollama pull qwen2.5vl:3b
  ollama pull mxbai-embed-large
  ```

## 🔧 系统要求

### 硬件要求
- **RAM**: 8GB 最低（16GB 推荐）
- **存储**: 5GB 可用空间
- **CPU**: 支持 AVX 指令集的现代 CPU

### 软件要求
- **macOS**: 10.15 (Catalina) 或更高版本
- **Windows**: Windows 10 或更高版本
- **Linux**: Ubuntu 20.04+, Debian 11+, Fedora 35+
- **Ollama**: 用于运行 AI 模型

## 📋 首次运行

首次运行 MemScreen 时，应用会：

1. ✅ 检查 Ollama 是否已安装
2. ✅ 检查 AI 模型是否已下载
3. ✅ 如果需要，提示你安装依赖
4. ✅ 自动启动 Ollama 服务
5. ✅ 初始化 MemScreen 应用

### 下载 AI 模型

首次运行需要下载约 2.5GB 的 AI 模型：

```bash
# 视觉模型（~2GB）
ollama pull qwen2.5vl:3b

# 嵌入模型（~470MB）
ollama pull mxbai-embed-large
```

下载过程可能需要 10-20 分钟，取决于你的网络速度。

## 🐛 故障排除

### 应用无法启动

**macOS**:
```bash
# 移除隔离属性
xattr -cr /Applications/MemScreen.app
```

**Windows**:
- 确保已安装 [Ollama](https://ollama.com/download)
- 检杀毒软件是否阻止了应用运行

**Linux**:
```bash
# 添加执行权限
chmod +x MemScreen/MemScreen
```

### 模型下载失败

如果 Ollama 模型下载失败：

1. 检查网络连接
2. 尝试手动下载：
   ```bash
   ollama pull qwen2.5vl:3b
   ollama pull mxbai-embed-large
   ```
3. 如果在中国，可能需要配置代理

### 性能问题

如果应用运行缓慢：

1. 关闭其他应用释放内存
2. 确保 Ollama 服务正在运行：`ollama serve`
3. 检查系统资源使用情况

## 🔄 自动更新

当新版本发布时：

1. 访问 [Releases 页面](https://github.com/smileformylove/MemScreen/releases)
2. 下载最新版本
3. 替换旧版本（配置文件会保留）

## 📚 更多资源

- **主项目**: https://github.com/smileformylove/MemScreen
- **文档**: [README.md](https://github.com/smileformylove/MemScreen/blob/main/README.md)
- **打包指南**: [PACKAGING.md](https://github.com/smileformylove/MemScreen/blob/main/PACKAGING.md)
- **问题反馈**: [Issues](https://github.com/smileformylove/MemScreen/issues)

## 🤝 贡献

如果你想为 MemScreen 做贡献：

1. Fork 项目
2. 创建特性分支
3. 提交 Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](https://github.com/smileformylove/MemScreen/blob/main/LICENSE)

---

**需要帮助？** 请在 [GitHub Issues](https://github.com/smileformylove/MemScreen/issues) 中提问
