# MemScreen macOS Installation Guide

This guide will help you install MemScreen on macOS.

## Quick Installation

### Automated Installation (Recommended)

The easiest way to install MemScreen on macOS:

```bash
curl -fsSL https://raw.githubusercontent.com/smileformylove/MemScreen/main/macos/install.sh | bash
```

This automated script will:
- Check your Python installation
- Install all Python dependencies
- Install MemScreen
- Install Ollama (if needed)
- Download all required AI models
- Create command-line shortcuts

## Manual Installation

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
pip install git+https://github.com/smileformylove/MemScreen.git
```

### Step 4: Verify Installation

```bash
# Check if commands are available
memscreen --help
memscreen-chat --help
memscreen-screenshots --help
memscreen-process-mining --help
```

## Using MemScreen

### Screen Recording

```bash
memscreen

# With custom settings
memscreen --interval 10 --duration 60 --screenshot-interval 2.0
```

### Chat Interface

```bash
memscreen-chat
```

### Screenshot Browser

```bash
memscreen-screenshots
```

### Process Mining

```bash
memscreen-process-mining
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

### Launch from Spotlight

After installation, you can use Spotlight to launch MemScreen:

1. Press `Cmd + Space`
2. Type "memscreen"
3. Press Enter

### Create Desktop Shortcuts

```bash
# Create a shortcut on your Desktop
cat > ~/Desktop/MemScreen.command << 'EOF'
#!/bin/bash
memscreen
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

## Uninstallation

To remove MemScreen from your Mac:

```bash
# Uninstall the Python package
pip uninstall memscreen

# Remove data
rm -rf ~/db/

# Remove command shortcuts (if created)
sudo rm -f /usr/local/bin/memscreen*
```

## Updating

```bash
# Update to the latest version
pip install --upgrade git+https://github.com/smileformylove/MemScreen.git
```

## Support

- GitHub: https://github.com/smileformylove/MemScreen
- Issues: https://github.com/smileformylove/MemScreen/issues
- Email: jixiangluo85@gmail.com

## Homebrew Formula

Alternatively, you can install via Homebrew (formula available in this directory):

```bash
brew install ./macos/MemScreen.rb
```

Note: The formula requires manual setup. Use the automated installer for the best experience.
