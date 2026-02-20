#!/bin/bash
################################################################################
# MemScreen Ubuntu 
# UbuntuMemScreen
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
echo -e "${BLUE}  MemScreen Ubuntu ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}root${NC}"
    echo "sudo"
    exit 1
fi

# 
if [ ! -f "start.py" ]; then
    echo -e "${RED}: MemScreen${NC}"
    echo ""
    echo ""
    echo "  1. : tar -xzf MemScreen-0.5.0-ubuntu-installer.tar.gz"
    echo "  2. : cd MemScreen-installer"
    echo "  3. : ./install_ubuntu.sh"
    exit 1
fi

# 1. 
echo -e "${YELLOW}[1/7] ...${NC}"
sudo apt-get update

# 2. 
echo -e "${YELLOW}[2/7] ...${NC}"
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

# 3. Ollama
echo -e "${YELLOW}[3/7] Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo "Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo -e "${GREEN}Ollama${NC}"
fi

# 4. 
echo -e "${YELLOW}[4/7] Python...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}${NC}"
else
    echo -e "${GREEN}${NC}"
fi

# 5. Python
echo -e "${YELLOW}[5/7] Python...${NC}"
source venv/bin/activate

# 
pip install --upgrade pip
# pysqlite3-binarysqlite3
pip install pysqlite3-binary
pip install pydantic kivy ollama chromadb opencv-python numpy pillow \
            pynput mss toolz psutil requests

echo -e "${GREEN}Python${NC}"

# 6. 
echo -e "${YELLOW}[6/7] ...${NC}"
cat > run_memscreen.sh << 'EOF'
#!/bin/bash
# MemScreen

# 
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 
source "$SCRIPT_DIR/venv/bin/activate"

# MemScreen
cd "$SCRIPT_DIR"
python start.py
EOF

chmod +x run_memscreen.sh

# 7. 
echo -e "${YELLOW}[7/7] ...${NC}"
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

# 
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ ${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}${NC}"
echo -e "  1.  MemScreen "
echo -e "  2. : ${BLUE}./run_memscreen.sh${NC}"
echo ""
echo -e "${YELLOW}${NC}"
echo -e "  "
echo ""
echo -e "${YELLOW}${NC}"
echo -e "  - Ollama: ${BLUE}ollama serve${NC}"
echo -e "  - : ${BLUE}ollama pull qwen3:1.7b${NC}"
echo ""
echo -e "${GREEN}MemScreen🎉${NC}"
