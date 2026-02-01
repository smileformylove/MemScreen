### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

# MemScreen macOS Installation Guide

This guide will help you install MemScreen on macOS.

## Quick Installation

### Prerequisites

1. **Python 3.8+**
   ```bash
   python3 --version
   ```
   If not installed, download from [python.org](https://www.python.org/downloads/)

2. **pip** (Python package manager)
   ```bash
   python3 -m pip --version
   ```

### Step 1: Install Ollama

Ollama is required for running the AI models locally.

```bash
# Using Homebrew
brew install ollama

# Or download from https://ollama.com/download
```

### Step 2: Download AI Models

```bash
# Start Ollama service
ollama serve

# In another terminal, download the models
ollama pull qwen3:1.7b
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large:latest
```

### Step 3: Install MemScreen

```bash
# Clone the repository
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen

# Install dependencies
pip3 install -r requirements.txt

# Or install in development mode
pip3 install -e .
```

### Step 4: Run MemScreen

```bash
# Launch the GUI application
python3 start.py

# Or use command-line tools
python3 -m memscreen.memscreen
```

## Building a macOS Application Bundle

For creating a distributable .app bundle, see the comprehensive build guide:

```bash
# Development build (unsigned, for testing)
cd build/macos
chmod +x build.sh
./build.sh

# Release build (signed and notarized, for distribution)
chmod +x build_release.sh
./build_release.sh --signing-identity "Developer ID Application: Your Name (TEAM_ID)"
```

See [docs/MACOS_BUILD_GUIDE.md](../docs/MACOS_BUILD_GUIDE.md) for complete build instructions.

## Using MemScreen

### Screen Recording

```bash
python3 start.py

# Or command-line
python3 -m memscreen.memscreen --interval 10 --duration 60
```

### Chat Interface

```bash
python3 start.py
# Click on "Chat" tab in the GUI
```

## macOS-Specific Features

### Permissions

When running MemScreen for the first time, you may need to grant permissions:

1. **Screen Recording**: Required to capture your screen
   - Go to System Settings → Privacy & Security → Screen Recording
   - Add Terminal or your Python interpreter

2. **Accessibility**: Required for keyboard/mouse monitoring (process mining)
   - Go to System Settings → Privacy & Security → Accessibility
   - Add Terminal or your Python interpreter

3. **Microphone**: Required for audio recording (new feature)
   - Go to System Settings → Privacy & Security → Microphone
   - Add Terminal or your Python interpreter

### Launch from Spotlight

After installation, you can use Spotlight to launch MemScreen:

1. Press `Cmd + Space`
2. Type "MemScreen"
3. Press Enter

### Create Desktop Shortcuts

```bash
# Create a shortcut on your Desktop
cat > ~/Desktop/MemScreen.command << 'EOF'
#!/bin/bash
cd /path/to/MemScreen
python3 start.py
EOF
chmod +x ~/Desktop/MemScreen.command
```

## Troubleshooting

### "command not found: memscreen"

This means the installation path isn't in your PATH. Try:

```bash
# Use Python module syntax
python3 -m memscreen.memscreen

# Or add to your PATH (add to ~/.zshrc or ~/.bash_profile)
export PATH="$HOME/.local/bin:$PATH"
```

### Ollama connection error

Make sure Ollama is running:

```bash
# Check if Ollama is running
pgrep ollama

# Start Ollama if not running
ollama serve
```

### Permission denied when recording screens

Grant Screen Recording permission:
1. System Settings → Privacy & Security → Screen Recording
2. Enable Terminal or your Python interpreter
3. Restart MemScreen

### macOS Gatekeeper warnings

If you see "MemScreen cannot be opened because the developer cannot be verified":

```bash
# Right-click the app and select "Open"
# Or run from Terminal with:
xattr -cr /path/to/MemScreen.app
```

### Audio recording not working

For microphone recording, ensure:
1. Microphone is connected and working
2. Python has microphone permissions in System Settings
3. PyAudio is installed: `pip3 install pyaudio`

For system audio recording on macOS:
```bash
# Install BlackHole virtual audio device
brew install blackhole-2ch
```

See [docs/AUDIO_RECORDING.md](../docs/AUDIO_RECORDING.md) for details.

## Uninstallation

To remove MemScreen from your Mac:

```bash
# Navigate to MemScreen directory
cd MemScreen

# Uninstall the Python package
pip3 uninstall memscreen

# Remove virtual environment (if used)
deactivate  # if in venv
rm -rf venv

# Remove data
rm -rf ~/db/

# Remove the source code
cd ..
rm -rf MemScreen
```

## Updating

```bash
# Navigate to MemScreen directory
cd MemScreen

# Pull latest changes
git pull origin main

# Update dependencies
pip3 install -r requirements.txt --upgrade
```

## Support

- GitHub: https://github.com/smileformylove/MemScreen
- Issues: https://github.com/smileformylove/MemScreen/issues
- Email: jixiangluo85@gmail.com

## Additional Documentation

- [macOS Build Guide](../docs/MACOS_BUILD_GUIDE.md) - Complete build and distribution guide
- [Audio Recording Guide](../docs/AUDIO_RECORDING.md) - Audio feature documentation
- [README](../README.md) - General project documentation
