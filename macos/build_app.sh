#!/bin/bash
# MemScreen macOS Build Script
# Packages MemScreen as a standalone .app application

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="MemScreen"
APP_VERSION="0.4.0"
APP_IDENTIFIER="com.memscreen.app"
BUILD_DIR="$(pwd)/build"
DIST_DIR="$(pwd)/dist"
SRC_DIR="$(pwd)/.."

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}MemScreen macOS Build Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf "$BUILD_DIR"
rm -rf "$DIST_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"

# Check if py2app is installed
if ! python3 -c "import py2app" 2>/dev/null; then
    echo -e "${YELLOW}Installing py2app...${NC}"
    pip3 install py2app
fi

# Create setup.py for py2app
echo -e "${YELLOW}Creating setup.py...${NC}"
cat > "$BUILD_DIR/setup.py" << 'EOF'
from py2app import Script

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'memscreen.icns',
    'plist': {
        'CFBundleName': 'MemScreen',
        'CFBundleDisplayName': 'MemScreen',
        'CFBundleIdentifier': 'com.memscreen.app',
        'CFBundleVersion': '0.4.0',
        'CFBundleShortVersionString': '0.4.0',
        'NSHumanReadableCopyright': '© 2026 Jixiang Luo',
        'NSHighResolutionCapable': True,
    },
    'packages': [
        'memscreen',
        'memscreen.ui',
        'memscreen.presenters',
        'memscreen.memory',
        'memscreen.llm',
        'memscreen.embeddings',
        'memscreen.vector_store',
        'memscreen.storage',
        'memscreen.telemetry',
        'memscreen.process_mining',
        'memscreen.prompts',
        'memscreen.utils',
        'memscreen.config',
        'memscreen.graph',
    ],
    'includes': [
        'pydantic',
        'requests',
        'PIL',
        'cv2',
        'kivy',
        'kivy.core.window',
        'chroma_db',
        'ollama',
        'pynput',
        'sqlalchemy',
    ],
    'excludes': [
        'test',
        'tests',
        'tkinter',
        'matplotlib',
        'numpy.tests',
    ],
    'site_packages': [
        'pydantic',
        'requests',
        'PIL',
        'PIL._tkinter_finder',
        'cv2',
        'kivy',
        'kivy.core',
        'kivy.graphics',
        'chroma_db',
        'ollama',
        'pynput',
        'sqlalchemy',
        'chromadb',
        'huggingface_hub',
    ],
}

APP = ['start.py']

DATA_FILES = [
    'config_example.yaml',
    'GRAPH_MEMORY_GUIDE.md',
]

EOF

# Copy source files to build directory
echo -e "${YELLOW}Copying source files...${NC}"
cp "$SRC_DIR/start.py" "$BUILD_DIR/"
cp "$SRC_DIR/config_example.yaml" "$BUILD_DIR/" 2>/dev/null || true
cp "$SRC_DIR/GRAPH_MEMORY_GUIDE.md" "$BUILD_DIR/" 2>/dev/null || true

# Create the app bundle
echo ""
echo -e "${YELLOW}Building .app bundle...${NC}"
cd "$BUILD_DIR"

python3 setup.py py2app --dist-dir="$DIST_DIR"

# Check if build was successful
if [ ! -d "$DIST_DIR/$APP_NAME.app" ]; then
    echo -e "${RED}❌ Build failed!${NC}"
    echo "Check the errors above."
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Build successful!${NC}"
echo ""
echo -e "${BLUE}Application created:${NC}"
echo "  $DIST_DIR/$APP_NAME.app"
echo ""

# Create a simple launcher script
echo -e "${YELLOW}Creating launcher script...${NC}"
cat > "$DIST_DIR/$APP_NAME.sh" << EOF
#!/bin/bash
# MemScreen Launcher

