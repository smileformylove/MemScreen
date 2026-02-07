#!/bin/bash
# MemScreen Quick Launch Script
# A convenient launcher with automatic environment setup

set -e

MEMSCREEN_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$MEMSCREEN_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Virtual environment not found. Running quick install..."
    bash "$MEMSCREEN_DIR/install.sh"
fi

# Activate virtual environment
echo "🔧 Activating environment..."
source "$VENV_DIR/bin/activate"

# Check if Ollama is running
echo ""
echo "🦙 Checking Ollama service..."
if ! ollama list > /dev/null 2>&1; then
    echo "⚠️  Ollama service is not running."
    echo "   Starting Ollama in background..."
    ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    echo "   Waiting for Ollama to start..."
    sleep 5
    if kill -0 $OLLAMA_PID 2>/dev/null; then
        echo "✓ Ollama started (PID: $OLLAMA_PID)"
    else
        echo "❌ Failed to start Ollama. Please start manually:"
        echo "   ollama serve"
        exit 1
    fi
else
    echo "✓ Ollama service is running"
fi

# Check models
echo ""
echo "🤖 Checking AI models..."
MODELS=$(ollama list 2>/dev/null | grep -E "qwen2.5vl:3b|mxbai-embed-large" || true)
if [ -z "$MODELS" ]; then
    echo "⚠️  No models found. Models will be downloaded on first use."
else
    echo "$MODELS" | while read -r line; do
        echo "✓ $line"
    done
fi

# Launch MemScreen
echo ""
echo "🚀 Launching MemScreen v0.6.0..."
echo ""
python "$MEMSCREEN_DIR/start.py" "$@"
