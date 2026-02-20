#!/bin/bash
################################################################################
# MemScreen 
# tar.gz
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
echo -e "${BLUE}  📦  MemScreen for Ubuntu${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if we're in the project root
if [ ! -f "start.py" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Clean temporary files
echo -e "${YELLOW}...${NC}"
rm -rf build dist *.tar.gz __pycache__ memscreen/__pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Create installer package
echo -e "${YELLOW}...${NC}"
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
MemScreen v${VERSION} - Ubuntu 
========================================


1. ./install_ubuntu.sh
2. ./run_memscreen.sh


- Ubuntu 20.04 
- Python 3.8+
- 4GB 
- 10GB 



https://github.com/smileformylove/MemScreen


✓ AI
✓ 
✓ 
✓ 


https://github.com/smileformylove/MemScreen
EOF

# Create tar.gz package
echo -e "${YELLOW}...${NC}"
tar -czf "${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz" "$INSTALLER_DIR"

# Calculate checksum
echo -e "${YELLOW}...${NC}"
SHA256=$(sha256sum "${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz" | awk '{print $1}')
echo "$SHA256  ${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz" > "${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz.sha256"

# Cleanup
rm -rf "$INSTALLER_DIR"

# Get package size
SIZE=$(du -h "${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz" | cut -f1)

# Display result
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz${NC}"
echo -e "${YELLOW}${SIZE}${NC}"
echo -e "SHA256:   ${YELLOW}${SHA256}${NC}"
echo ""
echo -e "${YELLOW}${NC}"
echo -e "  1. : wget [URL]${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz"
echo -e "  2. : tar -xzf ${APP_NAME}-${VERSION}-ubuntu-installer.tar.gz"
echo -e "  3. : cd ${APP_NAME}-installer && ./install_ubuntu.sh"
echo -e "  4. : ./run_memscreen.sh"
echo ""
echo -e "${GREEN}🚀${NC}"