SCRIPT_DIR="\$( cd "\$( dirname "\${BASH_SOURCE[0]}" )" && pwd )"
cd "\$SCRIPT_DIR"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found!"
    echo ""
    echo "MemScreen requires Ollama to run AI models."
    echo "Please install Ollama first:"
    echo "  brew install ollama"
    echo ""
    echo "Then download AI models:"
    echo "  ollama pull qwen2.5vl:3b"
    echo "  ollama pull mxbai-embed-large"
    echo ""
    read -p "Press Enter to open Ollama download page..."
    open "https://ollama.com/download"
    exit 1
fi

# Check if Ollama service is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Launch MemScreen
open "$APP_NAME.app"
EOF

chmod +x "$DIST_DIR/$APP_NAME.sh"

echo -e "${GREEN}✅ Launcher script created: $DIST_DIR/$APP_NAME.sh${NC}"
echo ""

# Create README for the app bundle
echo -e "${YELLOW}Creating README...${NC}"
cat > "$DIST_DIR/README.txt" << EOF
MemScreen for macOS
==================

Version: $APP_VERSION
Release: $(date +%Y-%m-%d)

QUICK START:
------------

1. Install Ollama (Required):
   brew install ollama

2. Download AI Models:
   ollama pull qwen2.5vl:3b
   ollama pull mxbai-embed-large

3. Launch MemScreen:
   - Double-click MemScreen.app
   - Or run: ./MemScreen.sh

SYSTEM REQUIREMENTS:
--------------------

- macOS 10.15 (Catalina) or later
- Python 3.8+ (bundled)
- 5GB free disk space
- 8GB RAM recommended

TROUBLESHOOTING:
----------------

Q: App won't open
A: Right-click → Open, then confirm "Open" if prompted

Q: "Ollama not found" error
A: Install Ollama: brew install ollama

Q: AI models not working
A: Run these commands:
   ollama pull qwen2.5vl:3b
   ollama pull mxbai-embed-large

For more information:
https://github.com/smileformylove/MemScreen

LICENSE:
-------
MIT License - See LICENSE file in the repository
EOF

echo -e "${GREEN}✅ README created${NC}"
echo ""

# Create DMG (optional, if a suitable tool is available)
echo -e "${YELLOW}Creating DMG installer...${NC}"
DMG_FILE="$DIST_DIR/MemScreen-$APP_VERSION-macOS.dmg"

if command -v hdiutil &> /dev/null; then
    # Create a temporary DMG
    TEMP_DMG="/tmp/MemScreen.dmg"
    hdiutil create -size 500m -volname "MemScreen" -fs HFS+ "$TEMP_DMG"

    # Mount the DMG
    MOUNT_DIR=$(hdiutil attach "$TEMP_DMG" | grep -o '/Volumes/[^ ]*')

    # Copy the app
    cp -R "$DIST_DIR/$APP_NAME.app" "$MOUNT_DIR/"
    cp "$DIST_DIR/README.txt" "$MOUNT_DIR/"

    # Unmount
    hdiutil detach "$MOUNT_DIR"

    # Compress to final DMG
    hdiutil convert "$TEMP_DMG" -format UDZO -o "$DMG_FILE"

    # Cleanup
    rm "$TEMP_DMG"

    echo -e "${GREEN}✅ DMG created: $DMG_FILE${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠️  hdiutil not found. Skipping DMG creation.${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Complete! 🎉${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Created files:${NC}"
echo "  • $DIST_DIR/$APP_NAME.app"
echo "  • $DIST_DIR/$APP_NAME.sh"
echo "  • $DIST_DIR/README.txt"
if [ -f "$DMG_FILE" ]; then
    echo "  • $DMG_FILE"
fi
echo ""
echo -e "${BLUE}To distribute:${NC}"
echo "  1. Test the app: open $DIST_DIR/$APP_NAME.app"
echo "  2. If DMG was created, upload $DMG_FILE to GitHub Releases"
echo "  3. Otherwise, zip the app bundle:"
echo "     zip -r MemScreen-macOS.zip $APP_NAME.app README.txt"
echo ""
