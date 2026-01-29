# MemScreen Packaging and Distribution Guide

This guide explains how to build and distribute MemScreen across different platforms.

## Overview

MemScreen uses PyInstaller for cross-platform packaging, creating standalone executables for:
- **Windows** (.exe)
- **macOS** (.app)
- **Linux** (executable)

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install PyInstaller
pip install pyinstaller
```

### Build for Current Platform

```bash
# Build the application
python build_all.py

# The output will be in dist/
# - MemScreen-0.4.0-{platform}.zip (distributable archive)
# - README.txt (user instructions)
# - install_dependencies.{sh|bat} (dependency installer)
```

## Platform-Specific Builds

### Building on macOS

```bash
# macOS can build for:
# 1. macOS (current platform) - automatic
# 2. Linux - requires Docker
# 3. Windows - not possible from macOS

# Build for macOS
python build_all.py
```

### Building on Windows

```bash
# Windows can build for:
# 1. Windows (current platform) - automatic
# 2. Linux - requires Docker or WSL
# 3. macOS - not possible from Windows

# Build for Windows
python build_all.py
```

### Building on Linux

```bash
# Linux can build for:
# 1. Linux (current platform) - automatic
# 2. Windows - requires MinGW or cross-compilation
# 3. macOS - not possible from Linux

# Build for Linux
python build_all.py
```

## Cross-Platform Builds Using Docker

For building on platforms you don't have access to, you can use Docker:

### Build for Linux on macOS/Windows

```bash
# Use a Linux container
docker run --rm -v $(pwd):/workspace python:3.11-slim bash -c "
  cd /workspace
  pip install -r requirements.txt
  pip install pyinstaller
  python build_all.py
"
```

### Build for Windows on Linux

```bash
# Use Wine with MinGW (more complex setup required)
# See: https://github.com/pyinstaller/pyinstaller/wiki/How-to-cross-compile
```

## Release Process

### Automated Release (Recommended)

```bash
# 1. Build the application
python build_all.py

# 2. Create GitHub release
python create_github_release.py

# This will:
# - Create and push git tag
# - Generate release notes
# - Upload build artifacts to GitHub
```

### Manual Release

#### 1. Create Git Tag

```bash
# Update version in pyproject.toml if needed
# Then create and push tag
git tag -a v0.4.0 -m "Release v0.4.0"
git push origin v0.4.0
```

#### 2. Build for All Platforms

You'll need to run `build_all.py` on each platform you want to support:
- On a Mac, build the macOS version
- On Windows, build the Windows version
- On Linux, build the Linux version

#### 3. Create GitHub Release

**Via Web UI:**
1. Go to: https://github.com/smileformylove/MemScreen/releases/new
2. Select the tag (e.g., v0.4.0)
3. Add release title and description
4. Attach the built archives:
   - `MemScreen-0.4.0-macos.zip` (from macOS)
   - `MemScreen-0.4.0-windows.zip` (from Windows)
   - `MemScreen-0.4.0-linux.zip` (from Linux)
5. Publish the release

**Via GitHub CLI:**
```bash
# Install GitHub CLI first
# macOS: brew install gh
# Windows: scoop install gh
# Linux: See https://cli.github.com/

# Create release with assets
gh release create v0.4.0 \
  --title "MemScreen v0.4.0" \
  --notes "Release notes here..." \
  dist/MemScreen-0.4.0-macos.zip \
  dist/MemScreen-0.4.0-windows.zip \
  dist/MemScreen-0.4.0-linux.zip
