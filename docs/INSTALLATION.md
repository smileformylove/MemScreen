# MemScreen Installation Guide

This guide provides detailed instructions for installing MemScreen on different platforms using the installation packages.

## Table of Contents

- [Overview](#overview)
- [Quick Install](#quick-install)
- [Platform-Specific Instructions](#platform-specific-instructions)
  - [macOS](#macos)
  - [Windows](#windows)
  - [Linux](#linux)
- [Manual Installation](#manual-installation)
- [Troubleshooting](#troubleshooting)
- [Building Installers](#building-installers)

---

## Overview

MemScreen provides platform-specific installers for a seamless installation experience:

- **macOS**: DMG disk image with drag-and-drop installation
- **Windows**: NSIS installer with guided setup wizard
- **Linux**: AppImage universal package

All installers include:
- ✅ Automated dependency installation (Python, Ollama)
- ✅ AI model downloading (~3GB)
- ✅ System permission requests
- ✅ Desktop shortcuts and menu entries

---

## Quick Install

### Prerequisites

Before installing, ensure your system meets these requirements:

**macOS:**
- macOS 11.0 (Big Sur) or later
- 4GB RAM minimum, 8GB recommended
- 5GB free disk space

**Windows:**
- Windows 10 or later (64-bit)
- 4GB RAM minimum, 8GB recommended
- 5GB free disk space

**Linux:**
- Any modern distribution (Ubuntu 20.04+, Fedora 33+, Arch, etc.)
- 4GB RAM minimum, 8GB recommended
- 5GB free disk space

### Download

Download the appropriate installer for your platform from the [Releases](https://github.com/smileformylove/MemScreen/releases) page.

---

## Platform-Specific Instructions

### macOS

#### Option 1: DMG Installer (Recommended)

1. **Download** `MemScreen-{version}.dmg`

2. **Open** the DMG file:
   ```bash
   open MemScreen-{version}.dmg
   ```

3. **Drag and drop** MemScreen.app to Applications folder

4. **Launch** from Applications:
   ```bash
   open /Applications/MemScreen.app
   ```

5. **Grant permissions** when prompted:
   - Screen Recording
   - Accessibility
   - Microphone (optional)

#### Option 2: Automated Installation Script

1. **Download** the source code:
   ```bash
   git clone https://github.com/smileformylove/MemScreen.git
   cd MemScreen
   ```

2. **Run** the installation script:
   ```bash
   sudo ./install/install.sh
   ```

3. **Follow** the prompts to install:
   - Python 3.8+ (if needed)
   - Ollama AI runtime
   - Required AI models
   - System permissions

4. **Launch** MemScreen:
   ```bash
   python3 start.py
   ```

#### Permissions on macOS

MemScreen requires the following permissions:

**Screen Recording:**
- System Preferences > Privacy & Security > Privacy > Screen Recording
- Check the box next to MemScreen
- Restart the application

**Accessibility:**
- System Preferences > Privacy & Security > Privacy > Accessibility
- Check the box next to MemScreen
- Restart the application

**Microphone (optional):**
- System Preferences > Privacy & Security > Privacy > Microphone
- Check the box next to MemScreen
- Only required for audio recording features

---

### Windows

#### Option 1: NSIS Installer (Recommended)

1. **Download** `MemScreen-Setup-{version}.exe`

2. **Run** the installer as Administrator:
   - Right-click > "Run as Administrator"

3. **Follow** the setup wizard:
   - Accept the license agreement
   - Choose installation components
   - Select installation location
   - Wait for dependencies to install

4. **Launch** MemScreen:
   - From desktop shortcut
   - From Start Menu
   - Or: `python start.py`

#### Option 2: Automated Installation Script

1. **Download** the source code:
   ```powershell
   git clone https://github.com/smileformylove/MemScreen.git
   cd MemScreen
   ```

2. **Run** the installation script as Administrator:
   ```powershell
   Right-click install/install.bat > Run as Administrator
   ```

3. **Follow** the prompts

4. **Launch** MemScreen:
   ```powershell
   python start.py
   ```

#### Firewall Settings

When MemScreen first runs, Windows Firewall may prompt for network access:

- **Allow** network access for Ollama communication
- This is required for the AI features to work

---

### Linux

#### Option 1: AppImage (Recommended)

1. **Download** `MemScreen-{version}-x86_64.AppImage`

2. **Make it executable**:
   ```bash
   chmod +x MemScreen-{version}-x86_64.AppImage
   ```

3. **Run** the AppImage:
   ```bash
   ./MemScreen-{version}-x86_64.AppImage
   ```

4. **Optional: Install system-wide**:
   ```bash
   sudo cp MemScreen-{version}-x86_64.AppImage /usr/local/bin/memscreen
   sudo chmod +x /usr/local/bin/memscreen
   ```

#### Option 2: Manual Installation

1. **Install** dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-venv

   # Fedora
   sudo dnf install python3 python3-pip
   ```

2. **Install** Ollama:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

3. **Download** AI models:
   ```bash
   ollama pull qwen2.5vl:3b
   ollama pull mxbai-embed-large
   ```

4. **Install** MemScreen:
   ```bash
   git clone https://github.com/smileformylove/MemScreen.git
   cd MemScreen
   pip3 install -r requirements.txt
   ```

5. **Launch** MemScreen:
   ```bash
   python3 start.py
   ```

---

## Manual Installation

If you prefer to install MemScreen manually without using the installers:

### Step 1: Install Python

Ensure Python 3.8 or later is installed:

```bash
# Check version
python3 --version

# If not installed:
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt install python3

# Windows
# Download from https://www.python.org/downloads/
```

### Step 2: Install Ollama

Install Ollama AI runtime:

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download
```

Start Ollama service:

```bash
ollama serve &
```

### Step 3: Download AI Models

Download required models (~3GB):

```bash
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large
```

### Step 4: Install MemScreen

```bash
# Clone repository
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen

# Install Python dependencies
pip install -r requirements.txt

# Launch MemScreen
python start.py
```

---

## Troubleshooting

### macOS Issues

**"MemScreen can't be opened because it is from an unidentified developer"**

Right-click the app > "Open" > "Open" in the dialog

**"Ollama command not found"**

Make sure Ollama is in your PATH:
```bash
export PATH=$PATH:/Applications/Ollama.app/Contents/MacOS
```

**Permissions not working**

- Open System Preferences > Privacy & Security
- Find MemScreen in the list
- Click the lock to make changes
- Check all required permissions
- Restart MemScreen

### Windows Issues

**"Windows protected your PC"**

Click "More info" > "Run anyway"

**Installation fails with "Ollama download failed"**

1. Download Ollama manually from https://ollama.com/download
2. Install to default location
3. Re-run the MemScreen installer

**Models fail to download**

1. Open Command Prompt as Administrator
2. Run:
   ```powershell
   %APPDATA%\Ollama\ollama.exe pull qwen2.5vl:3b
   %APPDATA%\Ollama\ollama.exe pull mxbai-embed-large
   ```

### Linux Issues

**AppImage won't run**

1. Make sure it's executable:
   ```bash
   chmod +x MemScreen-*.AppImage
   ```

2. Check for missing dependencies:
   ```bash
   ./MemScreen-*.AppImage --appimage-extract
   ./squashfs-root/AppRun
   ```

**Ollama service not running**

```bash
# Start Ollama
ollama serve &

# Check status
ps aux | grep ollama
```

### General Issues

**Out of memory**

- Close other applications
- Use a smaller AI model:
  ```bash
  ollama pull qwen2.5vl:0.5b  # Smaller model
  ```

**Slow performance**

- Ensure Ollama is running:
  ```bash
  ollama serve &
  ```
- Check if GPU acceleration is available
- Reduce screen capture frequency in settings

**Models already downloaded but not found**

```bash
# List installed models
ollama list

# Re-download if needed
python memscreen/utils/model_downloader.py --download
```

---

## Building Installers

If you want to build the installers yourself:

### Prerequisites

```bash
# Install PyInstaller
pip install pyinstaller

# macOS: Install additional tools
brew install create-dmg

# Windows: Install NSIS
# Download from https://nsis.sourceforge.io/

# Linux: Install AppImage tools
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
```

### Build macOS DMG

```bash
# 1. Build .app with PyInstaller
pyinstaller pyinstaller/memscreen_macos.spec --noconfirm

# 2. Create DMG
./packaging/macos/build_dmg.sh

# 3. Sign the app (optional, requires Apple Developer certificate)
CODESIGN_IDENTITY="Developer ID Application: Your Name" \
  ./packaging/macos/sign_app.sh
```

### Build Windows Installer

```bash
# On Windows or with Wine:
makensis packaging/windows/installer.nsi

# Or use the build script (Windows only)
./packaging/windows/build_installer.sh
```

### Build Linux AppImage

```bash
./packaging/linux/build_appimage.sh
```

---

## System Requirements

### Minimum

- **CPU**: x86_64 (Intel/AMD)
- **RAM**: 4GB
- **Storage**: 5GB (excluding AI models)
- **OS**:
  - macOS 11.0+
  - Windows 10+
  - Linux (glibc 2.17+)

### Recommended

- **CPU**: Apple Silicon (M1/M2) or Intel/AMD with SSE4.2
- **RAM**: 8GB+
- **Storage**: 10GB SSD
- **GPU** (optional): NVIDIA GPU with CUDA support for faster AI inference

---

## Uninstallation

### macOS

```bash
# Remove app
rm -rf /Applications/MemScreen.app

# Remove data
rm -rf ~/Library/Application\ Support/MemScreen
rm -rf ~/Library/Caches/MemScreen

# Remove Ollama (optional)
brew uninstall ollama
```

### Windows

Use the uninstaller from:
- Control Panel > Programs and Features > MemScreen > Uninstall

Or manually:
```powershell
# Remove installation directory
rmdir /s %LOCALAPPDATA%\MemScreen

# Remove data
rmdir /s %APPDATA%\MemScreen

# Unregister
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\MemScreen" /f
```

### Linux

```bash
# Remove AppImage
rm /usr/local/bin/memscreen

# Remove data
rm -rf ~/.local/share/MemScreen
rm -rf ~/.config/MemScreen
```

---

## Next Steps

After installation:

1. **Launch** MemScreen
2. **Configure** screen capture settings
3. **Grant** required permissions
4. **Start** capturing your screen!
5. **Search** your visual memory with natural language

For usage instructions, see the [main README](../README.md).

---

## Support

- **Documentation**: [README.md](../README.md)
- **Issues**: [GitHub Issues](https://github.com/smileformylove/MemScreen/issues)
- **Discussions**: [GitHub Discussions](https://github.com/smileformylove/MemScreen/discussions)

---

**Enjoy using MemScreen! 🦉**
