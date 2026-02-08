# 🍎 macOS Installation Guide

Complete installation instructions for macOS.

---

## 📋 Prerequisites

- **macOS Version**: 10.15 (Catalina) or later
- **Python**: 3.8 or higher
- **Disk Space**: 10GB free (for AI models)
- **Memory**: 4GB RAM minimum, 8GB recommended

---

## 🚀 Method 1: Source Code Installation (Recommended)

Best for developers and users who want full control.

### Step 1: Install Xcode Command Line Tools

```bash
xcode-select --install
```

Click "Install" in the pop-up dialog and wait for installation to complete.

### Step 2: Install Python 3

macOS includes Python, but you may want the latest version:

```bash
# Option A: Using Homebrew (Recommended)
brew install python3

# Option B: Using official installer
# Download from https://www.python.org/downloads/macos/
```

Verify installation:
```bash
python3 --version  # Should be 3.8+
```

### Step 3: Clone Repository

```bash
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
```

### Step 4: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 5: Install Dependencies

```bash
pip install --upgrade pip
pip install -e .
```

This may take several minutes. Key dependencies include:
- Kivy (GUI framework)
- OpenCV (screen capture)
- PyObjC (macOS integration)
- ChromaDB (vector database)

### Step 6: Install Ollama (AI Backend)

```bash
# Option A: Using Homebrew
brew install ollama

# Option B: Using official installer
# Download from https://ollama.com/download
```

Start Ollama service:
```bash
ollama serve
```

Verify Ollama is running (in a new terminal):
```bash
ollama list
```

### Step 7: Download AI Models (Optional)

MemScreen will download models on first use, or you can pre-download:

```bash
# Vision model (~3GB)
ollama pull qwen2.5vl:3b

# Embedding model (~500MB)
ollama pull mxbai-embed-large
```

### Step 8: Launch MemScreen 🚀

```bash
python setup/start.py
```

**What to expect on macOS:**
- A floating ball appears in the top-right corner
- Main window starts minimized
- Right-click the ball to access all features
- Left-click to show/hide the main window
- Drag the ball to any position

---

## 🤖 Method 2: Automated Installation

For a fully automated setup:

```bash
git clone https://github.com/smileformylove/MemScreen.git && cd MemScreen
./setup/install/install.sh
```

This script handles everything automatically:
- ✅ Checks Python version
- ✅ Creates virtual environment
- ✅ Installs dependencies
- ✅ Installs Ollama (via Homebrew if available)
- ✅ Downloads AI models
- ✅ Creates configuration files

---

## 📦 Method 3: Homebrew Installation (Coming Soon)

```bash
# Soon you'll be able to install directly:
brew install memscreen
```

---

## 🔧 Common Issues on macOS

### Issue 1: "xcrun: error: invalid active developer path"

**Solution**: Install Xcode Command Line Tools:
```bash
xcode-select --install
```

### Issue 2: "Permission denied when running scripts"

**Solution**: Make scripts executable:
```bash
chmod +x setup/install/*.sh
chmod +x setup/run.sh
```

### Issue 3: "PyObjC installation fails"

**Solution**: Install additional dependencies:
```bash
brew install python3
pip install --upgrade pip
pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz
```

### Issue 4: "Ollama not found"

**Solution**: Install Ollama manually:
```bash
# Using Homebrew
brew install ollama

# Or download installer from
# https://ollama.com/download
```

### Issue 5: "Screen recording permission denied"

**Solution**: Grant screen recording permission:
1. Open System Settings → Privacy & Security → Screen Recording
2. Find Terminal or your Python interpreter
3. Toggle the switch to enable
4. Restart MemScreen

### Issue 6: "Floating ball doesn't appear"

**Solution**: Check app is running and not blocked:
1. Check terminal for errors
2. Ensure no firewall blocking
3. Try restarting: `python setup/start.py`
4. Check if main window appeared instead

---

## 📱 macOS-Specific Features

### Floating Ball Mode

MemScreen on macOS starts with a floating ball:

**Right-Click Menu:**
- 📹 Start/Stop Recording
- 🎬 View Recordings
- 🤖 AI Chat
- ⚙️ Settings
- ❌ Quit

**Keyboard Shortcuts:**
- `Cmd+R`: Start/Stop Recording
- `Cmd+Shift+R`: Select Region
- `Cmd+Q`: Quit

**Multi-Monitor Support:**
The floating ball works across all monitors and spaces.

---

## 🔄 Updating MemScreen

```bash
# Navigate to MemScreen directory
cd MemScreen

# Pull latest changes
git pull

# Update dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Relaunch
python setup/start.py
```

---

## 🗑️ Uninstallation

```bash
# Remove MemScreen directory
cd ..
rm -rf MemScreen

# Remove Ollama (optional)
brew uninstall ollama

# Remove user data (optional)
rm -rf ~/.memscreen
```

---

## 📚 Next Steps

1. **Read User Guide**: [USER_GUIDE.md](../USER_GUIDE.md)
2. **Configure Recording**: Set up hotkeys and storage
3. **Start Recording**: Try your first screen recording
4. **Explore AI Features**: Chat with your screen history

---

## 🆘 Getting Help

### macOS-Specific Resources

- 📖 [Kivy macOS Guide](https://kivy.org/doc/stable/installation/installation-macos.html)
- 🔧 [PyObjC Documentation](https://pyobjc.readthedocs.io/)
- 🤖 [Ollama macOS](https://ollama.com/download/mac)

### Community Support

- 🐛 [Report macOS Issues](https://github.com/smileformylove/MemScreen/issues)
- 💬 [macOS Discussion](https://github.com/smileformylove/MemScreen/discussions)
- 📧 [Email Support](mailto:jixiangluo85@gmail.com)

---

## ✅ Installation Checklist

- [ ] Xcode Command Line Tools installed
- [ ] Python 3.8+ installed
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Ollama installed and running
- [ ] AI models downloaded (or ready to auto-download)
- [ ] Screen recording permission granted
- [ ] MemScreen launches successfully

**All checked? You're ready to go!** 🎉

---

**Enjoy using MemScreen on macOS!** 🍎
