#!/bin/bash
# Docker 

echo "=========================================="
echo "🐳 MemScreen Docker "
echo "=========================================="

#  Docker 
if ! command -v docker &> /dev/null; then
    echo "❌ Docker "
    echo " https://docs.docker.com/get-docker/  Docker"
    exit 1
fi

echo "✅ Docker : $(docker --version)"

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose "
    echo " https://docs.docker.com/compose/install/  Docker Compose"
    exit 1
fi

echo "✅ Docker Compose "

# 
echo ""
echo "📊 :"
echo "   : $(df -h . | tail -1 | awk '{print $4}')"
echo "   : $(free -h | grep Mem | awk '{print $7}')"

echo ""
echo "=========================================="
echo "🔨  Docker "
echo "=========================================="

# 
echo " MemScreen Docker ..."
if docker compose build; then
    echo "✅ "
else
    echo "❌ "
    exit 1
fi

echo ""
echo "=========================================="
echo "🚀 "
echo "=========================================="

# 
echo " MemScreen ..."
if docker compose up -d; then
    echo "✅ "
else
    echo "❌ "
    exit 1
fi

# 
echo " (10)..."
sleep 10

echo ""
echo "=========================================="
echo "🧪 "
echo "=========================================="

#  Ollama
echo ""
echo "1️⃣  Ollama ..."
if docker exec memscreen-app curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama "
else
    echo "❌ Ollama "
fi

#  Python 
echo ""
echo "2️⃣  Python ..."
if docker exec memscreen-app python --version; then
    echo "✅ Python "
else
    echo "❌ Python "
fi

# 
echo ""
echo "3️⃣  Python ..."
REQUIRED_PACKAGES=("kivy" "cv2" "PIL" "requests")
for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if docker exec memscreen-app python -c "import $pkg" 2>/dev/null; then
        echo "   ✅ $pkg"
    else
        echo "   ❌ $pkg ()"
    fi
done

echo ""
echo "=========================================="
echo "📝 "
echo "=========================================="

docker compose logs --tail=20 memscreen

echo ""
echo "=========================================="
echo "✅ "
echo "=========================================="

echo ""
echo "📋 :"
echo ""
echo "1. :"
echo "   docker compose logs -f memscreen"
echo ""
echo "2. :"
echo "   docker exec -it memscreen-app bash"
echo ""
echo "3. :"
echo "   docker compose down"
echo ""
echo "4. :"
echo "   docker ps -a | grep memscreen"
echo ""
echo "5. :"
echo "   docker compose down -v"
echo ""
echo "=========================================="
