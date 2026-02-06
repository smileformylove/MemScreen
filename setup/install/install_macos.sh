#!/bin/bash
################################################################################
# MemScreen macOS Installation Script
#
# This script automates the installation of MemScreen on macOS, including:
# - Checking system requirements
# - Installing Python (if needed)
# - Installing Ollama (if needed)
# - Downloading AI models
# - Installing MemScreen Python package
# - Requesting necessary system permissions
#
# Usage: sudo ./scripts/install_macos.sh
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions for colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    print_warning "This script requires sudo privileges for some operations."
    print_info "You may be prompted for your password."
    echo ""
fi

################################################################################
# Main Installation Steps
################################################################################

print_header "🦉 MemScreen Installation"

echo "This script will install MemScreen with the following components:"
echo "  • Python 3.8+ (if not installed)"
echo "  • Ollama AI Runtime (if not installed)"
echo "  • Required AI Models (~3GB)"
echo "  • MemScreen Application"
echo ""

read -p "Continue with installation? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Installation cancelled."
    exit 0
fi

################################################################################
# Step 1: Check macOS Version
################################################################################

print_header "Step 1: Checking System Requirements"

MACOS_VERSION=$(sw_vers -macOSProductVersion)
MACOS_MAJOR=$(echo $MACOS_VERSION | cut -d. -f1)
MACOS_MINOR=$(echo $MACOS_VERSION | cut -d. -f2)

print_info "Detected macOS version: $MACOS_VERSION"

if [ "$MACOS_MAJOR" -lt 11 ]; then
    print_error "macOS 11.0 (Big Sur) or later is required."
    print_info "Your version: $MACOS_VERSION"
    exit 1
fi

print_success "macOS version check passed"

################################################################################
# Step 2: Check and Install Python
################################################################################

print_header "Step 2: Checking Python Installation"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    print_info "Python 3 found: version $PYTHON_VERSION"

    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        print_success "Python version is compatible (3.8+)"
    else
        print_warning "Python version is too old. Installing Python 3.11..."
        if command -v brew &> /dev/null; then
            brew install python@3.11
        else
            print_error "Homebrew not found. Please install Python manually."
            print_info "Visit: https://www.python.org/downloads/"
            exit 1
        fi
    fi
else
    print_warning "Python 3 not found. Installing..."

    if command -v brew &> /dev/null; then
        print_info "Installing Python 3 via Homebrew..."
        brew install python@3.11
        print_success "Python 3 installed"
    else
        print_error "Homebrew not found."
        print_info "Please install Python 3.8+ or Homebrew:"
        print_info "  • Python: https://www.python.org/downloads/"
        print_info "  • Homebrew: https://brew.sh/"
        exit 1
    fi
fi

################################################################################
# Step 3: Check and Install Ollama
################################################################################

print_header "Step 3: Checking Ollama Installation"

if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version)
    print_success "Ollama found: $OLLAMA_VERSION"
else
    print_warning "Ollama not found. Installing..."

    if command -v brew &> /dev/null; then
        print_info "Installing Ollama via Homebrew..."
        brew install ollama
        print_success "Ollama installed"
    else
        print_info "Installing Ollama via direct download..."

        # Detect architecture
        ARCH=$(uname -m)
        if [ "$ARCH" = "arm64" ]; then
            OLLAMA_URL="https://ollama.com/download/Ollama-darwin-arm64.tgz"
        else
            OLLAMA_URL="https://ollama.com/download/Ollama-darwin-x64.tgz"
        fi

        print_info "Downloading Ollama for $ARCH..."
        curl -L "$OLLAMA_URL" -o /tmp/ollama.tgz

        print_info "Installing Ollama..."
        sudo tar -xzf /tmp/ollama.tgz -C /tmp/
        sudo cp -r /tmp/Ollama.app /Applications/

        # Clean up
        rm /tmp/ollama.tgz

        print_success "Ollama installed"
    fi
fi

################################################################################
# Step 4: Start Ollama Service
################################################################################

print_header "Step 4: Starting Ollama Service"

print_info "Checking if Ollama service is running..."

if pgrep -x "ollama" > /dev/null; then
    print_success "Ollama service is already running"
else
    print_info "Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    OLLAMA_PID=$!

    # Wait for service to start
    sleep 5

    if ps -p $OLLAMA_PID > /dev/null; then
        print_success "Ollama service started (PID: $OLLAMA_PID)"
    else
        print_error "Failed to start Ollama service"
        exit 1
    fi
fi

################################################################################
# Step 5: Download AI Models
################################################################################

print_header "Step 5: Downloading AI Models"

print_info "Required models:"
print_info "  • qwen2.5vl:3b (~2GB) - Vision model for screen understanding"
print_info "  • mxbai-embed-large (~1GB) - Text embedding for semantic search"
print_info ""
print_warning "This may take several minutes depending on your internet connection..."
echo ""

