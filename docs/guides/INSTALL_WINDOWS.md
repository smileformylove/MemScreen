# 🪟 Windows Installation Guide

Complete installation instructions for Windows 10 and Windows 11.

---

## 📋 Prerequisites

- **OS Version**: Windows 10 (version 1903+) or Windows 11
- **Python**: 3.8 or higher
- **Disk Space**: 10GB free (for AI models)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Architecture**: x64 (64-bit)

---

## 🚀 Method 1: Source Code Installation (Recommended)

### Step 1: Install Git

Download and install Git for Windows:
- **Download**: https://git-scm.com/download/win
- **Installation**: Use default options
- **Verify**: Open Git Bash and run `git --version`

### Step 2: Install Python 3

1. **Download Python**: https://www.python.org/downloads/windows/
2. **Run Installer**:
   - ✅ Check "Add Python to PATH"
   - Click "Install Now"
3. **Verify Installation**:
   ```cmd
   python --version
   # Should be 3.8 or higher
   ```

### Step 3: Install Visual C++ Build Tools

Some Python packages require C++ build tools:

**Option A: Install Visual Studio Community** (Recommended)
- Download: https://visualstudio.microsoft.com/downloads/
- Install "Desktop development with C++" workload

**Option B: Install Build Tools Only**
- Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Install "Desktop development with C++"

### Step 4: Clone Repository

Using Git Bash:

```bash
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
```

Or using PowerShell:

```powershell
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
```

### Step 5: Create Virtual Environment

**Using Command Prompt (cmd):**

```cmd
python -m venv venv
venv\Scripts\activate
```

**Using PowerShell:**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Using Git Bash:**

```bash
python -m venv venv
source venv/Scripts/activate
```

You should see `(venv)` in your terminal prompt.

### Step 6: Install Dependencies

```cmd
pip install --upgrade pip
pip install -e .
```

**Note**: This may take several minutes and show build warnings. This is normal.

Key dependencies include:
- Kivy (GUI framework)
- OpenCV (screen capture)
- PyAutoGUI (automation)
- ChromaDB (vector database)

### Step 7: Install Ollama (AI Backend)

1. **Download Ollama**: https://ollama.com/download/windows
2. **Run Installer**: Double-click the downloaded `.exe` file
3. **Verify Installation**:
   ```cmd
   ollama --version
   ollama list
   ```

Ollama will start automatically on system boot.

### Step 8: Download AI Models (Optional)

MemScreen will download models on first use, or you can pre-download:

```cmd
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large
```

### Step 9: Launch MemScreen 🚀

```cmd
python setup\start.py
```

**What to expect on Windows:**
- Main window appears on screen
- System tray icon (may appear in notification area)
- Right-click window or tray icon for menu

---

## 🤖 Method 2: Batch Script Installation

For automated setup using batch scripts:

```cmd
git clone https://github.com/smileformylove/MemScreen.git && cd MemScreen
setup\install\install.bat
```

This script handles:
- ✅ Python version check
- ✅ Virtual environment creation
- ✅ Dependency installation
- ✅ Ollama installation check
- ✅ Configuration file creation

---

## 🐳 Method 3: WSL2 + Linux (Advanced)

For better compatibility, you can run MemScreen in WSL2:

### Install WSL2

```powershell
# Open PowerShell as Administrator
wsl --install
```

### Install MemScreen in WSL2

```bash
# Follow Linux installation guide
wsl
cd ~
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
./setup/install/install.sh
```

**Note**: Screen recording in WSL2 requires X11 forwarding and has limitations.

---

## 🔧 Common Issues on Windows

### Issue 1: "Python is not recognized"

**Solution**: Add Python to PATH or reinstall with PATH option:

1. Reinstall Python and check "Add Python to PATH"
2. Or manually add to PATH:
   - Search for "Environment Variables" in Windows
   - Edit PATH variable
   - Add: `C:\Users\YourUsername\AppData\Local\Programs\Python\Python3xx`
   - Add: `C:\Users\YourUsername\AppData\Local\Programs\Python\Python3xx\Scripts`

### Issue 2: "pip is not recognized"

**Solution**: Ensure Python Scripts folder is in PATH:
```
C:\Users\YourUsername\AppData\Local\Programs\Python\Python3xx\Scripts
```

### Issue 3: "Microsoft Visual C++ 14.0 is required"

**Solution**: Install Visual Studio Build Tools:
- Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Install "Desktop development with C++"

### Issue 4: "Kivy fails to install"

