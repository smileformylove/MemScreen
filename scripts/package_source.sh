#!/bin/bash
################################################################################
# MemScreen 源代码打包脚本
# 创建可分发的tar.gz包
################################################################################

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

VERSION="0.5.0"
APP_NAME="MemScreen"
PROJECT_ROOT="$(pwd)"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  📦 打包 MemScreen for Ubuntu${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if we're in the project root
if [ ! -f "start.py" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Clean temporary files
echo -e "${YELLOW}清理临时文件...${NC}"
rm -rf build dist *.tar.gz __pycache__ memscreen/__pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Create installer package
echo -e "${YELLOW}创建安装包...${NC}"
INSTALLER_DIR="${APP_NAME}-installer"
rm -rf "$INSTALLER_DIR"
mkdir -p "$INSTALLER_DIR"

# Copy essential files
cp -r memscreen "$INSTALLER_DIR/"
cp -r assets "$INSTALLER_DIR/"
cp start.py "$INSTALLER_DIR/"
cp scripts/install_ubuntu.sh "$INSTALLER_DIR/"
cp README.md "$INSTALLER_DIR/" 2>/dev/null || true

# Create README
cat > "$INSTALLER_DIR/INSTALL.txt" << EOF
MemScreen v${VERSION} - Ubuntu 安装包
========================================

快速安装：
1. 运行安装脚本：./install_ubuntu.sh
2. 运行应用：./run_memscreen.sh

系统要求：
- Ubuntu 20.04 或更高版本
- Python 3.8+
- 4GB 内存
- 10GB 可用磁盘空间

手动安装：
如果自动安装失败，请参考：
https://github.com/smileformylove/MemScreen

功能特性：
✓ AI驱动的屏幕记忆系统
✓ 支持中文界面
✓ 智能搜索和分类
✓ 视觉理解能力

更多信息和更新：
https://github.com/smileformylove/MemScreen
EOF

# Create tar.gz package
echo -e "${YELLOW}压缩文件...${NC}"
tar -czf "${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz" "$INSTALLER_DIR"

# Calculate checksum
echo -e "${YELLOW}生成校验和...${NC}"
SHA256=$(sha256sum "${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz" | awk '{print $1}')
echo "$SHA256  ${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz" > "${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz.sha256"

# Cleanup
rm -rf "$INSTALLER_DIR"

# Get package size
SIZE=$(du -h "${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz" | cut -f1)

# Display result
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ 打包完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "输出文件：${BLUE}${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz${NC}"
echo -e "文件大小：${YELLOW}${SIZE}${NC}"
echo -e "SHA256:   ${YELLOW}${SHA256}${NC}"
echo ""
echo -e "${YELLOW}用户安装方法：${NC}"
echo -e "  1. 下载: wget [URL]${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz"
echo -e "  2. 解压: tar -xzf ${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz"
echo -e "  3. 安装: cd ${APP_NAME}-installer && ./install_ubuntu.sh"
echo -e "  4. 运行: ./run_memscreen.sh"
echo ""
echo -e "${GREEN}准备分发！🚀${NC}"
