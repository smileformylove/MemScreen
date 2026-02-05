# Ubuntu 分发包创建指南

## 📦 分发策略

由于PyInstaller打包需要大量内存，我们采用**源代码分发**的方式，提供简单的安装脚本。

## 🚀 快速打包

### 方法一：创建源代码压缩包（推荐）

```bash
./package_source.sh
```

这会创建一个包含所有源代码和安装脚本的tar.gz包。

### 方法二：创建安装脚本

直接使用 `install_ubuntu.sh` 作为安装包。

## 📝 打包步骤

### 1. 清理临时文件

```bash
rm -rf build dist *.tar.gz __pycache__ memscreen/__pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete
```

### 2. 创建源代码包

```bash
VERSION="0.5.0"
tar -czf MemScreen-${VERSION}-source.tar.gz \
    --exclude='.git' \
    --exclude='build' \
    --exclude='dist' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.gitignore' \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='db' \
    --exclude='*.db' \
    --exclude='*.log' \
    .
```

### 3. 创建安装包

```bash
# 将源代码和安装脚本打包
mkdir -p MemScreen-installer
cp -r memscreen assets start.py install_ubuntu.sh MemScreen-installer/
cat > MemScreen-installer/README.txt << 'EOF'
MemScreen 安装说明
==================

安装方法：
1. 解压到任意目录
2. 运行安装脚本：./install_ubuntu.sh
3. 安装完成后运行：./run_memscreen.sh

或者双击桌面上的MemScreen图标

系统要求：
- Ubuntu 20.04 或更高版本
- Python 3.8+
- 至少4GB内存
- 10GB可用磁盘空间

更多信息请访问：https://github.com/smileformylove/MemScreen
EOF
tar -czf MemScreen-installer.tar.gz MemScreen-installer/
rm -rf MemScreen-installer
```

## 📂 分发包结构

### 源代码包

```
MemScreen-0.5.0-source.tar.gz
├── memscreen/          # 源代码
├── assets/            # 资源文件
├── start.py           # 启动脚本
├── install_ubuntu.sh  # 安装脚本
├── requirements.txt   # Python依赖
└── README.md          # 说明文档
```

### 安装包

```
MemScreen-installer.tar.gz
├── memscreen/          # 源代码
├── assets/            # 资源文件
├── start.py           # 启动脚本
├── install_ubuntu.sh  # 自动安装脚本
└── README.txt         # 快速开始指南
```

## 🌐 分发方式

### 1. GitHub Releases

```bash
# 创建tag
git tag -a v0.5.0 -m "Release version 0.5.0"
git push origin v0.5.0

# 上传到GitHub Releases
gh release create v0.5.0 \
    --title "MemScreen v0.5.0 for Ubuntu" \
    --notes "See CHANGELOG.md for details" \
    MemScreen-installer.tar.gz \
    MemScreen-0.5.0-source.tar.gz
```

### 2. 直接下载链接

用户可以通过以下方式下载：

```bash
# 下载安装包
wget https://github.com/smileformylove/MemScreen/releases/download/v0.5.0/MemScreen-installer.tar.gz

# 解压
tar -xzf MemScreen-installer.tar.gz
cd MemScreen-installer

# 安装
./install_ubuntu.sh
```

### 3. Launchpad PPA（高级）

创建PPA以便用户通过apt安装：

```bash
# 需要Launchpad账号
# 详细步骤：https://help.launchpad.net/Packaging/PPA/BuildingASourcePackage
```

## 📋 用户安装指南

### 快速安装

```bash
# 1. 下载
wget https://github.com/smileformylove/MemScreen/releases/download/v0.5.0/MemScreen-installer.tar.gz

# 2. 解压
tar -xzf MemScreen-installer.tar.gz
cd MemScreen-installer

# 3. 安装
chmod +x install_ubuntu.sh
./install_ubuntu.sh

# 4. 运行
./run_memscreen.sh
```

### 手动安装

```bash
# 1. 安装系统依赖
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv \
    portaudio19-dev libopencv-dev python3-opencv

# 2. 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 3. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 4. 安装Python依赖
pip install pydantic kivy ollama chromadb opencv-python numpy pillow

# 5. 运行
python start.py
```

## 🔧 故障排除

### 问题1：权限错误

```bash
chmod +x install_ubuntu.sh
sudo ./install_ubuntu.sh
```

### 问题2：Python版本不兼容

```bash
# 使用python3.8或更高版本
python3 --version
```

### 问题3：Ollama无法启动

```bash
# 手动启动Ollama服务
ollama serve
```

## 📊 版本管理

### 发布新版本

1. 更新版本号
2. 更新CHANGELOG.md
3. 创建Git tag
4. 构建分发包
5. 上传到GitHub Releases
6. 更新文档

### 版本号格式

```
v主版本.次版本.修订版本

例如：v0.5.0
- 主版本：0（开发中）
- 次版本：5（功能迭代）
- 修订版本：0（bug修复）
```

## 🎯 下一步

- [ ] 添加自动更新功能
- [ ] 创建Snap包
- [ ] 创建Flatpak包
- [ ] 添加自动安装脚本
- [ ] 提供Docker镜像

## 📚 相关资源

- [Ubuntu打包指南](https://packaging.ubuntu.com/)
- [Python打包指南](https://packaging.python.org/)
- [PyInstaller文档](https://pyinstaller.org/)
