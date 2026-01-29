#!/bin/bash
# MemScreen 本地构建脚本 - macOS
# 这个脚本会在本地构建应用，然后可以手动上传到 GitHub Release

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

APP_NAME="MemScreen"
VERSION="0.4.1"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       MemScreen macOS 本地构建和发布工具                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查当前目录
if [ ! -f "MemScreen.spec" ]; then
    echo -e "${RED}❌ 请在 MemScreen 项目根目录运行此脚本${NC}"
    exit 1
fi

# 1. 检查 Python 环境
echo -e "${YELLOW}📋 步骤 1/6: 检查 Python 环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 Python 3${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ ${PYTHON_VERSION}${NC}"

# 2. 检查 PyInstaller
echo -e "${YELLOW}📦 步骤 2/6: 检查 PyInstaller...${NC}"
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}正在安装 PyInstaller...${NC}"
    python3 -m pip install --user pyinstaller
fi
PYINSTALLER_VERSION=$(python3 -c "import PyInstaller; print(PyInstaller.__version__)")
echo -e "${GREEN}✓ PyInstaller ${PYINSTALLER_VERSION}${NC}"

# 3. 安装依赖（使用虚拟环境）
echo -e "${YELLOW}📚 步骤 3/6: 安装项目依赖...${NC}"

if [ ! -d "venv_build" ]; then
    echo -e "${YELLOW}创建构建虚拟环境...${NC}"
    python3 -m venv venv_build
fi

echo -e "${YELLOW}激活虚拟环境并安装依赖...${NC}"
source venv_build/bin/activate

# 升级 pip
pip install --upgrade pip -q

# 检查 requirements.txt
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}从 requirements.txt 安装依赖...${NC}"
    echo -e "${YELLOW}这可能需要 5-10 分钟，请耐心等待...${NC}"

    # 分批安装，避免一次性安装太多
    echo "  [1/4] 安装基础依赖..."
    pip install pyinstaller pydantic pillow numpy -q

    echo "  [2/4] 安装 AI 相关依赖..."
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu -q

    echo "  [3/4] 安装其他依赖..."
    pip install opencv-python easyocr kivy -q

    echo "  [4/4] 安装剩余依赖..."
    pip install -r requirements.txt -q

    echo -e "${GREEN}✓ 所有依赖已安装${NC}"
else
    echo -e "${RED}❌ 未找到 requirements.txt${NC}"
    exit 1
fi

# 4. 清理旧构建
echo -e "${YELLOW}🧹 步骤 4/6: 清理旧构建...${NC}"
rm -rf build dist
echo -e "${GREEN}✓ 已清理${NC}"

# 5. 构建
echo -e "${YELLOW}🔨 步骤 5/6: 使用 PyInstaller 构建...${NC}"
echo -e "${YELLOW}这可能需要 5-10 分钟...${NC}"

pyinstaller --clean MemScreen.spec

if [ ! -d "dist" ]; then
    echo -e "${RED}❌ 构建失败！未找到 dist 目录${NC}"
    exit 1
fi

# 检查构建产物
if [ -d "dist/MemScreen.app" ]; then
    echo -e "${GREEN}✓ MemScreen.app 已创建${NC}"
    APP_SIZE=$(du -sh dist/MemScreen.app | cut -f1)
    echo -e "${GREEN}  大小: ${APP_SIZE}${NC}"
else
    echo -e "${RED}❌ MemScreen.app 未创建${NC}"
    exit 1
fi

# 6. 创建分发包
echo -e "${YELLOW}📦 步骤 6/6: 创建分发包...${NC}"

cd dist

# 创建 zip
echo -e "${YELLOW}压缩应用...${NC}"
zip -qr "${APP_NAME}-${VERSION}-macos.zip" "MemScreen.app"

ZIP_SIZE=$(du -sh "${APP_NAME}-${VERSION}-macos.zip" | cut -f1)
echo -e "${GREEN}✓ 分发包已创建: ${APP_NAME}-${VERSION}-macos.zip (${ZIP_SIZE})${NC}"

cd ..

# 测试应用
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 构建成功完成！${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📍 构建产物位置:${NC}"
echo -e "   dist/MemScreen.app/           (应用程序)"
echo -e "   dist/MemScreen-${VERSION}-macos.zip  (分发包)"
echo ""
echo -e "${YELLOW}📤 上传到 GitHub Release:${NC}"
echo ""
echo "1. 访问: https://github.com/smileformylove/MemScreen/releases/new"
echo "2. 选择标签: v${VERSION}"
echo "3. 拖拽文件: dist/${APP_NAME}-${VERSION}-macos.zip"
echo "4. 标题: MemScreen v${VERSION} - macOS"
echo "5. 说明:"
echo "   - macOS 应用程序包"
echo "   - 双击 MemScreen.app 即可运行"
echo "   - 首次运行会自动检查和安装 Ollama"
echo "6. 点击 'Publish release'"
echo ""
echo -e "${YELLOW}🧪 测试应用:${NC}"
echo "   open dist/MemScreen.app"
echo ""
