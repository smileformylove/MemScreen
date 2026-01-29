#!/bin/bash
# Manual build and release script for macOS
# Use this if GitHub Actions fails

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

APP_NAME="MemScreen"
VERSION="0.4.1"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}MemScreen Manual Build Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check PyInstaller
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}Installing PyInstaller...${NC}"
    python3 -m pip install --user pyinstaller
fi

# Check if we have dependencies
if [ ! -d "venv" ]; then
    echo -e "${RED}No virtual environment found!${NC}"
    echo -e "${YELLOW}Creating one and installing dependencies...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install pyinstaller
    pip install -r requirements.txt || echo "Requirements.txt not found, installing manually..."
else
    source venv/bin/activate
fi

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf build dist

# Build
echo -e "${YELLOW}Building with PyInstaller...${NC}"
pyinstaller --clean MemScreen.spec

# Check if build succeeded
if [ ! -d "dist" ]; then
    echo -e "${RED}Build failed! No dist directory created.${NC}"
    exit 1
fi

# List what was created
echo -e "${GREEN}Build output:${NC}"
ls -lh dist/

# Create distribution
PLATFORM=$(uname -s)
case $PLATFORM in
    Darwin)
        echo -e "${YELLOW}Creating macOS distribution...${NC}"
        if [ -d "dist/MemScreen.app" ]; then
            cd dist
            zip -r "${APP_NAME}-${VERSION}-macos.zip" "MemScreen.app"
            echo -e "${GREEN}✓ Created: ${APP_NAME}-${VERSION}-macos.zip${NC}"
            cd ..
        else
            echo -e "${RED}MemScreen.app not found!${NC}"
        fi
        ;;
    Linux)
        echo -e "${YELLOW}Creating Linux distribution...${NC}"
        if [ -d "dist/MemScreen" ]; then
            cd dist
            tar -czf "${APP_NAME}-${VERSION}-linux.tar.gz" "MemScreen"
            echo -e "${GREEN}✓ Created: ${APP_NAME}-${VERSION}-linux.tar.gz${NC}"
            cd ..
        else
            echo -e "${RED}MemScreen directory not found!${NC}"
        fi
        ;;
    *)
        echo -e "${RED}Unknown platform: $PLATFORM${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "To create a GitHub Release manually:"
echo "1. Go to: https://github.com/smileformylove/MemScreen/releases/new"
echo "2. Select tag: v${VERSION}"
echo "3. Upload the zip/tar.gz file from dist/"
echo "4. Publish the release"
echo ""
