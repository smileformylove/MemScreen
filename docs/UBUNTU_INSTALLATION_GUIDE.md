# MemScreen Ubuntu 下载和安装指南

## 📥 下载地址

您可以通过以下方式下载MemScreen：

### 方法一：直接下载

```bash
wget https://github.com/smileformylove/MemScreen/releases/download/v0.5.0/MemScreen-0.5.0-ubuntu-installer.tar.gz
```

### 方法二：使用curl

```bash
curl -L -o MemScreen-0.5.0-ubuntu-installer.tar.gz \
  https://github.com/smileformylove/MemScreen/releases/download/v0.5.0/MemScreen-0.5.0-ubuntu-installer.tar.gz
```

### 方法三：从源代码构建

```bash
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
./package_source.sh
```

## 🔐 验证下载

下载后，请验证文件的完整性：

```bash
# 计算SHA256
sha256sum MemScreen-0.5.0-ubuntu-installer.tar.gz

# 应该输出：
# 757e64ca13b616d086a295342caad4345ddb8dc99fba220087f3e6e7ac606a5b  MemScreen-0.5.0-ubuntu-installer.tar.gz
```

## 📦 系统要求

- **操作系统**: Ubuntu 20.04 LTS 或更高版本
- **Python**: 3.8 或更高版本
- **内存**: 至少 4GB RAM
- **磁盘**: 至少 10GB 可用空间
- **网络**: 需要下载AI模型（约2GB）

## 🚀 快速安装

### 步骤 1：解压文件

```bash
tar -xzf MemScreen-0.5.0-ubuntu-installer.tar.gz
cd MemScreen-installer
```

### 步骤 2：运行安装脚本

```bash
chmod +x install_ubuntu.sh
./install_ubuntu.sh
```

安装脚本会自动：
1. ✅ 更新系统包
2. ✅ 安装系统依赖
3. ✅ 安装Ollama（AI模型运行时）
4. ✅ 创建Python虚拟环境
5. ✅ 安装Python依赖
6. ✅ 创建启动脚本
7. ✅ 创建桌面快捷方式

### 步骤 3：下载AI模型

```bash
# 下载中文模型（推荐）
ollama pull qwen3:1.7b

# 或下载更大的模型
ollama pull qwen2.5vl:3b
```

### 步骤 4：启动应用

```bash
./run_memscreen.sh
```

或者双击桌面上的MemScreen图标。

## 🎯 首次使用

1. **启动Ollama服务**（如果还没启动）：
   ```bash
   ollama serve
   ```

2. **在新终端中运行MemScreen**：
   ```bash
   cd MemScreen-installer
   ./run_memscreen.sh
   ```

3. **界面介绍**：
   - **Chat**: AI聊天界面
   - **Record**: 屏幕录制
   - **Video**: 视频回放
   - **Process**: 进程分析

## 🔧 手动安装（如果自动安装失败）

### 1. 安装系统依赖

```bash
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    portaudio19-dev \
    libopencv-dev \
    python3-opencv
```

### 2. 安装Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 3. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装Python依赖

```bash
pip install --upgrade pip
pip install pydantic kivy ollama chromadb \
            opencv-python numpy pillow pynput mss \
            toolz psutil requests
```

### 5. 运行应用

```bash
python start.py
```

## ❓ 常见问题

### Q1：安装脚本报错"Permission denied"

**A**: 添加执行权限：
```bash
chmod +x install_ubuntu.sh
sudo ./install_ubuntu.sh
```

### Q2：Ollama无法连接

**A**: 手动启动Ollama服务：
```bash
ollama serve
```

### Q3：中文显示乱码

**A**: 安装中文字体：
```bash
sudo apt-get install -y fonts-noto-cjk fonts-wqy-zenhei
```

### Q4：模型回复很慢

**A**: 使用更小的模型：
```bash
ollama pull qwen3:1.7b
```

### Q5：无法录制屏幕

**A**: 安装屏幕录制依赖：
```bash
sudo apt-get install -y ffmpeg
```

## 🗑️ 卸载

删除安装目录即可：
```bash
cd ..
rm -rf MemScreen-installer

# 如果创建了桌面快捷方式
rm ~/Desktop/MemScreen.desktop
```

## 🔄 更新

1. 备份数据（如果有）：
   ```bash
   cp -r MemScreen-installer/db ~/memscreen_backup
   ```

2. 下载新版本并解压

3. 恢复数据：
   ```bash
   cp -r ~/memscreen_backup MemScreen-installer/db
   ```

## 📚 更多资源

- **GitHub**: https://github.com/smileformylove/MemScreen
- **问题反馈**: https://github.com/smileformylove/MemScreen/issues
- **文档**: https://github.com/smileformylove/MemScreen/tree/main/docs

## 💡 提示

- 首次运行可能需要几分钟初始化
- 建议在4核8GB以上的系统上运行
- 定期清理旧的数据库文件以节省空间
- 使用快捷键提高效率：
  - `Ctrl+Tab`: 切换标签页
  - `Ctrl+Enter`: 发送消息
  - `Ctrl+R`: 开始录制
  - `Ctrl+S`: 停止录制

## 🎉 开始使用

安装完成后，您就可以体验MemScreen的强大功能了：

- ✨ **智能记忆**: 自动记录和理解屏幕内容
- 🔍 **语义搜索**: 用自然语言搜索历史记录
- 🤖 **AI助手**: 随时询问关于您活动的问题
- 📹 **视频回放**: 重放任何时间段的屏幕活动

享受使用MemScreen！
