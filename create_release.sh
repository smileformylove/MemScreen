#!/bin/bash
# MemScreen GitHub Release Creator
# This script helps you create a GitHub release for the current version

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}MemScreen GitHub Release Creator${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get version from pyproject.toml
VERSION=$(grep "^version = " pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo -e "${YELLOW}Version: ${VERSION}${NC}"

# Check if tag exists
if git rev-parse "v${VERSION}" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Tag v${VERSION} already exists${NC}"
else
    echo -e "${YELLOW}Creating git tag v${VERSION}...${NC}"
    git tag -a "v${VERSION}" -m "Release v${VERSION}"
    git push origin "v${VERSION}"
    echo -e "${GREEN}✓ Tag created and pushed${NC}"
fi

# Check for build artifacts
echo ""
echo -e "${YELLOW}Checking for build artifacts...${NC}"

if [ -d "dist" ]; then
    echo -e "${GREEN}✓ dist/ directory found${NC}"
    echo ""
    echo "Build artifacts:"
    ls -lh dist/ | grep -v "^total" | grep -v "^\." | tail -n +2
else
    echo -e "${YELLOW}⚠ No dist/ directory found${NC}"
    echo "Please run: python build_all.py"
fi

# Open GitHub release page
echo ""
echo -e "${YELLOW}Opening GitHub release page...${NC}"

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "https://github.com/smileformylove/MemScreen/releases/new?tag=v${VERSION}"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "https://github.com/smileformylove/MemScreen/releases/new?tag=v${VERSION}" 2>/dev/null || \
    firefox "https://github.com/smileformylove/MemScreen/releases/new?tag=v${VERSION}" 2>/dev/null || \
    google-chrome "https://github.com/smileformylove/MemScreen/releases/new?tag=v${VERSION}" 2>/dev/null || \
    echo "Please open manually: https://github.com/smileformylove/MemScreen/releases/new?tag=v${VERSION}"
else
    # Windows
    start "https://github.com/smileformylove/MemScreen/releases/new?tag=v${VERSION}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Next Steps:${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "1. Fill in the release title and description"
echo "2. Upload the build artifacts from dist/"
echo "3. Click 'Publish release'"
echo ""
echo "Release notes template: RELEASE_NOTES.md"
echo ""
echo -e "${BLUE}Release page opened in your browser${NC}"
echo ""
