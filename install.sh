#!/bin/bash
# MemScreen Quick Installation Script
# Supports: macOS, Linux

set -e

echo "🦉 MemScreen v0.6.0 - Quick Installation"
echo "=========================================="
echo ""

# Detect OS
OS="$(uname -s)"
echo "🖥️  Detected OS: $OS"

# Check Python version
echo ""
echo "🐍 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Please install Python 3.8+ first:"
    echo "  - macOS: brew install python3"
    echo "  - Ubuntu: sudo apt-get install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

if [ $(echo "$PYTHON_VERSION 3.8" | awk '{print ($1 < $2)}') -eq 1 ]; then
    echo "❌ Python 3.8+ is required (current: $PYTHON_VERSION)"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo ""
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "📚 Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Check Ollama
echo ""
echo "🦙 Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama is installed"

    # Check if Ollama is running
    if ollama list > /dev/null 2>&1; then
        echo "✓ Ollama service is running"
    else
        echo "⚠️  Ollama is installed but not running"
        echo "   Start it with: ollama serve"
    fi
else
    echo "⚠️  Ollama is not installed"
    echo ""
    echo "📥 Installing Ollama..."
    if [ "$OS" = "Darwin" ]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ollama
        else
            echo "❌ Homebrew not found. Please install from https://ollama.com/download"
            exit 1
        fi
    else
        # Linux
        echo "Please install Ollama from https://ollama.com/download"
        echo "Then run: curl https://ollama.com/install.sh | sh"
    fi
fi

# Pull models
echo ""
echo "🤖 Checking AI models..."
if command -v ollama &> /dev/null && ollama list > /dev/null 2>&1; then
    MODELS=$(ollama list 2>/dev/null | grep -E "qwen2.5vl:3b|mxbai-embed-large" || echo "")

    if echo "$MODELS" | grep -q "qwen2.5vl:3b"; then
        echo "✓ Vision model (qwen2.5vl:3b) already downloaded"
    else
        echo "📥 Downloading vision model (qwen2.5vl:3b, ~3GB)..."
        ollama pull qwen2.5vl:3b
    fi

    if echo "$MODELS" | grep -q "mxbai-embed-large"; then
        echo "✓ Embedding model (mxbai-embed-large) already downloaded"
    else
        echo "📥 Downloading embedding model (mxbai-embed-large, ~500MB)..."
        ollama pull mxbai-embed-large
    fi
else
    echo "⚠️  Cannot check models (Ollama not running)"
    echo "   Please start Ollama first: ollama serve"
    echo "   Then models will be downloaded on first use"
fi

# Create config
echo ""
echo "⚙️  Creating configuration..."
if [ ! -f "config.yaml" ]; then
    if [ -f "config_example.yaml" ]; then
        cp config_example.yaml config.yaml
        echo "✓ Created config.yaml from template"
    else
        echo "✓ config.yaml already exists"
    fi
else
    echo "✓ config.yaml already exists"
fi

# Create data directory
echo ""
echo "📁 Creating data directories..."
mkdir -p ~/.memscreen/db
mkdir -p ~/.memscreen/videos
mkdir -p ~/.memscreen/logs
echo "✓ Data directories created"

# Summary
echo ""
echo "=========================================="
echo "✅ Installation complete!"
echo ""
echo "🚀 Quick Start:"
echo "   source venv/bin/activate"
echo "   python start.py"
echo ""
echo "📚 Documentation:"
echo "   - User Guide: docs/USER_GUIDE.md"
echo "   - README: README.md"
echo "   - Changelog: CHANGELOG.md"
echo ""
echo "🔧 Troubleshooting:"
echo "   - Ensure Ollama is running: ollama serve"
echo "   - Check Python version: python3 --version"
echo "   - Reinstall dependencies: pip install -r requirements.txt"
echo ""
