#!/bin/bash
################################################################################
# MemScreen 
# 
################################################################################

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🧹  MemScreen ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 
echo -e "${YELLOW}:${NC}"
echo "  • appimagetool, node_modules"
echo "  • Python__pycache__, *.pyc, *.egg-info"
echo "  • "
echo "  • docs/"
echo "  • "
echo ""
read -p "? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/8] ...${NC}"
rm -f appimagetool
rm -f *.tar.gz 2>/dev/null || true
rm -f *.sha256 2>/dev/null || true
echo -e "${GREEN}✓ ${NC}"

echo -e "${YELLOW}[2/8] Python...${NC}"
rm -rf memscreen.egg-info
rm -rf __pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✓ Python${NC}"

echo -e "${YELLOW}[3/8] Node.js...${NC}"
rm -rf node_modules
rm -f package-lock.json
echo -e "${GREEN}✓ Node.js${NC}"

echo -e "${YELLOW}[4/8] docs/...${NC}"
# mddocs
if [ -f "UBUNTU_PACKAGE_SUMMARY.md" ]; then
    mv UBUNTU_PACKAGE_SUMMARY.md docs/
    echo -e "${GREEN}  ✓  UBUNTU_PACKAGE_SUMMARY.md${NC}"
fi

echo -e "${YELLOW}[5/8] ...${NC}"
# /
rm -f build_linux_simple.sh 2>/dev/null || true
rm -f build_ubuntu.sh 2>/dev/null || true
echo -e "${GREEN}✓ ${NC}"

echo -e "${YELLOW}[6/8] ...${NC}"
rm -rf build dist
echo -e "${GREEN}✓ ${NC}"

echo -e "${YELLOW}[7/8] ...${NC}"
# 
mkdir -p docs/{history,images}
mkdir -p packaging/{linux,macos,windows}
mkdir -p tests

# releases
mkdir -p releases
echo -e "${GREEN}✓ ${NC}"

echo -e "${YELLOW}[8/8] ...${NC}"
echo ""
echo -e "${GREEN}:${NC}"
echo ""

# 
echo "📁 :"
ls -1 | grep -E "^(memscreen|assets|tests|docs|packaging|pyinstaller|docker|install|examples|tools)$" | sort

echo ""
echo "📄 :"
ls -1 | grep -E "^(start|README|LICENSE|pyproject|config_example|package_source|install_ubuntu|uninstall_ubuntu)" | sort

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
