#!/bin/bash
################################################################################
# MemScreen Ubuntu 
# MemScreen
################################################################################

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_NAME="MemScreen"
PROJECT_ROOT="$(pwd)"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🗑️  MemScreen ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 
if [ ! -f "start.py" ]; then
    echo -e "${RED}: MemScreen${NC}"
    echo ": cdMemScreen"
    exit 1
fi

echo -e "${YELLOW}: ${PROJECT_ROOT}${NC}"
echo ""
echo -e "${RED}: :${NC}"
echo "  • Python (venv/)"
echo "  •  (db/)"
echo "  •  (*.log)"
echo "  •  (build/, dist/)"
echo "  • Python (__pycache__)"
echo ""

# 
read -p "MemScreen? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/6] ...${NC}"
# MemScreen
pkill -9 -f "python start.py" 2>/dev/null || true
pkill -9 -f "MemScreen" 2>/dev/null || true
echo -e "${GREEN}${NC}"

echo -e "${YELLOW}[2/6] ...${NC}"
# 
if [ -f "$HOME/Desktop/MemScreen.desktop" ]; then
    rm -f "$HOME/Desktop/MemScreen.desktop"
    echo -e "${GREEN}${NC}"
else
    echo -e "${YELLOW}${NC}"
fi

# 
if [ -f "$HOME/.local/share/applications/MemScreen.desktop" ]; then
    rm -f "$HOME/.local/share/applications/MemScreen.desktop"
    echo -e "${GREEN}${NC}"
fi

echo -e "${YELLOW}[3/6] ...${NC}"
# 
read -p "? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 
    rm -rf db/
    rm -f *.log 2>/dev/null || true
    echo -e "${GREEN}${NC}"
else
    echo -e "${YELLOW}${NC}"
    echo ": $PROJECT_ROOT/db/"
fi

echo -e "${YELLOW}[4/6] ...${NC}"
# 
if [ -d "venv" ]; then
    rm -rf venv/
    echo -e "${GREEN}${NC}"
else
    echo -e "${YELLOW}${NC}"
fi

echo -e "${YELLOW}[5/6] ...${NC}"
# 
rm -rf build/
rm -rf dist/
rm -rf *.AppImage 2>/dev/null || true
rm -rf *.tar.gz 2>/dev/null || true
rm -rf MemScreen.AppDir 2>/dev/null || true
rm -rf __pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}${NC}"

echo -e "${YELLOW}[6/6] ...${NC}"
# 
if [ -f "run_memscreen.sh" ]; then
    rm -f run_memscreen.sh
    echo -e "${GREEN}${NC}"
fi

# 
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 
REMAINING=$(find . -mindepth 1 -maxdepth 1 ! -name "uninstall_ubuntu.sh" 2>/dev/null | wc -l)
if [ $REMAINING -gt 0 ]; then
    echo -e "${YELLOW}:${NC}"
    find . -mindepth 1 -maxdepth 1 ! -name "uninstall_ubuntu.sh" -print
    echo ""
    echo -e "${YELLOW}:${NC}"
    echo "  cd .. && rm -rf $(basename "$PROJECT_ROOT")"
else
    echo -e "${GREEN}${NC}"
    echo ""
    echo -e "${YELLOW}:${NC}"
    echo "  cd .. && rm -rf $(basename "$PROJECT_ROOT")"
fi

echo ""
echo -e "${BLUE}MemScreen${NC}"
