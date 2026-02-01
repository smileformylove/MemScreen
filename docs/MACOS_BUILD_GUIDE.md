# MemScreen macOS Release Build Guide

Complete guide for building signed and notarized macOS releases for MemScreen.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Development Build](#development-build)
4. [Release Build](#release-build)
5. [Troubleshooting](#troubleshooting)
6. [Distribution](#distribution)

---

## Prerequisites

### Required Software

1. **Python 3.8+**
   ```bash
   python3 --version
   ```

2. **Xcode Command Line Tools**
   ```bash
   xcode-select --install
   ```

3. **PyInstaller**
   ```bash
   pip3 install pyinstaller
   ```

### For Code Signing & Notarization (Release Builds Only)

1. **Apple Developer Account**
   - Enroll in [Apple Developer Program](https://developer.apple.com/programs/)
   - Cost: $99/year

2. **Developer ID Certificate**
   ```bash
   # Create certificate from Xcode
   # Xcode → Preferences → Accounts → Manage Certificates
   ```

3. **Application-Specific Password**
   - Generate at: https://appleid.apple.com
   - Required for notarization

---

## Quick Start

### For Development/Testing (No Signing)

```bash
# 1. Navigate to project
cd /path/to/MemScreen

# 2. Run build script (no signing required)
./build/macos/build.sh

# 3. Test the app
open dist/MemScreen.app
```

**Result**: Unsigned .app bundle for personal use.

---

## Development Build

### Build Unsigned Application Bundle

```bash
cd build/macos
chmod +x build.sh
./build.sh
```

**What it does:**
1. Cleans previous builds
2. Creates PyInstaller spec file
3. Builds application bundle
4. Ad-hoc signs the app (for local testing)
5. Optionally creates DMG

**Output:**
- Application: `dist/MemScreen.app`
- DMG (optional): `dist/MemScreen_0.5.0_macOS.dmg`

### Icon Setup

To add a custom icon:

1. Create icon in .icns format
2. Place at `assets/icon.icns`
3. Rebuild

```bash
# Create icon from PNG (example)
mkdir -p assets
# Use iconutil to create .icns file
```

---

## Release Build

### Overview

Release builds require:
1. **Code Signing**: With your Apple Developer certificate
2. **Notarization**: Submit to Apple for verification
3. **Stapling**: Attach notarization ticket to app

This ensures users can install your app without macOS security warnings.

### Step-by-Step Process

#### 1. Set Environment Variables

```bash
# Your signing identity (find with: security find-identity -v -p "Mac Developer")
export SIGNING_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"

# Your Apple ID and password
export APPLE_ID="your@email.com"
export APPLE_PASSWORD="abcd-efgh-ijkl-mnop-qrst"

# Your Team ID (find in Apple Developer portal)
export TEAM_ID="YOUR_TEAM_ID"
```

#### 2. Build and Notarize

```bash
cd build/macos
chmod +x build_release.sh

# Run release build with signing
./build_release.sh \
    --signing-identity "$SIGNING_IDENTITY" \
    --apple-id "$APPLE_ID" \
    --team-id "$TEAM_ID"
```

#### 3. Verify Output

```bash
# Check code signature
codesign -v -d dist/MemScreen.app

# Check notarization
spctl -a -vv dist/MemScreen_0.5.0_macOS.dmg
```

---

## Detailed Build Process

### Phase 1: Build

```bash
# Build with PyInstaller
pyinstaller \
    --clean \
    --noconfirm \
    --workpath build/macOS/build \
    --distpath dist \
    build/macOS/memscreen.spec
```

### Phase 2: Sign Application

```bash
# Deep sign (signs all nested code)
codesign --force --deep --sign "$SIGNING_IDENTITY" dist/MemScreen.app

# Verify signature
codesign -v dist/MemScreen.app
```

### Phase 3: Create DMG

```bash
# Create temporary DMG (500MB)
hdiutil create -volname "MemScreen" -fs 500M dist/temp.dmg

# Mount DMG
hdiutil attach dist/temp.dmg -mountpoint build/mount

# Copy app
cp -R dist/MemScreen.app build/mount/

# Create Applications symlink
ln -s /Applications build/mount/Applications

# Unmount
hdiutil detach build/mount

# Compress to DMG
hdiutil convert dist/temp.dmg -format UDZO -o dist/MemScreen_0.5.0_macOS.dmg
rm dist/temp.dmg
```

### Phase 4: Sign DMG

```bash
codesign --sign "$SIGNING_IDENTITY" dist/MemScreen_0.5.0_macOS.dmg
```

### Phase 5: Notarize

```bash
# Submit for notarization
xcrun notarytool submit dist/MemScreen_0.5.0_macOS.dmg \
    --apple-id "$APPLE_ID" \
    --password "$APPLE_PASSWORD" \
    --team-id "$TEAM_ID" \
    --output-format xml
```

**Response:**
```xml
<RequestUUID>your-request-uuid</RequestUUID>
```

### Phase 6: Wait for Completion

```bash
# Check notarization status (poll every 30 seconds)
xcrun notarytool info your-request-uuid

# When status shows "Accepted", staple the ticket
xcrun stapler staple dist/MemScreen_0.5.0_macOS.dmg
```

### Phase 7: Verify Notarization

```bash
# Verify notarization
spctl -a -vv dist/MemScreen_0.5.0_macOS.dmg
```

---

## Troubleshooting

### Issue: "PyInstaller not found"

**Solution:**
```bash
pip3 install pyinstaller
```

### Issue: "Code signing failed"

**Possible causes:**
1. Wrong signing identity
2. Certificate expired
3. File already signed

**Solution:**
```bash
# List available signing identities
security find-identity -v -p "Mac Developer"

# Verify certificate
security find-identity -v -s "Developer ID Application: Your Name" | grep "Valid"
```

### Issue: "Notarization failed"

**Common errors:**

1. **Invalid Apple ID or password**
   - Generate new app-specific password

2. **Binary already modified**
   - Rebuild from scratch

3. **Team ID mismatch**
   - Verify Team ID in Apple Developer portal

4. **Notarization timeout**
   - Wait up to 10 minutes
   - Check status: `xcrun notarytool info <uuid>`

### Issue: "App won't open - damaged"

**Cause:** Missing or invalid signature

**Solution:**
```bash
# Verify signature
codesign -v -d dist/MemScreen.app

# Check quarantine flag
xattr -l dist/MemScreen.app

# Remove quarantine (if needed)
xattr -d com.apple.quarantine dist/MemScreen.app
```

### Issue: "Microphone permission denied"

**Cause:** Missing NSMicrophoneUsageDescription in Info.plist

**Solution:** Add to `memscreen.spec`:
```python
info_plist={
    'NSMicrophoneUsageDescription': 'MemScreen needs microphone access to record audio.',
    # ...
}
```

---

## Distribution

### Options for Distribution

1. **GitHub Releases**
   - Upload `.dmg` file to releases page
   - Users can download and install directly

2. **Website Download**
   - Host `.dmg` on your website
   - Include SHA256 checksum for verification

3. **Direct Distribution**
   - Share `.dmg` file via email/file sharing
   - Users must right-click → Open (security warning)

### Versioning

Update versions in:
1. `pyproject.toml` → `version = "0.5.0"`
2. `build/macos/memscreen.spec` → `CFBundleVersion`
3. `build/macos/build.sh` → `VERSION`

### Updating Build Scripts

When adding new dependencies:

1. Add to `pyproject.toml`:
   ```toml
   dependencies = [
       "new-package>=1.0.0",
   ]
   ```

2. Add to `memscreen.spec` hiddenimports:
   ```python
   hiddenimports=[
       'new_package',
   ]
   ```

3. Rebuild and test

---

## Automation

### GitHub Actions Workflow

Create `.github/workflows/release-macos.yml`:

```yaml
name: Build macOS Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: macos-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller

    - name: Import certificates
      env:
        CERTIFICATES_P12: ${{ secrets.CERTIFICATES_P12 }}
        CERTIFICATES_P12_PASSWORD: ${{ secrets.CERTIFICATES_P12_PASSWORD }}
      run: |
        echo "$CERTIFICATES_P12" | base64 --decode > certificates.p12
        security create-keychain -p build_keychain build.keychain
        security import certificates.p12 -k build_keychain -P "$CERTIFICATES_P12_PASSWORD" -T
        security set-key-partition-list -S apple-tool:,build_keychain -s -k build_keychain
        security unlock-keychain -p build_keychain -s build_keychain
        security find-identity -v
        security default-keychain -s build_keychain

    - name: Build and sign
      env:
        SIGNING_IDENTITY: ${{ secrets.SIGNING_IDENTITY }}
      run: |
        cd build/macos
        chmod +x build.sh
        ./build.sh
        codesign --force --deep --sign "$SIGNING_IDENTITY" ../../dist/MemScreen.app

    - name: Create DMG
      run: |
        hdiutil create -volname MemScreen -fs 500M dist/temp.dmg
        hdiutil attach dist/temp.dmg -mountpoint build/mount
        cp -R dist/MemScreen.app build/mount/
        ln -s /Applications build/mount/Applications
        hdiutil detach build/mount
        hdiutil convert dist/temp.dmg -format UDZO -o dist/MemScreen_${{ github.ref_name }}.dmg
        rm dist/temp.dmg

    - name: Upload asset
      uses: actions/upload-artifact@v3
      with:
        name: MemScreen-macOS-DMG
        path: dist/MemScreen_*.dmg
```

---

## Best Practices

### 1. Version Control

- Tag releases in Git: `git tag -a v0.5.0 -m "Version 0.5.0"`
- Update version in all files consistently
- Keep CHANGELOG

### 2. Testing Before Release

```bash
# Test on clean macOS system
# 1. Unzip DMG
# 2. Right-click → Open
# 3. Test all features
# 4. Check microphone permissions
# 5. Verify screen recording works
```

### 3. Security

- Never commit private keys or certificates
- Use environment variables for sensitive data
- Revoke old certificates when compromised
- Keep app-specific passwords rotated

### 4. File Size Optimization

```bash
# Use UPX to reduce binary size
pip install upx
# UPX is already enabled in build script
```

### 5. User Experience

- Include README in DMG
- Add uninstaller script
- Provide first-run setup wizard
- Include user guide

---

## Appendix

### File Structure

```
MemScreen/
├── build/
│   └── macos/
│       ├── build.sh          # Development build
│       ├── build_release.sh # Release build with notarization
│       └── memscreen.spec     # PyInstaller configuration
├── dist/
│   └── MemScreen.app/        # Application bundle
├── assets/
│   └── icon.icns            # Application icon
├── start.py                 # Application entry point
└── memscreen/               # Source code
```

### Useful Commands

```bash
# Find signing identity
security find-identity -v -p "Mac Developer"

# Check signature
codesign -v -d /path/to/app.app

# Check quarantine flag
xattr -l /path/to/app.app

# Remove quarantine
xattr -d com.apple.quarantine /path/to/app.app

# Verify notarization
spctl -a -vv /path/to/file.dmg

# List all apps for user
mdfind "kMDItemKind == 'Application'"
```

---

## Resources

- [Apple Code Signing Guide](https://developer.apple.com/support/code-signing/)
- [Apple Notarization Guide](https://developer.apple.com/documentation/security/notarizing-macos-software/)
- [PyInstaller macOS Documentation](https://pyinstaller.org/en/stable/platforms.html#macos-x)
- [codesign Manual](https://developer.apple.com/library/archive/technotes/tn2206/)
- [xcrun notarytool Guide](https://developer.apple.com/documentation/security/notarization/mac-apps-notarizing-macos-software)

---

**Last Updated:** 2026-02-01
**Author:** Jixiang Luo (jixiangluo85@gmail.com)
**License:** MIT
