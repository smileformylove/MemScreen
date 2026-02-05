#!/bin/bash
################################################################################
# MemScreen AppImage Build Script for Linux
#
# This script creates an AppImage package for MemScreen on Linux.
# AppImage is a universal Linux package format that works on most distributions.
#
# Prerequisites:
# - PyInstaller: pip install pyinstaller
# - appimagetool: Download from https://github.com/AppImage/AppImageKit/releases
#
# Usage: ./packaging/linux/build_appimage.sh
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
ARCH="x86_64"
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"

# Build paths
BUILD_DIR="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"
APPDIR="${APP_NAME}.AppDir"
PYINSTALLER_SPEC="$PROJECT_ROOT/pyinstaller/memscreen_linux.spec"

# Output paths
APPIMAGE_NAME="${APP_NAME}-${VERSION}-${ARCH}.AppImage"
APPIMAGE_PATH="$PROJECT_ROOT/${APPIMAGE_NAME}"

# AppImage tool download URL
APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage"

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

print_header "🔨 Building MemScreen AppImage"

echo "Configuration:"
echo "  Version: $VERSION"
echo "  Architecture: $ARCH"
echo "  Output: $APPIMAGE_NAME"
echo ""

################################################################################
# Check Prerequisites
################################################################################

print_header "Checking Prerequisites"

# Check if appimagetool is available
if ! command -v appimagetool &> /dev/null; then
    print_warning "appimagetool not found. Downloading..."

    # Download appimagetool
    wget -c "$APPIMAGETOOL_URL" -O "$PROJECT_ROOT/appimagetool"
    chmod +x "$PROJECT_ROOT/appimagetool"

    # Use local version
    APPIMAGETOOL="$PROJECT_ROOT/appimagetool"
    print_success "appimagetool downloaded"
else
    APPIMAGETOOL="appimagetool"
    print_success "appimagetool is installed"
fi

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
    print_error "PyInstaller spec not found: $PYINSTALLER_SPEC"
    exit 1
fi

# Detect if we need to create a Linux-specific spec
print_info "Note: Using macOS spec file - you may need to create a Linux-specific one"
print_warning "For production, create pyinstaller/memscreen_linux.spec"

################################################################################
# Step 1: Build with PyInstaller
################################################################################

print_header "Step 1: Building Application with PyInstaller"

print_info "Running PyInstaller..."
cd "$PROJECT_ROOT"

# Clean previous builds
print_info "Cleaning previous builds..."
rm -rf "$BUILD_DIR"
rm -rf "$DIST_DIR"
rm -rf "$APPDIR"

# Run PyInstaller
pyinstaller "$PYINSTALLER_SPEC" --noconfirm

# Check if build succeeded
if [ ! -d "$DIST_DIR/$APP_NAME" ]; then
    print_error "PyInstaller failed to create application"
    exit 1
fi

print_success "PyInstaller build complete"

################################################################################
# Step 2: Create AppDir Structure
################################################################################

print_header "Step 2: Creating AppDir Structure"

print_info "Creating AppDir directory tree..."

mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/metainfo"

print_success "AppDir structure created"

################################################################################
# Step 3: Populate AppDir
################################################################################

print_header "Step 3: Populating AppDir"

# Copy PyInstaller output
print_info "Copying application files..."
if [ -d "$DIST_DIR/$APP_NAME" ]; then
    cp -r "$DIST_DIR/$APP_NAME/"* "$APPDIR/usr/bin/"
    print_success "Application files copied"
else
    print_error "PyInstaller output not found: $DIST_DIR/$APP_NAME"
    exit 1
fi

# Copy desktop file
print_info "Copying desktop file..."
cp "$PROJECT_ROOT/packaging/linux/memscreen.desktop" "$APPDIR/memscreen.desktop"
cp "$PROJECT_ROOT/packaging/linux/memscreen.desktop" "$APPDIR/usr/share/applications/"
print_success "Desktop files copied"

