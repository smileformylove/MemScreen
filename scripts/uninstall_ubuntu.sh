#!/bin/bash
################################################################################
# MemScreen Ubuntu 卸载脚本
# 从系统中完全移除MemScreen及其组件
################################################################################

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_NAME="MemScreen"
PROJECT_ROOT="$(pwd)"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🗑️  MemScreen 卸载程序${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查是否在正确的目录
if [ ! -f "start.py" ]; then
    echo -e "${RED}错误: 请在MemScreen安装目录中运行此脚本${NC}"
    echo "提示: cd到MemScreen安装目录后再运行"
    exit 1
fi

echo -e "${YELLOW}当前目录: ${PROJECT_ROOT}${NC}"
echo ""
echo -e "${RED}警告: 此操作将删除以下内容:${NC}"
echo "  • Python虚拟环境 (venv/)"
echo "  • 生成的数据库文件 (db/)"
echo "  • 日志文件 (*.log)"
echo "  • 临时文件 (build/, dist/)"
echo "  • Python缓存 (__pycache__)"
echo ""

# 询问确认
read -p "确认要卸载MemScreen吗? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}取消卸载${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/6] 停止运行中的进程...${NC}"
# 停止所有MemScreen进程
pkill -9 -f "python start.py" 2>/dev/null || true
pkill -9 -f "MemScreen" 2>/dev/null || true
echo -e "${GREEN}进程已停止${NC}"

echo -e "${YELLOW}[2/6] 删除桌面快捷方式...${NC}"
# 删除桌面快捷方式
if [ -f "$HOME/Desktop/MemScreen.desktop" ]; then
    rm -f "$HOME/Desktop/MemScreen.desktop"
    echo -e "${GREEN}桌面快捷方式已删除${NC}"
else
    echo -e "${YELLOW}未找到桌面快捷方式${NC}"
fi

# 删除应用菜单中的快捷方式（如果存在）
if [ -f "$HOME/.local/share/applications/MemScreen.desktop" ]; then
    rm -f "$HOME/.local/share/applications/MemScreen.desktop"
    echo -e "${GREEN}应用菜单快捷方式已删除${NC}"
fi

echo -e "${YELLOW}[3/6] 删除用户数据...${NC}"
# 询问是否删除用户数据
read -p "是否删除用户数据（数据库、日志等）? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 删除数据库和日志
    rm -rf db/
    rm -f *.log 2>/dev/null || true
    echo -e "${GREEN}用户数据已删除${NC}"
else
    echo -e "${YELLOW}保留用户数据${NC}"
    echo "数据库和日志文件保留在: $PROJECT_ROOT/db/"
fi

echo -e "${YELLOW}[4/6] 删除虚拟环境...${NC}"
# 删除虚拟环境
if [ -d "venv" ]; then
    rm -rf venv/
    echo -e "${GREEN}虚拟环境已删除${NC}"
else
    echo -e "${YELLOW}未找到虚拟环境${NC}"
fi

echo -e "${YELLOW}[5/6] 清理临时文件...${NC}"
# 清理临时文件
rm -rf build/
rm -rf dist/
rm -rf *.AppImage 2>/dev/null || true
rm -rf *.tar.gz 2>/dev/null || true
rm -rf MemScreen.AppDir 2>/dev/null || true
rm -rf __pycache__
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}临时文件已清理${NC}"

echo -e "${YELLOW}[6/6] 删除启动脚本...${NC}"
# 删除启动脚本
if [ -f "run_memscreen.sh" ]; then
    rm -f run_memscreen.sh
    echo -e "${GREEN}启动脚本已删除${NC}"
fi

# 完成
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ 卸载完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 显示剩余文件
REMAINING=$(find . -mindepth 1 -maxdepth 1 ! -name "uninstall_ubuntu.sh" 2>/dev/null | wc -l)
if [ $REMAINING -gt 0 ]; then
    echo -e "${YELLOW}目录中还有以下文件:${NC}"
    find . -mindepth 1 -maxdepth 1 ! -name "uninstall_ubuntu.sh" -print
    echo ""
    echo -e "${YELLOW}如需完全删除安装目录，请手动删除:${NC}"
    echo "  cd .. && rm -rf $(basename "$PROJECT_ROOT")"
else
    echo -e "${GREEN}安装目录已清空${NC}"
    echo ""
    echo -e "${YELLOW}您可以删除安装目录:${NC}"
    echo "  cd .. && rm -rf $(basename "$PROJECT_ROOT")"
fi

echo ""
echo -e "${BLUE}感谢使用MemScreen！${NC}"
