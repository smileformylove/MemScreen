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

# Check if start.py exists
if [ ! -f "start.py" ]; then
    echo "❌ Cannot find start.py"
    echo "Please ensure you're in the MemScreen directory"
    exit 1
fi

# Launch the UI
echo "🖼️  Launching MemScreen UI..."
echo ""

# Function to filter stderr in real-time
filter_stderr() {
    while IFS= read -r line; do
        # Skip all objc SDL2 duplicate warnings
        # These warnings don't affect functionality
        if echo "$line" | grep -q "objc\[.*\]:.*SDL.*is implemented in both"; then
            continue
        fi
        if echo "$line" | grep -q "objc\[.*\]:.*Cocoa_WindowListener.*is implemented in both"; then
            continue
        fi
        if echo "$line" | grep -q "objc\[.*\]:.*METAL_.*is implemented in both"; then
            continue
        fi
        echo "$line" >&2
    done
}

# Run with stderr filtering
python3 start.py "$@" 2> >(filter_stderr)

