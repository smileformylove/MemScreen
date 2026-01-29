#!/bin/bash
# MemScreen macOS Simple Build Script
# Creates a standalone .app bundle without py2app

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

APP_NAME="MemScreen"
APP_VERSION="0.4.0"
BUILD_DIR="$(pwd)/build"
DIST_DIR="$(pwd)/dist"
SRC_DIR="$(pwd)/.."

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}MemScreen macOS Simple Build${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf "$BUILD_DIR"
rm -rf "$DIST_DIR"
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"

# Create .app bundle structure
echo -e "${YELLOW}Creating .app bundle...${NC}"
APP_BUNDLE="$DIST_DIR/${APP_NAME}.app"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"
mkdir -p "$APP_BUNDLE/Contents/Frameworks"

# Copy Info.plist
echo -e "${YELLOW}Copying Info.plist...${NC}"
cp "Info.plist" "$APP_BUNDLE/Contents/Info.plist"

# Create launcher script
echo -e "${YELLOW}Creating launcher script...${NC}"
cat > "$APP_BUNDLE/Contents/MacOS/$APP_NAME" << 'EOF'
#!/bin/bash
# MemScreen Launcher

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../Resources"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    osascript -e 'display dialog "MemScreen requires Ollama to run AI models.

Please install Ollama:
  brew install ollama

Then download AI models:
  ollama pull qwen2.5vl:3b
  ollama pull mxbai-embed-large

Visit ollama.com for more information." buttons {"OK"} with title "MemScreen - Ollama Required"'
    exit 1
fi

# Check if Ollama service is running
if ! pgrep -x "ollama" > /dev/null; then
    osascript -e 'display dialog "Starting Ollama service...

This will take a few seconds." buttons {"OK"} with title "MemScreen - Starting Ollama" giving up after 0' &> /dev/null

    # Start Ollama in background
    ollama serve > /tmp/ollama.log 2>&1 &

    # Wait for Ollama to start
    sleep 5
fi

# Launch MemScreen
cd "$SCRIPT_DIR/../Resources"
exec python3 start.py "$@"
EOF

chmod +x "$APP_BUNDLE/Contents/MacOS/$APP_NAME"

# Copy application resources
echo -e "${YELLOW}Copying application files...${NC}"
# Copy source files
mkdir -p "$APP_BUNDLE/Contents/Resources/memscreen"
cp -R "$SRC_DIR/memscreen" "$APP_BUNDLE/Contents/Resources/"
cp "$SRC_DIR/start.py" "$APP_BUNDLE/Contents/Resources/"
cp "$SRC_DIR/config_example.yaml" "$APP_BUNDLE/Contents/Resources/" 2>/dev/null || true
cp "$SRC_DIR/GRAPH_MEMORY_GUIDE.md" "$APP_BUNDLE/Contents/Resources/" 2>/dev/null || true
cp "$SRC_DIR/requirements.txt" "$APP_BUNDLE/Contents/Resources/" 2>/dev/null || true

# Create README
cat > "$DIST_DIR/README.txt" << EOF
MemScreen for macOS
==================

Version: $APP_VERSION

QUICK START:
------------

1. Install Dependencies:
   - Install Ollama: brew install ollama
   - Download models:
     ollama pull qwen2.5vl:3b
     ollama pull mxbai-embed-large

2. Launch MemScreen:
   - Double-click MemScreen.app
   - The app will guide you through first-time setup

SYSTEM REQUIREMENTS:
--------------------

- macOS 10.15 (Catalina) or later
- Python 3.8+ (must be installed separately)
- Ollama for AI models
- 5GB free disk space
- 8GB RAM recommended

FOR DEVELOPERS:
---------------

To run from source instead:

1. Install Python dependencies:
   pip install -r requirements.txt

2. Run directly:
   python3 start.py

For more information and updates:
https://github.com/smileformylove/MemScreen

EOF

# Create a setup script for first-run dependencies
cat > "$DIST_DIR/install_dependencies.sh" << 'EOF'
#!/bin/bash
# MemScreen Dependency Installer

echo "MemScreen - Installing Python Dependencies..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "Please install Python 3.8 or later from python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Found Python $PYTHON_VERSION"

# Install Python dependencies
echo ""
echo "Installing Python packages..."
pip3 install --user -r requirements.txt

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "Next:"
echo "1. Install Ollama: brew install ollama"
echo "2. Download AI models:"
echo "   ollama pull qwen2.5vl:3b"
echo "   ollama pull mxbai-embed-large"
echo ""

EOF

chmod +x "$DIST_DIR/install_dependencies.sh"

echo ""
echo -e "${GREEN}✅ Build successful!${NC}"
echo ""
echo -e "${BLUE}Created: $APP_BUNDLE${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Right-click $APP_BUNDLE and select 'Open'"
echo "2. Confirm you want to open the app"
echo "3. The app will check for Ollama and guide you through setup"
echo ""
echo -e "${BLUE}Or run the dependency installer:${NC}"
echo "   ./install_dependencies.sh"
echo ""

# Create a simple DMG (optional)
if command -v hdiutil &> /dev/null; then
    echo -e "${YELLOW}Creating DMG installer...${NC}"
    DMG_FILE="$DIST_DIR/MemScreen-$APP_VERSION-macOS.dmg"
    TEMP_DMG="/tmp/MemScreen-build.dmg"

    # Create DMG
    hdiutil create -size 100m -volname "MemScreen" -fs HFS+ "$TEMP_DMG" 2>/dev/null || true

    # Mount and copy files
    MOUNT_DIR=$(hdiutil attach "$TEMP_DMG" 2>/dev/null | grep -o '/Volumes/[^ ]*')
    if [ -n "$MOUNT_DIR" ]; then
        # Copy app to DMG
        ditto "$APP_BUNDLE" "$MOUNT_DIR/"
        ditto "$DIST_DIR/README.txt" "$MOUNT_DIR/"
        ditto "$DIST_DIR/install_dependencies.sh" "$MOUNT_DIR/"

        # Create a symlink to Applications
        ln -s /Applications "$MOUNT_DIR/Applications"

        # Unmount
        hdiutil detach "$MOUNT_DIR"

        # Convert to compressed DMG
        hdiutil convert "$TEMP_DMG" -format UDZO -o "$DMG_FILE" 2>/dev/null

        # Clean up
        rm "$TEMP_DMG"

        echo -e "${GREEN}✅ DMG created: $DMG_FILE${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not create DMG${NC}"
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Complete! 🎉${NC}"
echo -e "${GREEN}========================================${NC}"
