#!/bin/bash
################################################################################
# MemScreen Code Signing Script for macOS
#
# This script signs the MemScreen application bundle for distribution.
# Code signing is required for:
# - Distribution outside the Mac App Store
# - Notarization by Apple
# - Avoiding Gatekeeper warnings on user machines
#
# Prerequisites:
# - Apple Developer Certificate installed in Keychain
# - Xcode Command Line Tools
#
# Usage: CODESIGN_IDENTITY="Developer ID Application: Your Name" ./packaging/macos/sign_app.sh
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
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
APP_PATH="$PROJECT_ROOT/dist/$APP_NAME.app"

# Code signing identity (can be overridden via environment variable)
CODESIGN_IDENTITY="${CODESIGN_IDENTITY:-}"

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
# Main Signing Process
################################################################################

print_header "🔐 Code Signing for MemScreen"

echo "Configuration:"
echo "  App: $APP_PATH"
echo "  Version: $VERSION"
echo ""

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    print_error "Application not found: $APP_PATH"
    print_info "Please build the app first using: ./packaging/macos/build_dmg.sh"
    exit 1
fi

# Check for code signing identity
if [ -z "$CODESIGN_IDENTITY" ]; then
    print_warning "No code signing identity specified"
    echo ""
    echo "Available identities:"
    security find-identity -v -p codesigning | grep "Developer ID Application"
    echo ""
    read -p "Enter identity (or press Enter to skip signing): " CODESIGN_IDENTITY

    if [ -z "$CODESIGN_IDENTITY" ]; then
        print_warning "Skipping code signing"
        print_info "Note: The app will trigger Gatekeeper warnings without signing"
        exit 0
    fi
fi

print_info "Using identity: $CODESIGN_IDENTITY"

################################################################################
# Step 1: Sign the Application Bundle
################################################################################

print_header "Step 1: Signing Application Bundle"

print_info "Removing existing signatures (if any)..."
codesign --remove-signature "$APP_PATH" 2>/dev/null || true

print_info "Signing application with deep signature..."
codesign \
    --force \
    --deep \
    --sign "$CODESIGN_IDENTITY" \
    --options runtime \
    --entitlements "$PROJECT_ROOT/packaging/macos/entitlements.plist" \
    "$APP_PATH"

print_success "Application signed"

################################################################################
# Step 2: Verify Signature
################################################################################

print_header "Step 2: Verifying Signature"

print_info "Verifying code signature..."
if codesign --verify --deep --strict "$APP_PATH" 2>&1; then
    print_success "Signature verification passed"
else
    print_error "Signature verification failed"
    codesign -dvv "$APP_PATH"
    exit 1
fi

# Display detailed signature information
print_info "Signature details:"
codesign -dvv "$APP_PATH"

################################################################################
# Step 3: Check for Hardened Runtime
################################################################################

print_header "Step 3: Checking Hardened Runtime"

print_info "Checking hardened runtime entitlements..."
if codesign --display --entitlements - "$APP_PATH" 2>/dev/null | grep -q "com.apple.security.cs.allow-jit"; then
    print_success "Hardened runtime is enabled"
else
    print_warning "Hardened runtime may not be fully enabled"
    print_info "This is optional for development but recommended for distribution"
fi

################################################################################
# Step 4: Sign DMG (if it exists)
################################################################################

DMG_PATH="$PROJECT_ROOT/$APP_NAME-$VERSION.dmg"

if [ -f "$DMG_PATH" ]; then
    print_header "Step 4: Signing DMG"

    print_info "Signing DMG image..."
    codesign --force --sign "$CODESIGN_IDENTITY" "$DMG_PATH"
    print_success "DMG signed"
fi

################################################################################
# Signing Complete
################################################################################

print_header "Signing Complete"

print_success "Application signed successfully!"
echo ""
print_info "Signed application: $APP_PATH"
if [ -f "$DMG_PATH" ]; then
    print_info "Signed DMG: $DMG_PATH"
fi
echo ""
print_warning "Note: Signed applications still need notarization for distribution"
print_info "See: https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution"
echo ""
print_success "Ready for notarization! 🎉"