```

## File Structure

After building, the `dist/` directory contains:

```
dist/
├── MemScreen-0.4.0-{platform}.zip    # Distributable archive (upload this)
├── MemScreen/                         # Unbundled executable folder
│   ├── MemScreen.exe                  # Windows executable
│   └── [dependencies]
├── MemScreen.app/                     # macOS application bundle
│   └── Contents/
│       ├── MacOS/MemScreen
│       └── Resources/
├── README.txt                         # User instructions
└── install_dependencies.{sh|bat}      # Dependency installer
```

## Distribution Formats

### For End Users

Upload these files to GitHub Releases:

1. **macOS**: `MemScreen-0.4.0-macos.zip`
   - Contains MemScreen.app bundle
   - Users: Download, extract, drag to Applications

2. **Windows**: `MemScreen-0.4.0-windows.zip`
   - Contains MemScreen.exe and dependencies
   - Users: Download, extract, run MemScreen.exe

3. **Linux**: `MemScreen-0.4.0-linux.zip`
   - Contains MemScreen executable and dependencies
   - Users: Download, extract, run ./MemScreen/MemScreen

### Alternative: Create Installer Packages

For a more professional distribution:

#### macOS (.dmg or .pkg)

```bash
# Already supported by build_simple.sh
cd macos
./build_simple.sh  # Creates DMG
```

#### Windows (.msi or .exe installer)

Use tools like:
- NSIS: https://nsis.sourceforge.io/
- Inno Setup: https://jrsoftware.org/isinfo.php
- WiX Toolset: https://wixtoolset.org/

#### Linux (.deb, .rpm, or .AppImage)

```bash
# .deb (Debian/Ubuntu)
# Use fpm: https://fpm.readthedocs.io/
fpm -s dir -t deb -n memscreen -v 0.4.0 \
  dist/MemScreen=/opt/memcreen

# .rpm (Red Hat/Fedora)
fpm -s dir -t rpm -n memscreen -v 0.4.0 \
  dist/MemScreen=/opt/memcreen

# .AppImage (Universal Linux)
# See: https://github.com/AppImage/AppImageKit
```

## Code Signing (Optional)

### macOS Code Signing

```bash
# Sign the app
codesign --force --deep --verify --verbose \
  --sign "Developer ID Application: Your Name" \
  dist/MemScreen.app

# Notarize for distribution
xcrun notarytool submit dist/MemScreen.app \
  --apple-id "your@email.com" \
  --password "app-specific-password" \
  --team-id "TEAM_ID"

# Staple the ticket
xcrun stapler staple dist/MemScreen.app
```

### Windows Code Signing

```bash
# Sign the executable
signtool sign /f certificate.pfx /p password \
  /t http://timestamp.digicert.com \
  dist/MemScreen/MemScreen.exe
```

## Versioning

Update version numbers in:
1. `pyproject.toml` - Project version
2. `memscreen/__init__.py` - Module version
3. `build_all.py` - APP_VERSION constant
4. `MemScreen.spec` - APP_VERSION constant

Then create a new git tag:
```bash
git tag -a v0.4.1 -m "Release v0.4.1"
git push origin v0.4.1
```

## CI/CD Automation

For automated builds, you can use GitHub Actions:

### Example: .github/workflows/build.yml

```yaml
name: Build Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    strategy:
      matrix:
        os: [macos-latest, windows-latest, ubuntu-latest]

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Build
        run: python build_all.py

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: memscreen-${{ matrix.os }}
          path: dist/MemScreen-*.zip

  release:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Download all artifacts
        uses: actions/download-artifact@v3

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: memscreen-*/MemScreen-*.zip
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Troubleshooting

### Build Fails

**Problem**: PyInstaller fails to build
**Solution**:
```bash
# Clean build cache
rm -rf build/ dist/
pip install pyinstaller --upgrade

# Try again
python build_all.py
```

### Application Won't Start

**Problem**: Built app crashes on startup
**Solution**:
```bash
# Run from console to see errors
./dist/MemScreen/MemScreen  # Linux
./dist/MemScreen.app/Contents/MacOS/MemScreen  # macOS
.\dist\MemScreen\MemScreen.exe  # Windows
```

### Missing Dependencies

**Problem**: "Module not found" errors
**Solution**:
1. Add missing imports to `hiddenimports` in `MemScreen.spec`
2. Rebuild: `python build_all.py`

### Large File Size

**Problem**: Distribution is too large
**Solution**:
1. Use UPX compression (enabled by default)
2. Exclude unnecessary packages in `excludes` in `MemScreen.spec`
3. Use `--strip` option to remove debug symbols

## Support

For packaging issues:
- Open an issue: https://github.com/smileformylove/MemScreen/issues
- Email: jixiangluo85@gmail.com

## Resources

- PyInstaller Documentation: https://pyinstaller.org/
- GitHub Releases Guide: https://docs.github.com/en/repositories/releasing-projects-on-github
- Cross-Compilation: https://github.com/pyinstaller/pyinstaller/wiki/How-to-cross-compile
