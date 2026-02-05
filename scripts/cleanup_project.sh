#!/bin/bash
################################################################################
# MemScreen 项目清理脚本
# 整理项目文件，删除临时和不必要的文件
################################################################################

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🧹 清理 MemScreen 项目目录${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 询问确认
echo -e "${YELLOW}此操作将:${NC}"
echo "  • 删除临时文件（appimagetool, node_modules等）"
echo "  • 删除Python缓存（__pycache__, *.pyc, *.egg-info）"
echo "  • 删除旧的安装包"
echo "  • 移动文档到docs/目录"
echo "  • 删除重复的脚本"
echo ""
read -p "确认要整理项目目录吗? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}取消整理${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/8] 删除临时文件...${NC}"
rm -f appimagetool
rm -f *.tar.gz 2>/dev/null || true
rm -f *.sha256 2>/dev/null || true
echo -e "${GREEN}✓ 临时文件已删除${NC}"

echo -e "${YELLOW}[2/8] 删除Python缓存...${NC}"
rm -rf memscreen.egg-info
rm -rf __pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✓ Python缓存已清理${NC}"

echo -e "${YELLOW}[3/8] 删除Node.js文件...${NC}"
rm -rf node_modules
rm -f package-lock.json
echo -e "${GREEN}✓ Node.js文件已删除${NC}"

echo -e "${YELLOW}[4/8] 移动文档到docs/目录...${NC}"
# 移动根目录的md文档到docs目录
if [ -f "UBUNTU_PACKAGE_SUMMARY.md" ]; then
    mv UBUNTU_PACKAGE_SUMMARY.md docs/
    echo -e "${GREEN}  ✓ 移动 UBUNTU_PACKAGE_SUMMARY.md${NC}"
fi

echo -e "${YELLOW}[5/8] 删除重复的脚本...${NC}"
# 保留主要的脚本，删除备份/重复的
rm -f build_linux_simple.sh 2>/dev/null || true
rm -f build_ubuntu.sh 2>/dev/null || true
echo -e "${GREEN}✓ 重复脚本已删除${NC}"

echo -e "${YELLOW}[6/8] 清理构建目录...${NC}"
rm -rf build dist
echo -e "${GREEN}✓ 构建目录已清理${NC}"

echo -e "${YELLOW}[7/8] 整理项目结构...${NC}"
# 确保所有必要的目录都存在
mkdir -p docs/{history,images}
mkdir -p packaging/{linux,macos,windows}
mkdir -p tests

# 创建releases目录用于存放分发包
mkdir -p releases
echo -e "${GREEN}✓ 项目结构已整理${NC}"

echo -e "${YELLOW}[8/8] 显示当前状态...${NC}"
echo ""
echo -e "${GREEN}整理完成！当前项目结构:${NC}"
echo ""

# 显示目录结构
echo "📁 核心目录:"
ls -1 | grep -E "^(memscreen|assets|tests|docs|packaging|pyinstaller|docker|install|examples|tools)$" | sort

echo ""
echo "📄 主要文件:"
ls -1 | grep -E "^(start|README|LICENSE|pyproject|config_example|package_source|install_ubuntu|uninstall_ubuntu)" | sort

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ 清理完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
