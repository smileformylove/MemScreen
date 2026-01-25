#!/bin/bash
#
# MemScreen UI Launcher
# This script ensures the correct Python environment is used
#

echo "🚀 Starting MemScreen UI..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python version
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Please install Python 3.8+"
    exit 1
fi

echo "📍 Using Python: $(which python3)"
echo "📍 Python Version: $(python3 --version)"
echo ""

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import pydantic" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Dependencies missing."
    echo ""
    echo "Please install dependencies using one of these methods:"
    echo ""
    echo "1. Using virtual environment (recommended):"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -e ."
    echo "   ./run_ui.sh"
    echo ""
    echo "2. Using --user flag:"
    echo "   pip3 install --user -e ."
    echo ""
    echo "3. Using --break-system-packages (not recommended):"
    echo "   pip3 install --break-system-packages -e ."
    echo ""
    echo "See TROUBLESHOOTING.md for more details."
    exit 1
fi

echo "✅ Dependencies OK"
echo ""

# Launch the UI
echo "🖼️  Launching MemScreen UI..."
echo ""

# Try to launch with unified_ui first (official command)
if [ -f "memscreen/unified_ui.py" ]; then
    python3 -m memscreen.ui
else
    echo "❌ Cannot find memscreen UI module"
    exit 1
fi
