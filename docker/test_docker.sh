#!/bin/bash
# Docker 测试脚本

echo "=========================================="
echo "🐳 MemScreen Docker 测试脚本"
echo "=========================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    echo "请访问 https://docs.docker.com/get-docker/ 安装 Docker"
    exit 1
fi

echo "✅ Docker 已安装: $(docker --version)"

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    echo "请访问 https://docs.docker.com/compose/install/ 安装 Docker Compose"
    exit 1
fi

echo "✅ Docker Compose 已安装"

# 检查可用磁盘空间
echo ""
echo "📊 系统资源检查:"
echo "   可用磁盘空间: $(df -h . | tail -1 | awk '{print $4}')"
echo "   可用内存: $(free -h | grep Mem | awk '{print $7}')"

echo ""
echo "=========================================="
echo "🔨 构建 Docker 镜像"
echo "=========================================="

# 构建镜像
echo "正在构建 MemScreen Docker 镜像..."
if docker compose build; then
    echo "✅ 镜像构建成功"
else
    echo "❌ 镜像构建失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "🚀 启动容器"
echo "=========================================="

# 启动容器
echo "正在启动 MemScreen 容器..."
if docker compose up -d; then
    echo "✅ 容器启动成功"
else
    echo "❌ 容器启动失败"
    exit 1
fi

# 等待服务启动
echo "等待服务启动 (10秒)..."
sleep 10

echo ""
echo "=========================================="
echo "🧪 测试服务"
echo "=========================================="

# 测试 Ollama
echo ""
echo "1️⃣ 测试 Ollama 服务..."
if docker exec memscreen-app curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama 服务正常运行"
else
    echo "❌ Ollama 服务无法访问"
fi

# 测试 Python 环境
echo ""
echo "2️⃣ 测试 Python 环境..."
if docker exec memscreen-app python --version; then
    echo "✅ Python 环境正常"
else
    echo "❌ Python 环境异常"
fi

# 测试依赖包
echo ""
echo "3️⃣ 检查 Python 依赖..."
REQUIRED_PACKAGES=("kivy" "cv2" "PIL" "requests")
for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if docker exec memscreen-app python -c "import $pkg" 2>/dev/null; then
        echo "   ✅ $pkg"
    else
        echo "   ❌ $pkg (缺失)"
    fi
done

echo ""
echo "=========================================="
echo "📝 容器日志"
echo "=========================================="

docker compose logs --tail=20 memscreen

echo ""
echo "=========================================="
echo "✅ 测试完成"
echo "=========================================="

echo ""
echo "📋 后续步骤:"
echo ""
echo "1. 查看实时日志:"
echo "   docker compose logs -f memscreen"
echo ""
echo "2. 进入容器:"
echo "   docker exec -it memscreen-app bash"
echo ""
echo "3. 停止服务:"
echo "   docker compose down"
echo ""
echo "4. 查看容器状态:"
echo "   docker ps -a | grep memscreen"
echo ""
echo "5. 清理数据:"
echo "   docker compose down -v"
echo ""
echo "=========================================="