**Solution**: Install dependencies manually:

```cmd
pip install kivy[base]
pip install docutils pygments pypiwin32 kivy.deps.sdl2 kivy.deps.glew
pip install kivy.deps.gstreamer
```

### Issue 5: "OpenCV fails to install"

**Solution**: Install precompiled wheels:

```cmd
pip uninstall opencv-python opencv-contrib-python
pip install opencv-python opencv-contrib-python
```

### Issue 6: "Permission denied when running scripts"

**Solution**: Run PowerShell as Administrator or use Git Bash:

```bash
# In Git Bash
chmod +x setup/install/*.sh
./setup/install/install.sh
```

### Issue 7: "Ollama not running"

**Solution**: Start Ollama service:

```cmd
# Check if Ollama is running
tasklist | findstr ollama

# Start Ollama (from Start Menu or)
ollama serve
```

### Issue 8: "Screen capture not working"

**Solution**: Grant screen recording permission:

1. Settings → Privacy → Screen recording
2. Enable Python/Terminal
3. Restart MemScreen

---

## 📱 Windows-Specific Features

### System Tray Integration

MemScreen on Windows includes a system tray icon:

**Right-Click Menu:**
- 📹 Start/Stop Recording
- 🎬 View Recordings
- 🤖 AI Chat
- ⚙️ Settings
- ❌ Quit

### Keyboard Shortcuts

- `Win+Alt+R`: Start/Stop Recording
- `Win+Alt+Shift+R`: Select Region
- `Alt+F4`: Quit (when main window focused)

### Multi-Monitor Support

MemScreen supports multiple monitors on Windows:
- Record specific monitors
- Move window between monitors
- Region selection across monitors

---

## 🔄 Updating MemScreen

Using Command Prompt or Git Bash:

```bash
# Navigate to MemScreen directory
cd MemScreen

# Pull latest changes
git pull

# Update dependencies
venv\Scripts\activate
pip install --upgrade -r requirements.txt

# Relaunch
python setup\start.py
```

---

## 🗑️ Uninstallation

```cmd
# 1. Stop MemScreen if running

# 2. Remove MemScreen directory
cd ..
rmdir /s MemScreen

# 3. Uninstall Ollama
# Go to Settings → Apps → Installed Apps
# Find Ollama and click Uninstall

# 4. Remove user data (optional)
rmdir /s %USERPROFILE%\.memscreen

# 5. Remove virtual environment (if separate)
rmdir /s venv
```

---

## ✅ Installation Checklist

- [ ] Git installed
- [ ] Python 3.8+ installed and in PATH
- [ ] Visual C++ Build Tools installed
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Ollama installed and running
- [ ] AI models downloaded (or ready to auto-download)
- [ ] Screen recording permission granted
- [ ] MemScreen launches successfully

**All checked? You're ready to go!** 🎉

---

## 💡 Tips for Windows Users

### Performance Optimization

1. **Disable Windows Defender Real-time Protection** (for install directory only)
2. **Add Python to exclusions** in Windows Security
3. **Use SSD** for better recording performance
4. **Close unnecessary apps** when recording

### Recommended Terminal

- **Git Bash** - Best for Linux-like commands
- **Windows Terminal** - Modern, tabbed interface
- **PowerShell 7** - Latest PowerShell features

### Running at Startup

To auto-start MemScreen on Windows boot:

1. `Win+R`, type `shell:startup`
2. Create shortcut to `python setup\start.py`
3. Or use Task Scheduler

---

## 📚 Next Steps

1. **Read User Guide**: [USER_GUIDE.md](../USER_GUIDE.md)
2. **Configure Hotkeys**: Set up custom keyboard shortcuts
3. **Start Recording**: Try your first screen recording
4. **Explore AI Features**: Chat with your screen history

---

## 🆘 Getting Help

### Windows-Specific Resources

- 📖 [Kivy Windows Guide](https://kivy.org/doc/stable/installation/installation-windows.html)
- 🔧 [Python Windows](https://docs.python.org/3/using/windows.html)
- 🤖 [Ollama Windows](https://ollama.com/download/windows)

### Community Support

- 🐛 [Report Windows Issues](https://github.com/smileformylove/MemScreen/issues)
- 💬 [Windows Discussion](https://github.com/smileformylove/MemScreen/discussions)
- 📧 [Email Support](mailto:jixiangluo85@gmail.com)

---

**Enjoy using MemScreen on Windows!** 🪟
