#!/bin/bash
# MemScreen 统一启动脚本

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MemScreen v0.4.0"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查是否已有实例在运行
RUNNING=$(ps aux | grep "memscreen.ui.kivy_app\|kivy_app" | grep -v grep | wc -l)

if [ "$RUNNING" -gt 0 ]; then
    echo "⚠️  发现 $RUNNING 个 MemScreen 实例正在运行"
    echo ""
    ps aux | grep "memscreen.ui.kivy_app\|kivy_app" | grep -v grep
    echo ""
    echo "提示: 使用 'pkill -f memscreen' 终止所有实例"
    exit 1
fi

echo "✓ 正在启动 MemScreen..."
echo ""

# 启动应用
cd /Users/jixiangluo/Documents/project_code/repository/MemScreen
python3 start.py

echo ""
echo "✓ MemScreen 已退出"
