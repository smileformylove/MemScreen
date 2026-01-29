#!/bin/bash
# MemScreen Complete Installer for macOS
# This script installs everything: Ollama, models, and MemScreen

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

APP_VERSION="0.4.0"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}MemScreen Complete Installer${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check Python
echo -e "${YELLOW}Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    echo "Please install Python 3.8 or later from python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
echo ""

# Check Homebrew
echo -e "${YELLOW}Checking Homebrew...${NC}"
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}⚠️  Homebrew not found${NC}"
    echo ""
    read -p "Would you like to install Homebrew now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        echo -e "${GREEN}✓ Homebrew installed${NC}"

        # Update PATH
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo "Skipping Homebrew installation."
        echo "You'll need to install Ollama manually."
    fi
    echo ""
fi

# Install Ollama
echo -e "${YELLOW}Checking Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama via Homebrew..."
    brew install ollama
    echo -e "${GREEN}✓ Ollama installed${NC}"
    echo ""
else
    echo -e "${GREEN}✓ Ollama already installed${NC}"
    echo ""
fi

# Start Ollama service
echo -e "${YELLOW}Starting Ollama service...${NC}"
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve > /tmp/ollama_install.log 2>&1 &
    sleep 3
fi
echo -e "${GREEN}✓ Ollama service running${NC}"
echo ""

# Check and download models
echo -e "${YELLOW}Checking AI models...${NC}"
MODELS_NEEDED=()
if ! ollama list | grep -q "qwen2.5vl:3b"; then
    MODELS_NEEDED+=("qwen2.5vl:3b")
fi

if ! ollama list | grep -q "mxbai-embed-large"; then
    MODELS_NEEDED+=("mxbai-embed-large")
fi

if [ ${#MODELS_NEEDED[@]} -gt 0 ]; then
    echo "AI models to download:"
    for model in "${MODELS_NEEDED[@]}"; do
        echo "  • $model"
    done
    echo ""

    read -p "Download models now? (recommended) [Y/n] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        TOTAL_START=$(date +%s)

        for i in "${!MODELS_NEEDED[@]}"; do
            echo ""
            echo -e "${BLUE}[$((i+1))/${#MODELS_NEEDED[@]}] Downloading $model...${NC}"
            echo "Started at $(date +%H:%M:%S)"

            START_TIME=$(date +%s)
            ollama pull "${MODELS_NEEDED[$i]}"

            END_TIME=$(date +%s)
            DURATION=$((END_TIME - START_TIME))

            echo -e "${GREEN}✓ $model downloaded (${DURATION}s)${NC}"
        done

        TOTAL_END=$(date +%s)
        TOTAL_DURATION=$((TOTAL_END - TOTAL_START))

        echo ""
        echo -e "${GREEN}✅ All models downloaded successfully!${NC}"
        echo "Total time: ${TOTAL_DURATION}s"
    else
        echo -e "${YELLOW}⚠️  Skipping model download${NC}"
        echo "You can download them later:"
        for model in "${MODELS_NEEDED[@]}"; do
            echo "  ollama pull $model"
        done
    fi
else
    echo -e "${GREEN}✓ All AI models already installed${NC}"
    echo ""
fi

# Install MemScreen
echo -e "${YELLOW}Installing MemScreen...${NC}"
CURRENT_DIR="$(pwd)"

if [ ! -f "start.py" ]; then
    echo "MemScreen source files not found."
    echo "Please run this script from the MemScreen directory."
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --user -r requirements.txt

echo -e "${GREEN}✓ MemScreen installed${NC}"
echo ""

# Create launcher script
LAUNCHER="$HOME/Desktop/MemScreen.command"
cat > "$LAUNCHER" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
cd "$HOME/Desktop/MemScreen.app/Contents/Resources"
python3 start.py
EOF

chmod +x "$LAUNCHER"

echo -e "${GREEN}✓ Created launcher on Desktop${NC}"
echo ""

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Installation Complete! 🎉${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}MemScreen is ready to use!${NC}"
echo ""
echo "Launch options:"
echo "  1. Double-click MemScreen.command on Desktop"
echo "  2. Or run: cd $CURRENT_DIR && python3 start.py"
echo ""
echo "Features:"
echo "  • Screen recording with OCR"
echo "  • AI-powered chat with your screen history"
echo "  • Process mining and workflow analysis"
echo "  • 100% local, 100% private"
echo ""