# Copy icon
print_info "Copying icon files..."
if [ -f "$PROJECT_ROOT/assets/logo.png" ]; then
    cp "$PROJECT_ROOT/assets/logo.png" "$APPDIR/memscreen.png"
    cp "$PROJECT_ROOT/assets/logo.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/memscreen.png"
    cp "$PROJECT_ROOT/assets/logo.png" "$APPDIR/.DirIcon"
    print_success "Icon files copied"
else
    print_warning "Icon not found: $PROJECT_ROOT/assets/logo.png"
fi

# Copy AppRun launcher
print_info "Copying AppRun launcher..."
cp "$PROJECT_ROOT/packaging/linux/AppRun" "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"
print_success "AppRun launcher copied"

# Copy shared libraries
print_info "Bundling shared libraries..."
# Find and copy Python libraries and other dependencies
find "$APPDIR/usr/bin" -type f -name "*.so*" -exec cp {} "$APPDIR/usr/lib/" \; 2>/dev/null || true
print_success "Shared libraries copied"

################################################################################
# Step 4: Create AppMetadata
################################################################################

print_header "Step 4: Creating AppMetadata"

# Create AppStream metadata file
cat > "$APPDIR/usr/share/metainfo/memscreen.appdata.xml" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.smileformylove.MemScreen</id>
  <name>MemScreen</name>
  <summary>AI-Powered Visual Memory System</summary>
  <description>
    <p>MemScreen is your personal AI-powered visual memory system that captures,
    understands, and remembers everything on your screen.</p>
  </description>
  <url type="homepage">https://github.com/smileformylove/MemScreen</url>
  <url type="bugtracker">https://github.com/smileformylove/MemScreen/issues</url>
  <metadata_license>MIT</metadata_license>
  <project_license>MIT</project_license>
  <developer_name>Jixiang Luo</developer_name>
  <releases>
    <release version="${VERSION}" date="2026-01-01"/>
  </releases>
  <content_rating type="oars-1.1"/>
</component>
EOF

print_success "AppMetadata created"

################################################################################
# Step 5: Build AppImage
################################################################################

print_header "Step 5: Building AppImage"

# Remove existing AppImage if present
if [ -f "$APPIMAGE_PATH" ]; then
    print_info "Removing existing AppImage..."
    rm "$APPIMAGE_PATH"
fi

# Set environment variables for AppImage build
export ARCH="$ARCH"

print_info "Running appimagetool..."
"$APPIMAGETOOL" "$APPDIR" "$APPIMAGE_PATH"

# Check if AppImage was created
if [ ! -f "$APPIMAGE_PATH" ]; then
    print_error "AppImage build failed"
    exit 1
fi

# Make AppImage executable
chmod +x "$APPIMAGE_PATH"

# Get AppImage size
APPIMAGE_SIZE=$(du -h "$APPIMAGE_PATH" | cut -f1)

print_success "AppImage created"

################################################################################
# Step 6: Cleanup
################################################################################

print_header "Step 6: Cleanup"

print_info "Removing temporary files..."
# Keep AppDir for inspection, remove AppImage tool
rm -f "$PROJECT_ROOT/appimagetool"

print_success "Cleanup complete"

################################################################################
# Build Complete
################################################################################

print_header "Build Complete"

print_success "AppImage created successfully!"
echo ""
echo "Output: $APPIMAGE_PATH"
echo "Size: $APPIMAGE_SIZE"
echo ""
print_info "To test the AppImage:"
echo "  1. Make it executable (already done): chmod +x $APPIMAGE_NAME"
echo "  2. Run it: ./$APPIMAGE_NAME"
echo ""
print_info "To install system-wide:"
echo "  1. Copy to /opt or /usr/local/bin"
echo "  2. Copy desktop file to /usr/share/applications"
echo "  3. Copy icon to /usr/share/icons"
echo ""
print_success "Ready for distribution! 🎉"
