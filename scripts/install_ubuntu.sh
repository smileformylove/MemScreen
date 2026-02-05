#!/bin/bash
################################################################################
# MemScreen Ubuntu 安装脚本
# 这个脚本会在Ubuntu系统上安装MemScreen及其依赖
################################################################################

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

VERSION="0.5.0"
APP_NAME="MemScreen"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  MemScreen Ubuntu 安装程序${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}请不要使用root用户运行此脚本${NC}"
    echo "使用普通用户运行，sudo会在需要时自动调用"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "start.py" ]; then
    echo -e "${RED}错误: 请在MemScreen安装目录运行此脚本${NC}"
    echo ""
    echo "正确的安装步骤："
    echo "  1. 解压: tar -xzf MemScreen-0.5.0-ubuntu-installer.tar.gz"
    echo "  2. 进入目录: cd MemScreen-installer"
    echo "  3. 运行安装: ./install_ubuntu.sh"
    exit 1
fi

# 1. 更新系统包
echo -e "${YELLOW}[1/7] 更新系统包...${NC}"
sudo apt-get update

# 2. 安装系统依赖
echo -e "${YELLOW}[2/7] 安装系统依赖...${NC}"
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    portaudio19-dev \
    libopencv-dev \
    python3-opencv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good

# 3. 安装Ollama（如果未安装）
echo -e "${YELLOW}[3/7] 检查Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo "安装Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo -e "${GREEN}Ollama已安装${NC}"
fi

# 4. 创建虚拟环境
echo -e "${YELLOW}[4/7] 创建Python虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}虚拟环境创建成功${NC}"
else
    echo -e "${GREEN}虚拟环境已存在${NC}"
fi

# 5. 激活虚拟环境并安装Python依赖
echo -e "${YELLOW}[5/7] 安装Python依赖...${NC}"
source venv/bin/activate

# 安装核心依赖
pip install --upgrade pip
# 安装pysqlite3-binary以解决sqlite3版本问题
pip install pysqlite3-binary
pip install pydantic kivy ollama chromadb opencv-python numpy pillow \
            pynput mss toolz psutil requests

echo -e "${GREEN}Python依赖安装完成${NC}"

# 6. 创建启动脚本
echo -e "${YELLOW}[6/7] 创建启动脚本...${NC}"
cat > run_memscreen.sh << 'EOF'
#!/bin/bash
# MemScreen启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 激活虚拟环境
source "$SCRIPT_DIR/venv/bin/activate"

# 启动MemScreen
cd "$SCRIPT_DIR"
python start.py
EOF

chmod +x run_memscreen.sh

# 7. 创建桌面快捷方式
echo -e "${YELLOW}[7/7] 创建桌面快捷方式...${NC}"
INSTALL_DIR="$(pwd)"
cat > ~/Desktop/MemScreen.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=MemScreen
Comment=AI-Powered Visual Memory System
Exec=$INSTALL_DIR/run_memscreen.sh
Icon=$INSTALL_DIR/assets/logo.png
Terminal=false
Categories=Utility;Application;
EOF

chmod +x ~/Desktop/MemScreen.desktop

# 完成
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ 安装完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}使用方法：${NC}"
echo -e "  1. 双击桌面上的 MemScreen 图标"
echo -e "  2. 或运行: ${BLUE}./run_memscreen.sh${NC}"
echo ""
echo -e "${YELLOW}卸载方法：${NC}"
echo -e "  删除安装目录即可"
echo ""
echo -e "${YELLOW}注意事项：${NC}"
echo -e "  - 首次运行前，请确保Ollama服务已启动: ${BLUE}ollama serve${NC}"
echo -e "  - 需要下载模型: ${BLUE}ollama pull qwen3:1.7b${NC}"
echo ""
echo -e "${GREEN}享受使用MemScreen！🎉${NC}"
