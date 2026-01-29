#!/bin/bash
# MemScreen macOS Easy Installer
# This script sets up MemScreen on your Mac with minimal effort

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================"
echo "MemScreen macOS Installer"
echo "================================================${NC}"
echo ""

# Detect Python version
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo -e "${YELLOW}⚠️  Python not found. Please install Python 3.8+ first.${NC}"
    echo "Visit https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version | awk '{print $2}')
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"

# Check Python version >= 3.8
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${YELLOW}⚠️  Python 3.8+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

# Check if pip is available
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo -e "${YELLOW}⚠️  pip not found. Installing pip...${NC}"
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $PYTHON_CMD get-pip.py
    rm get-pip.py
fi

echo -e "${GREEN}✓ pip is available${NC}"

# Check for Homebrew
if command -v brew &> /dev/null; then
    echo -e "${GREEN}✓ Homebrew is installed${NC}"

    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        echo ""
        echo "Ollama is required for AI features."
        read -p "Install Ollama now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Installing Ollama..."
            brew install ollama
            echo -e "${GREEN}✓ Ollama installed${NC}"
        fi
    else
        echo -e "${GREEN}✓ Ollama is installed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Homebrew not found${NC}"
    echo "To install Ollama later: brew install ollama"
    echo "Or visit: https://ollama.com/download"
fi

echo ""
echo "================================================"
echo "Installation Complete! 🎉"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo -e "${BLUE}1. Navigate to MemScreen directory:${NC}"
echo "   cd MemScreen"
echo ""
echo -e "${BLUE}2. Install Python dependencies:${NC}"
echo "   pip install -r requirements.txt"
echo ""
echo -e "${BLUE}3. Launch MemScreen:${NC}"
echo "   python start.py"
echo ""

echo ""
echo "================================================"
echo "Setting up AI Models"
echo "================================================"
echo ""

# Check if Ollama is running
if command -v ollama &> /dev/null; then
    # Start Ollama service if not running
    if ! pgrep -x "ollama" > /dev/null; then
        echo "Starting Ollama service..."
        ollama serve > /dev/null 2>&1 &
        sleep 3
    fi

    echo "Downloading AI models (this may take a while)..."
    echo ""

    # Pull models
    for model in "qwen3:1.7b" "qwen2.5vl:3b" "mxbai-embed-large:latest"; do
        echo -e "${BLUE}Downloading $model...${NC}"
        ollama pull "$model"
        echo -e "${GREEN}✓ $model downloaded${NC}"
    done

    echo ""
    echo -e "${GREEN}✓ AI models ready${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama not found. Skipping model download.${NC}"
    echo "Install Ollama and run:"
    echo "  ollama pull qwen3:1.7b"
    echo "  ollama pull qwen2.5vl:3b"
    echo "  ollama pull mxbai-embed-large:latest"
fi

echo ""
echo "================================================"
echo -e "${GREEN}Installation Complete! 🎉${NC}"
echo "================================================"
echo ""
echo "For more information:"
echo "  https://github.com/smileformylove/MemScreen"
echo ""
echo "Happy screen recording! 📸"
echo ""
