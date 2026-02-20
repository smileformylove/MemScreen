#!/bin/bash
set -e

echo "=========================================="
echo "🦉 MemScreen Docker "
echo "=========================================="

# 1. Start Xvfb (virtual display server)
echo "📺 ..."
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
XVFB_PID=$!
sleep 2

# 2. Start fluxbox (window manager)
echo "🖥️ ..."
fluxbox > /dev/null 2>&1 &
sleep 2

# 3. Start Ollama in background
echo "🤖  Ollama ..."
ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!
sleep 5

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "⚠️ Ollama "
    cat /tmp/ollama.log
    exit 1
fi

echo "✅ Ollama "

# 4. Pull models if not present
echo "📥  AI ..."

if ! ollama list | grep -q "qwen2.5vl:3b"; then
    echo "    qwen2.5vl:3b (~2GB)..."
    ollama pull qwen2.5vl:3b
fi

if ! ollama list | grep -q "mxbai-embed-large"; then
    echo "    mxbai-embed-large (~470MB)..."
    ollama pull mxbai-embed-large
fi

echo "✅ AI "

# 5. Start MemScreen application
echo "🚀  MemScreen ..."
cd /app

echo ""
echo "=========================================="
echo "✅ MemScreen "
echo "=========================================="
echo ""
echo "📝 :"
echo "  - : docker exec -it memscreen-app bash"
echo "  - : docker logs -f memscreen-app"
echo "  - : docker-compose down"
echo ""
echo "🌐  noVNC:"
echo "  - : http://localhost:6080"
echo ""
echo "🦉  MemScreen ..."
echo "=========================================="

# Start the application
python start.py

# Cleanup on exit
trap "kill $XVFB_PID $OLLAMA_PID 2>/dev/null" EXIT
