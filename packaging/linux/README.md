# Ubuntu 打包指南

本文档说明如何在Ubuntu上构建MemScreen的可分发包。

## 📦 打包格式

我们使用 **AppImage** 格式，这是Linux通用的打包格式，可以在大多数Linux发行版上运行。

## 🛠️ 系统要求

- Ubuntu 20.04 或更高版本
- Python 3.8 或更高版本
- 至少 4GB 可用内存
- 10GB 可用磁盘空间

## 📋 前置依赖

### 1. 安装系统依赖

```bash
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    patchelf \
    desktop-file-utils \
    libgdk-pixbuf2.0-0 \
    wget
```

### 2. 安装Python依赖

```bash
cd /path/to/MemScreen
pip3 install -r requirements.txt  # 如果有requirements.txt
# 或者手动安装主要依赖
pip3 install pyinstaller kivy ollama chromadb opencv-python numpy pillow
```

## 🚀 快速构建

### 方法一：使用简化的构建脚本（推荐）

```bash
cd /path/to/MemScreen
./build_ubuntu.sh
```

这个脚本会自动完成所有步骤。

### 方法二：使用完整的构建脚本

```bash
cd /path/to/MemScreen
./packaging/linux/build_appimage.sh
```

## 📝 构建步骤详解

### 步骤 1：构建可执行文件

使用PyInstaller将Python应用打包成可执行文件：

```bash
pyinstaller pyinstaller/memscreen_linux.spec --noconfirm
```

### 步骤 2：创建AppDir目录结构

```bash
mkdir -p MemScreen.AppDir/{usr/bin,usr/lib,usr/share/applications,usr/share/icons/hicolor/256x256/apps}
```

### 步骤 3：复制文件到AppDir

```bash
# 复制可执行文件
cp -r dist/MemScreen/* MemScreen.AppDir/

# 复制桌面文件
cp packaging/linux/memscreen.desktop MemScreen.AppDir/
cp packaging/linux/memscreen.desktop MemScreen.AppDir/usr/share/applications/

# 复制图标
cp assets/logo.png MemScreen.AppDir/memscreen.png
cp assets/logo.png MemScreen.AppDir/.DirIcon
cp assets/logo.png MemScreen.AppDir/usr/share/icons/hicolor/256x256/apps/memscreen.png

# 复制启动脚本
cp packaging/linux/AppRun MemScreen.AppDir/AppRun
chmod +x MemScreen.AppDir/AppRun
```

### 步骤 4：构建AppImage

```bash
# 下载appimagetool
wget -c "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O appimagetool
chmod +x appimagetool

# 构建AppImage
./appimagetool MemScreen.AppDir MemScreen-0.5.0-x86_64.AppImage
chmod +x MemScreen-0.5.0-x86_64.AppImage
```

## 🧪 测试AppImage

构建完成后，在本地测试：

```bash
./MemScreen-0.5.0-x86_64.AppImage
```

如果应用正常启动，说明构建成功。

## 📦 分发

生成的AppImage文件可以直接分发：

```bash
MemScreen-0.5.0-x86_64.AppImage
```

用户只需要：
1. 下载AppImage文件
2. 添加执行权限：`chmod +x MemScreen-0.5.0-x86_64.AppImage`
3. 运行：`./MemScreen-0.5.0-x86_64.AppImage`

## 🔧 故障排除

### 问题1：PyInstaller找不到模块

```bash
# 确保所有依赖都已安装
pip3 install pyinstaller kivy ollama chromadb opencv-python

# 检查spec文件中的hiddenimports
# 编辑 pyinstaller/memscreen_linux.spec
```

### 问题2：AppImage无法运行

```bash
# 检查AppRun脚本是否可执行
chmod +x MemScreen.AppDir/AppRun

# 检查可执行文件是否存在
ls -l MemScreen.AppDir/
```

### 问题3：缺少系统库

```bash
# 安装完整的SDL2库
sudo apt-get install -y libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-ttf-2.0-0

# 安装OpenCV依赖
sudo apt-get install -y libopencv-dev python3-opencv
```

## 📂 文件结构

构建后的AppImage内部结构：

```
MemScreen.AppDir/
├── AppRun                              # 启动脚本
├── memscreen.desktop                   # 桌面文件
├── memscreen.png                       # 图标
├── .DirIcon                            # 目录图标
├── usr/
│   ├── bin/
│   │   └── MemScreen                  # 可执行文件
│   ├── lib/                           # 共享库
│   └── share/
│       ├── applications/
│       │   └── memscreen.desktop
│       └── icons/
│           └── hicolor/256x256/apps/
│               └── memscreen.png
└── [其他依赖文件]
```

## 🚀 自动化构建

对于自动化构建，可以使用CI/CD：

```yaml
# .github/workflows/build-linux.yml 示例
name: Build Linux AppImage

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y patchelf desktop-file-utils
          pip3 install pyinstaller kivy ollama chromadb opencv-python

      - name: Build AppImage
        run: ./build_ubuntu.sh

      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: MemScreen-Linux
          path: MemScreen-*.AppImage
```

## 📚 相关资源

- [AppImage官方文档](https://docs.appimage.org/)
- [PyInstaller文档](https://pyinstaller.org/)
- [Kivy打包指南](https://kivy.org/doc/stable/guide/packaging.html)

## 💡 提示

1. **测试不同Ubuntu版本**：在Ubuntu 20.04、22.04和最新版本上测试
2. **检查依赖完整性**：确保所有Python依赖都在spec文件中列出
3. **优化体积**：使用UPX压缩可执行文件（已在spec中启用）
4. **签名**：考虑对AppImage进行签名以增强安全性

## 🎯 下一步

- [ ] 创建GitHub Releases自动发布
- [ ] 添加自动更新功能
- [ ] 创建Snap包
- [ ] 创建Flatpak包
