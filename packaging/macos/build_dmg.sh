#!/bin/bash
################################################################################
# MemScreen DMG Build Script for macOS
#
# This script creates a distributable DMG disk image for MemScreen.
# It uses PyInstaller to build the .app bundle, then packages it into a DMG.
#
# Prerequisites:
# - PyInstaller: pip install pyinstaller
#
# Usage: ./packaging/macos/build_dmg.sh
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
APP_FILENAME="MemScreen.app"
VOLUME_NAME="MemScreen"
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"

# Build paths
BUILD_DIR="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"
DMG_TEMP_DIR="$BUILD_DIR/dmg"
PYINSTALLER_SPEC="$PROJECT_ROOT/pyinstaller/memscreen_macos.spec"
INFO_PLIST="$PROJECT_ROOT/packaging/macos/Info.plist"

# Output paths
APP_PATH="$DIST_DIR/$APP_FILENAME"
DMG_NAME="$APP_NAME-$VERSION.dmg"
DMG_PATH="$PROJECT_ROOT/$DMG_NAME"

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

print_header "🔨 Building MemScreen DMG"

echo "Configuration:"
echo "  Version: $VERSION"
echo "  App Name: $APP_NAME"
echo "  Output: $DMG_NAME"
echo ""

# Check prerequisites
print_info "Checking prerequisites..."

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    print_warning "PyInstaller not found. Installing..."
    pip install pyinstaller
    print_success "PyInstaller installed"
else
    print_success "PyInstaller is installed"
fi

# Check if spec file exists
if [ ! -f "$PYINSTALLER_SPEC" ]; then
    print_error "PyInstaller spec file not found: $PYINSTALLER_SPEC"
    exit 1
fi

# Check if Info.plist exists
if [ ! -f "$INFO_PLIST" ]; then
    print_error "Info.plist not found: $INFO_PLIST"
    exit 1
fi

################################################################################
# Step 1: Build .app Bundle with PyInstaller
################################################################################

print_header "Step 1: Building .app Bundle"

print_info "Running PyInstaller..."
cd "$PROJECT_ROOT"

# Clean previous builds
print_info "Cleaning previous builds..."
rm -rf "$BUILD_DIR"
rm -rf "$DIST_DIR"

# Run PyInstaller
pyinstaller "$PYINSTALLER_SPEC" --noconfirm

# Check if app was created
if [ ! -d "$APP_PATH" ]; then
    print_error "PyInstaller failed to create .app bundle"
    print_error "Expected: $APP_PATH"
    exit 1
fi

print_success ".app bundle created"

# Copy Info.plist to app bundle
print_info "Copying Info.plist to app bundle..."
cp "$INFO_PLIST" "$APP_PATH/Contents/Info.plist"
print_success "Info.plist copied"

# Copy assets if they exist
if [ -d "$PROJECT_ROOT/assets" ]; then
    print_info "Copying assets to app bundle..."
    cp -R "$PROJECT_ROOT/assets" "$APP_PATH/Contents/Resources/"
    print_success "Assets copied"
fi

################################################################################
# Step 2: Create DMG Structure
################################################################################

print_header "Step 2: Creating DMG Structure"

# Clean and create temporary DMG directory
print_info "Preparing DMG structure..."
rm -rf "$DMG_TEMP_DIR"
mkdir -p "$DMG_TEMP_DIR"

# Copy app to temp directory
print_info "Copying .app bundle to DMG directory..."
cp -R "$APP_PATH" "$DMG_TEMP_DIR/"
print_success ".app bundle copied"

# Create Applications symlink
print_info "Creating Applications symlink..."
ln -s /Applications "$DMG_TEMP_DIR/Applications"
print_success "Applications symlink created"

################################################################################
# Step 3: Create DMG
################################################################################

print_header "Step 3: Creating DMG Image"

# Remove existing DMG if it exists
if [ -f "$DMG_PATH" ]; then
    print_info "Removing existing DMG..."
    rm "$DMG_PATH"
fi

print_info "Creating disk image..."

# Create DMG with hdiutil
hdiutil create \
    -volname "$VOLUME_NAME" \
    -srcfolder "$DMG_TEMP_DIR" \
    -ov \
    -format UDZO \
    -imagekey zlib-level=9 \
    "$DMG_PATH"

# Check if DMG was created
if [ ! -f "$DMG_PATH" ]; then
    print_error "Failed to create DMG"
    exit 1
fi

# Get DMG size
DMG_SIZE=$(du -h "$DMG_PATH" | cut -f1)

print_success "DMG created: $DMG_NAME ($DMG_SIZE)"

################################################################################
# Step 4: Cleanup
################################################################################

print_header "Step 4: Cleanup"

print_info "Removing temporary files..."
rm -rf "$DMG_TEMP_DIR"

print_success "Cleanup complete"

################################################################################
# Build Complete
################################################################################

print_header "Build Complete"

print_success "DMG package created successfully!"
echo ""
echo "Output: $DMG_PATH"
echo "Size: $DMG_SIZE"
echo ""
print_info "To test the DMG:"
echo "  1. Double-click $DMG_NAME to mount"
echo "  2. Drag MemScreen.app to Applications"
echo "  3. Launch from Applications"
echo ""
print_success "Ready for distribution! 🎉"
