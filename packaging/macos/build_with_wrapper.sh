#!/bin/bash
set -e

echo "🔨 Building MemScreen with macOS foreground app support..."

# Build with PyInstaller
echo "[1/4] Building with PyInstaller..."
pyinstaller pyinstaller/memscreen_macos.spec --noconfirm --clean

# Add foreground app keys to Info.plist
echo "[2/4] Configuring Info.plist for foreground app..."
plutil -replace LSBackgroundOnly -bool NO dist/MemScreen.app/Contents/Info.plist 2>/dev/null || echo "Key LSBackgroundOnly added manually"
plutil -replace LSUIElement -bool NO dist/MemScreen.app/Contents/Info.plist 2>/dev/null || echo "Key LSUIElement added manually"
plutil -replace NSSupportsAutomaticTermination -bool NO dist/MemScreen.app/Contents/Info.plist 2>/dev/null || true

# Remove cv2's SDL2 to avoid conflicts with Kivy
echo "[3/4] Removing cv2's SDL2 libraries..."
rm -f dist/MemScreen.app/Contents/Frameworks/cv2/__dot__dylibs/libSDL2-2.0.0.dylib 2>/dev/null || true
echo "  ✅ Removed cv2's SDL2"

# Copy wrapper and rename original executable
echo "[4/4] Installing activation wrapper..."
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
