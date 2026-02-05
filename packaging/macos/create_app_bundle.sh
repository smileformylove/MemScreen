#!/bin/bash
set -e

# Create a proper macOS .app bundle from PyInstaller output
# This script creates an .app that runs as a foreground application

VERSION="0.5.0"
APP_NAME="MemScreen"
PYINSTALLER_DIST="dist/MemScreen"
FINAL_APP="dist/${APP_NAME}_fixed.app"

echo "🔨 Creating macOS .app bundle with foreground support..."

# Check if PyInstaller output exists
if [ ! -d "$PYINSTALLER_DIST" ]; then
    echo "❌ PyInstaller output not found at $PYINSTALLER_DIST"
    echo "   Please run: pyinstaller pyinstaller/memscreen_macos.spec --noconfirm"
    exit 1
fi

# Remove previous app bundle
rm -rf "$FINAL_APP"

# Create .app bundle structure
mkdir -p "$FINAL_APP/Contents/MacOS"
mkdir -p "$FINAL_APP/Contents/Resources"
mkdir -p "$FINAL_APP/Contents/Frameworks"

# Copy PyInstaller output
cp -R "$PYINSTALLER_DIST"/* "$FINAL_APP/Contents/MacOS/"

# Create Info.plist with foreground app settings
cat > "$FINAL_APP/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>MemScreen</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.smileformylove.MemScreen</string>
    <key>CFBundleName</key>
    <string>MemScreen</string>
    <key>CFBundleDisplayName</key>
    <string>MemScreen</string>
    <key>CFBundleShortVersionString</key>
    <string>0.5.0</string>
    <key>CFBundleVersion</key>
    <string>0.5.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
    <key>NSSupportsAutomaticTermination</key>
    <false/>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
    <key>NSAppleMusicUsageDescription</key>
    <string>MemScreen needs access to your screen to provide AI-powered visual memory.</string>
    <key>NSCameraUsageDescription</key>
    <string>MemScreen needs camera access for video recording functionality.</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>MemScreen needs microphone access for audio recording.</string>
    <key>LSBackgroundOnly</key>
    <false/>
    <key>LSUIElement</key>
    <false/>
    <key>LSMultipleInstancesProhibited</key>
    <true/>
</dict>
</plist>
EOF

# Copy icon if exists
if [ -f "assets/logo.icns" ]; then
    cp "assets/logo.icns" "$FINAL_APP/Contents/Resources/AppIcon.icns"
fi

# Make executable executable
chmod +x "$FINAL_APP/Contents/MacOS/MemScreen"

echo "✅ Created $FINAL_APP"
echo ""
echo "To test the app:"
echo "  open \"$FINAL_APP\""
echo ""
echo "To install to Applications:"
echo "  cp -R \"$FINAL_APP\" /Applications/"
