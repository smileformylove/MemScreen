#!/bin/bash
echo "🔍 检查本地构建状态..."
echo ""

# 检查虚拟环境
if [ -d "venv_build" ]; then
    echo "✅ 虚拟环境已创建"
else
    echo "⏳ 虚拟环境还未创建"
    exit 0
fi

# 检查构建目录
if [ -d "build" ]; then
    echo "✅ build 目录存在"
    echo "   内容:"
    ls -lh build/ | tail -5
else
    echo "⏳ 还未开始构建"
fi

# 检查输出目录
if [ -d "dist" ]; then
    echo ""
    echo "✅ dist 目录存在"
    echo "   内容:"
    ls -lh dist/
else
    echo "⏳ 还未生成输出"
fi

echo ""
echo "📊 进度:"
if [ -d "venv_build" ] && [ ! -d "build" ]; then
    echo "   正在安装依赖..."
elif [ -d "build" ] && [ ! -d "dist" ]; then
    echo "   正在构建应用..."
elif [ -d "dist" ]; then
    echo "   ✅ 构建完成！"
    if [ -f "dist/MemScreen-0.4.1-macos.zip" ]; then
        SIZE=$(ls -lh "dist/MemScreen-0.4.1-macos.zip" | awk '{print $5}')
        echo "   📦 分发包: dist/MemScreen-0.4.1-macos.zip (${SIZE})"
    fi
fi