# Check if models are already downloaded
MODELS_INSTALLED=true

if ollama list | grep -q "qwen2.5vl"; then
    print_success "qwen2.5vl:3b already downloaded"
else
    print_info "Downloading qwen2.5vl:3b..."
    ollama pull qwen2.5vl:3b
    MODELS_INSTALLED=false
fi

if ollama list | grep -q "mxbai-embed-large"; then
    print_success "mxbai-embed-large already downloaded"
else
    print_info "Downloading mxbai-embed-large..."
    ollama pull mxbai-embed-large
    MODELS_INSTALLED=false
fi

if [ "$MODELS_INSTALLED" = true ]; then
    print_success "All models already downloaded"
else
    print_success "All models downloaded successfully"
fi

################################################################################
# Step 6: Install MemScreen
################################################################################

print_header "Step 6: Installing MemScreen"

print_info "Upgrading pip..."
python3 -m pip install --upgrade pip --user

print_info "Installing Python dependencies..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    python3 -m pip install -r "$PROJECT_ROOT/requirements.txt" --user
    print_success "Python dependencies installed"
else
    print_error "requirements.txt not found in project root: $PROJECT_ROOT"
    exit 1
fi

################################################################################
# Step 7: Request System Permissions
################################################################################

print_header "Step 7: Requesting System Permissions"

print_warning "MemScreen requires the following permissions:"
echo ""
echo "  1. 📹 Screen Recording"
echo "     • Required for capturing screen content"
echo ""
echo "  2. ♿ Accessibility"
echo "     • Required for automated screen capture"
echo ""
echo "  3. 🎤 Microphone"
echo "     • Required for audio recording (optional feature)"
echo ""

print_info "Opening System Preferences > Privacy & Security..."
print_warning "Please grant all requested permissions, then return here."
echo ""

read -p "Press Enter to open System Preferences..." -r
echo ""

# Open System Preferences to the appropriate pane
open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"

print_warning "After granting permissions:"
print_info "1. Return to this terminal"
print_info "2. Press Enter to continue"
echo ""

read -p "Press Enter when you have granted permissions..." -r
echo ""

print_success "Permissions step completed"

################################################################################
# Step 8: Create Desktop Shortcut
################################################################################

print_header "Step 8: Creating Desktop Shortcut"

DESKTOP_PATH="$HOME/Desktop"
APP_NAME="MemScreen"

# Create a symbolic link or launch script
if [ -d "$DESKTOP_PATH" ]; then
    cat > "$DESKTOP_PATH/MemScreen.command" <<EOF
#!/bin/bash
cd "$PROJECT_ROOT"
python3 start.py
EOF

    chmod +x "$DESKTOP_PATH/MemScreen.command"
    print_success "Desktop shortcut created"
else
    print_warning "Desktop directory not found. Skipping desktop shortcut."
fi

################################################################################
# Step 9: Verify Installation
################################################################################

print_header "Step 9: Verifying Installation"

print_info "Running verification checks..."

ERRORS=0

# Check Python
if command -v python3 &> /dev/null; then
    print_success "Python 3 is available"
else
    print_error "Python 3 not found"
    ERRORS=$((ERRORS + 1))
fi

# Check Ollama
if command -v ollama &> /dev/null; then
    print_success "Ollama is available"
else
    print_error "Ollama not found"
    ERRORS=$((ERRORS + 1))
fi

# Check Ollama service
if pgrep -x "ollama" > /dev/null; then
    print_success "Ollama service is running"
else
    print_warning "Ollama service is not running (will start automatically)"
fi

# Check models
if ollama list | grep -q "qwen2.5vl"; then
    print_success "Vision model (qwen2.5vl:3b) is installed"
else
    print_error "Vision model not found"
    ERRORS=$((ERRORS + 1))
fi

if ollama list | grep -q "mxbai-embed-large"; then
    print_success "Embedding model (mxbai-embed-large) is installed"
else
    print_error "Embedding model not found"
    ERRORS=$((ERRORS + 1))
fi

################################################################################
# Installation Complete
################################################################################

print_header "Installation Complete"

if [ $ERRORS -eq 0 ]; then
    print_success "MemScreen installed successfully!"
    echo ""
    print_info "To launch MemScreen:"
    echo "  • Double-click 'MemScreen' on your desktop"
    echo "  • Or run: cd \"$PROJECT_ROOT\" && python3 start.py"
    echo ""
    print_info "For more information, see the README.md file."
    echo ""
    print_success "Enjoy using MemScreen! 🦉"
else
    print_warning "Installation completed with $ERRORS error(s)"
    print_info "Please review the errors above and troubleshoot accordingly."
    exit 1
fi
