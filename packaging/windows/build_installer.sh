#!/bin/bash
################################################################################
# MemScreen Windows Installer Build Script
#
# This script builds the Windows NSIS installer for MemScreen.
# It requires PyInstaller to be run first to create the dist/MemScreen directory.
#
# Prerequisites:
# - makensis: Available on macOS via Homebrew, or on Windows via NSIS
# - PyInstaller: pip install pyinstaller
#
# Usage: ./packaging/windows/build_installer.sh
################################################################################

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERSION="0.5.0"
APP_NAME="MemScreen"
INSTALLER_NAME="MemScreen-Setup-${VERSION}.exe"
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"

# Build paths
DIST_DIR="$PROJECT_ROOT/dist"
PYINSTALLER_SPEC="$PROJECT_ROOT/pyinstaller/memscreen_windows.spec"
NSIS_SCRIPT="$PROJECT_ROOT/packaging/windows/installer.nsi"

# Functions
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

################################################################################
# Main Build Process
################################################################################

print_header "🔨 Building Windows Installer"

echo "Configuration:"
echo "  Version: $VERSION"
echo "  Installer: $INSTALLER_NAME"
echo ""

# Detect platform
PLATFORM=$(uname -s)
case "$PLATFORM" in
    Linux*)
        print_warning "Building on Linux (you may need Wine for NSIS)"
        ;;
    Darwin*)
        print_info "Building on macOS"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        print_info "Building on Windows"
        ;;
    *)
        print_error "Unknown platform: $PLATFORM"
        exit 1
        ;;
esac

################################################################################
# Check Prerequisites
################################################################################

print_header "Checking Prerequisites"

# Check if makensis is installed
if ! command -v makensis &> /dev/null; then
    print_warning "makensis not found. Installing..."

    case "$PLATFORM" in
        Darwin*)
            # macOS
            if command -v brew &> /dev/null; then
                brew install makensis
                print_success "makensis installed"
            else
                print_error "Homebrew not found. Please install makensis manually:"
                print_info "  brew install makensis"
                exit 1
            fi
            ;;
        Linux*)
            # Linux
            print_info "Install makensis using your package manager:"
            print_info "  Ubuntu/Debian: sudo apt-get install nsis"
            print_info "  Fedora: sudo dnf install nsis"
            print_info "  Arch: sudo pacman -S nsis"
            exit 1
            ;;
        *)
            print_error "Please install NSIS from: https://nsis.sourceforge.io/"
            exit 1
            ;;
    esac
else
    print_success "makensis is installed"
fi

# Check if PyInstaller spec exists
if [ ! -f "$PYINSTALLER_SPEC" ]; then
    print_error "PyInstaller spec not found: $PYINSTALLER_SPEC"
    exit 1
fi

# Check if NSIS script exists
if [ ! -f "$NSIS_SCRIPT" ]; then
    print_error "NSIS script not found: $NSIS_SCRIPT"
    exit 1
fi

################################################################################
# Step 1: Build Windows Executable with PyInstaller
################################################################################

print_header "Step 1: Building Windows Executable"

print_info "Running PyInstaller..."
cd "$PROJECT_ROOT"

# Clean previous builds
print_info "Cleaning previous builds..."
rm -rf "$DIST_DIR"

# Check if we're on Windows or need Wine
if [[ "$PLATFORM" == MINGW* ]] || [[ "$PLATFORM" == MSYS* ]] || [[ "$PLATFORM" == CYGWIN* ]]; then
    # Native Windows
    python pyinstaller "$PYINSTALLER_SPEC" --noconfirm
elif [ "$PLATFORM" == "Darwin" ]; then
    # macOS - can't build Windows binaries without Wine
    print_warning "Building Windows binaries on macOS is not supported"
    print_info "Options:"
    print_info "  1. Run this script on Windows"
    print_info "  2. Use Wine + Wine Python (experimental)"
    print_info "  3. Use GitHub Actions or CI/CD for cross-platform builds"

    read -p "Continue anyway? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi

    print_error "Cannot build Windows binaries on macOS"
    print_info "Please run this script on Windows or use a CI/CD pipeline"
    exit 1
else
    print_error "Cannot build Windows binaries on this platform"
    exit 1
fi

# Check if executable was created
if [ ! -d "$DIST_DIR/MemScreen" ]; then
    print_error "PyInstaller failed to create Windows executable"
    print_error "Expected: $DIST_DIR/MemScreen"
    exit 1
fi

print_success "Windows executable created"

################################################################################
# Step 2: Build NSIS Installer
################################################################################

print_header "Step 2: Building NSIS Installer"

print_info "Creating installer with NSIS..."
cd "$PROJECT_ROOT/packaging/windows"

# Remove existing installer if present
if [ -f "$PROJECT_ROOT/$INSTALLER_NAME" ]; then
    print_info "Removing existing installer..."
    rm "$PROJECT_ROOT/$INSTALLER_NAME"
fi

# Build NSIS installer
makensis "$NSIS_SCRIPT"

# Check if installer was created
if [ ! -f "$PROJECT_ROOT/$INSTALLER_NAME" ]; then
    print_error "NSIS failed to create installer"
    exit 1
fi

# Get installer size
INSTALLER_SIZE=$(du -h "$PROJECT_ROOT/$INSTALLER_NAME" | cut -f1)

print_success "NSIS installer created"

################################################################################
# Build Complete
################################################################################

print_header "Build Complete"

print_success "Windows installer created successfully!"
echo ""
echo "Output: $PROJECT_ROOT/$INSTALLER_NAME"
echo "Size: $INSTALLER_SIZE"
echo ""
print_info "To test the installer:"
echo "  1. Transfer $INSTALLER_NAME to a Windows machine"
echo "  2. Double-click to run the installer"
echo "  3. Follow the installation prompts"
echo ""
print_success "Ready for distribution! 🎉"
