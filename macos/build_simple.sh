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

# Check and install Ollama if needed
if ! command -v ollama &> /dev/null; then
    osascript -e 'display dialog "MemScreen requires Ollama.

Would you like to install Ollama now?
This will open the Ollama download page.

After installing, please restart MemScreen." buttons {"Install Now", "Cancel" default button "Install Now" with title "MemScreen - Ollama Required" giving up after 0' &> /dev/null

    # Wait for user response
    sleep 2

    # Open Ollama download page
    open "https://ollama.com/download"

    osascript -e 'display dialog "After installing Ollama, please restart MemScreen." buttons {"OK"} with title "MemScreen - Installation Required" giving up after 0' &> /dev/null

    exit 1
fi

# Check and download AI models on first run
MODELS_CHECK_FILE="$HOME/.memscreen_models_installed"

if [ ! -f "$MODELS_CHECK_FILE" ]; then
    echo "Checking for required AI models..."

    MODELS_OK=true

    # Check if qwen2.5vl:3b exists
    if ! ollama list | grep -q "qwen2.5vl:3b"; then
        MODELS_OK=false
        MODEL1="qwen2.5vl:3b"
    fi

    # Check if mxbai-embed-large exists
    if ! ollama list | grep -q "mxbai-embed-large"; then
        MODELS_OK=false
        MODEL2="mxbai-embed-large"
    fi

    if [ "$MODELS_OK" = false ]; then
        osascript -e 'display dialog "MemScreen needs to download AI models (~2.5GB total).

This one-time download will happen in the background.
You can continue using MemScreen once models are ready.

Models to download:
• qwen2.5vl:3b (~2GB) - Vision model
• mxbai-embed-large (~470MB) - Text embeddings

Click OK to start download." buttons {"OK"} with title "MemScreen - AI Models" giving up after 0' &> /dev/null

        # Create download script
        cat > /tmp/memscreen_download_models.sh << 'EOF'
#!/bin/bash
cd "$HOME"

echo "Downloading AI models for MemScreen..."
echo "This may take 10-20 minutes depending on your connection."

# Download vision model
echo ""
echo "[1/2] Downloading qwen2.5vl:3b (~2GB)..."
ollama pull qwen2.5vl:3b

# Download embedding model
echo ""
echo "[2/2] Downloading mxbai-embed-large (~470MB)..."
ollama pull mxbai-embed-large

# Create marker file
touch ~/.memscreen_models_installed

echo ""
echo "✅ All models downloaded successfully!"
echo "You can now launch MemScreen."

# Show notification
osascript -e 'display notification "MemScreen" with title "AI Models Ready!"' &> /dev/null
EOF

        chmod +x /tmp/memscreen_download_models.sh

        # Run download in background Terminal
        osascript -e 'tell application "Terminal"
            do script "chmod +x /tmp/memscreen_download_models.sh && /tmp/memscreen_download_models.sh"
            end tell' &> /dev/null

        osascript -e 'display dialog "AI models are downloading in the background.

You can close this window. A notification will appear when ready.

To check progress, open Terminal and see the download progress."
         buttons {"OK"} with title "MemScreen - Downloading Models" giving up after 0' &> /dev/null

        exit 0
    fi

    # Create marker file
    touch "$MODELS_CHECK_FILE"
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
