#!/bin/bash
set -e

echo "🔨 Building MemScreen with macOS foreground app support..."

# Build with PyInstaller
echo "[1/3] Building with PyInstaller..."
pyinstaller pyinstaller/memscreen_macos.spec --noconfirm --clean

# Add foreground app keys to Info.plist
echo "[2/3] Configuring Info.plist for foreground app..."
plutil -replace LSBackgroundOnly -bool NO dist/MemScreen.app/Contents/Info.plist 2>/dev/null || echo "Key LSBackgroundOnly added manually"
plutil -replace LSUIElement -bool NO dist/MemScreen.app/Contents/Info.plist 2>/dev/null || echo "Key LSUIElement added manually"
plutil -replace NSSupportsAutomaticTermination -bool NO dist/MemScreen.app/Contents/Info.plist 2>/dev/null || true

# Copy wrapper and rename original executable
echo "[3/3] Installing activation wrapper..."
chmod +x packaging/macos/app_wrapper.sh
mv dist/MemScreen.app/Contents/MacOS/MemScreen dist/MemScreen.app/Contents/MacOS/MemScreen.bin
cp packaging/macos/app_wrapper.sh dist/MemScreen.app/Contents/MacOS/MemScreen
chmod +x dist/MemScreen.app/Contents/MacOS/MemScreen

echo ""
echo "✅ Build complete: dist/MemScreen.app"
echo ""
echo "To test:"
echo "  open dist/MemScreen.app"
echo ""
echo "To install to Applications:"
echo "  cp -R dist/MemScreen.app /Applications/"
