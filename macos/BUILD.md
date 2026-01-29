# MemScreen macOS Build Guide

This guide explains how to build and distribute MemScreen as a native macOS application.

## Prerequisites

### For Building:
- Xcode Command Line Tools: `xcode-select --install`
- Python 3.8+
- Homebrew (for distributing Ollama)

### For Users:
- macOS 10.15 (Catalina) or later
- Python 3.8+ (system or from python.org)
- Ollama: `brew install ollama`
- ~5GB free disk space

## Build Methods

### Method 1: Simple Build (Recommended)

The simple build creates a standalone .app bundle that includes the MemScreen source code.

```bash
cd macos
chmod +x build_simple.sh
./build_simple.sh
```

This creates:
- `dist/MemScreen.app` - Double-clickable application
- `dist/install_dependencies.sh` - Dependency installer script
- `dist/README.txt` - User instructions
- `dist/MemScreen-0.4.0-macOS.dmg` - Distributable DMG (optional)

### Method 2: Full Build with py2app

The full build creates a truly standalone .app with bundled Python.

```bash
cd macos
chmod +x build_app.sh
./build_app.sh
```

**Note:** py2app can be tricky. The simple build is recommended for most users.

## Distribution

### Option 1: Distribute as DMG (Recommended)

1. Build the app (DMG is created automatically):
   ```bash
   ./build_simple.sh
   ```

2. Upload the DMG:
   - File: `dist/MemScreen-0.4.0-macOS.dmg`
   - Upload to GitHub Releases
   - Users download and open the DMG
   - Drag MemScreen.app to Applications folder

### Option 2: Distribute as .app Bundle

1. Build the app:
   ```bash
   ./build_simple.sh
   ```

2. Create a zip archive:
   ```bash
   cd dist
   zip -r MemScreen-macOS.zip MemScreen.app README.txt install_dependencies.sh
   ```

3. Upload to GitHub Releases

### Option 3: GitHub Release with Assets

1. Tag the release:
   ```bash
   git tag -a v0.4.0 -m "Release v0.4.0"
   git push origin v0.4.0
   ```

2. Create Release on GitHub:
   - Go to repository Releases page
   - Click "Draft a new release"
   - Select the tag
   - Upload DMG or zip file
   - Publish the release

## User Installation Flow

### Automatic Installation (from DMG)

1. User downloads `MemScreen-0.4.0-macOS.dmg`
2. Opens DMG (auto-mounts)
3. Drags MemScreen.app to Applications
4. Ejects DMG
5. Double-clicks MemScreen.app to launch

### Manual Installation (from .app)

1. User downloads and unzips `MemScreen-macOS.zip`
2. Copies MemScreen.app to /Applications
3. Right-click → Open (first time, to bypass Gatekeeper)
4. Confirms "Open" in the dialog
5. App launches and checks dependencies

## First Run Experience

### First Launch

1. App checks for Python 3
2. App checks for Ollama
3. App checks for AI models
4. App provides clear instructions if anything is missing

### Dependency Check Dialogs

If Ollama is missing:
```
MemScreen requires Ollama to run AI models.

Please install Ollama:
  brew install ollama

Then download AI models:
  ollama pull qwen2.5vl:3b
  ollama pull mxbai-embed-large

Visit ollama.com for more information.
```

## Code Signing (Optional)

For distribution outside GitHub, you may want to code-sign the app to avoid Gatekeeper warnings.

### 1. Get a Developer ID

```bash
# Check if you have a Developer ID
security find-identity -v -p codesigning
```

If not, enroll in Apple Developer Program ($99/year).

### 2. Sign the App

```bash
codesign --force --deep --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  dist/MemScreen.app
```

### 3. Verify Signature

```bash
codesign -v --verify --strict dist/MemScreen.app
```

### 4. Notarize the App (for distribution)

```bash
# Upload for notarization
xcrun notarytool submit MemScreen.app \
  --apple-id "your@email.com" \
  --password "app-specific-password" \
  --team-id "TEAM_ID"

# Staple the notary ticket
xcrun stapler staple dist/MemScreen.app
```

## Troubleshooting

### Build Issues

**Problem**: `py2app` fails to build
```
Solution: Use the simple build method (build_simple.sh) instead
```

**Problem**: App won't open (Gatekeeper)
```
Solution: Right-click → Open, then confirm "Open"
Or: xattr -cr com.apple.quarantine dist/MemScreen.app
```

**Problem**: App crashes immediately
```
Solution: Check Console.app for crash logs
Most common issue: Missing Python or Ollama
```

### Distribution Issues

**Problem**: DMG size is too large
```
Solution: Create a minimal app bundle without frameworks
Use build_simple.sh which excludes heavy frameworks
```

**Problem**: App doesn't work on other Macs
```
Solution: Ensure all dependencies are properly bundled
Or use install_dependencies.sh to install on first run
```

## Advanced: Creating an Installer Package

For a professional installer experience, you can use Apple's Packages tool:

1. Download Packages from: https://s.sudara.free.fr/Packages/about/

2. Create a new project:
   - Add MemScreen.app as a component
   - Add pre-install scripts to check for Python
   - Add post-install scripts to set up Ollama
   - Configure installer options

3. Build the installer package (.pkg)

4. Distribute the .pkg file

## Versioning

Update version numbers in:
- `macos/build/Info.plist` - CFBundleVersion and CFBundleShortVersionString
- `macos/build_simple.sh` - APP_VERSION
- `macos/build_app.sh` - APP_VERSION

When releasing:
```bash
git tag -a v0.4.0 -m "Release v0.4.0"
git push origin v0.4.0
```

## Support

For build issues:
- Open an issue on GitHub: https://github.com/smileformylove/MemScreen/issues
- Email: jixiangluo85@gmail.com

For user issues:
- See README.txt included in the distribution
- Check the main README.md
