#!/bin/bash
set -e

echo "=========================================="
echo "🦉 MemScreen Docker 启动脚本"
echo "=========================================="

# 1. Start Xvfb (virtual display server)
echo "📺 启动虚拟显示服务器..."
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
XVFB_PID=$!
sleep 2

# 2. Start fluxbox (window manager)
echo "🖥️ 启动窗口管理器..."
fluxbox > /dev/null 2>&1 &
sleep 2

# 3. Start Ollama in background
echo "🤖 启动 Ollama 服务..."
ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!
sleep 5

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "⚠️ Ollama 启动失败，检查日志："
    cat /tmp/ollama.log
    exit 1
fi

echo "✅ Ollama 服务已启动"

# 4. Pull models if not present
echo "📥 检查 AI 模型..."

if ! ollama list | grep -q "qwen2.5vl:3b"; then
    echo "   下载 qwen2.5vl:3b (~2GB)..."
    ollama pull qwen2.5vl:3b
fi

if ! ollama list | grep -q "mxbai-embed-large"; then
    echo "   下载 mxbai-embed-large (~470MB)..."
    ollama pull mxbai-embed-large
fi

echo "✅ AI 模型已就绪"

# 5. Start MemScreen application
echo "🚀 启动 MemScreen 应用..."
cd /app

echo ""
echo "=========================================="
echo "✅ MemScreen 已启动！"
echo "=========================================="
echo ""
echo "📝 可用命令:"
echo "  - 进入容器: docker exec -it memscreen-app bash"
echo "  - 查看日志: docker logs -f memscreen-app"
echo "  - 停止服务: docker-compose down"
echo ""
echo "🌐 如果启用了 noVNC:"
echo "  - 访问: http://localhost:6080"
echo ""
echo "🦉 启动 MemScreen 应用..."
echo "=========================================="

# Start the application
python start.py

# Cleanup on exit
trap "kill $XVFB_PID $OLLAMA_PID 2>/dev/null" EXIT
