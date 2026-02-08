# 🐧 Linux Installation Guide

Complete installation instructions for Linux (Ubuntu, Debian, Fedora, etc.).

---

## 📋 Prerequisites

- **OS Version**: Ubuntu 20.04+ / Debian 11+ / Fedora 35+ / Arch Linux
- **Python**: 3.8 or higher
- **Disk Space**: 10GB free (for AI models)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Display Server**: X11 or Wayland

---

## 🚀 Method 1: Source Code Installation (Recommended)

Best for all Linux distributions.

### Step 1: Install System Dependencies

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    libsdl2-2.0-0 \
    libportaudio2 \
    libpulse-dev
```

#### Fedora

```bash
sudo dnf install -y \
    python3 \
    python3-pip \
    gcc \
    gcc-c++ \
    glib2 \
    libSM \
    libXext \
    libXrender \
    gstreamer1 \
    gstreamer1-plugins-base \
    gstreamer1-plugins-good \
    SDL2 \
    portaudio \
    pulseaudio-libs
```

#### Arch Linux

```bash
sudo pacman -S \
    python \
    python-pip \
    base-devel \
    glib2 \
    libsm \
    libxext \
    libxrender \
    gstreamer \
    gst-plugins-base \
    gst-plugins-good \
    sdl2 \
    portaudio \
    pulseaudio
```

### Step 2: Verify Python Installation

```bash
python3 --version  # Should be 3.8+
```

If Python is too old or not installed:

```bash
# Ubuntu/Debian
sudo apt-get install python3.11 python3.11-venv

# Fedora
sudo dnf install python3.11

# Arch Linux
sudo pacman -S python3
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

Key dependencies include:
- Kivy (GUI framework)
- OpenCV (screen capture)
- PyAutoGUI (automation)
- ChromaDB (vector database)

### Step 6: Install Ollama (AI Backend)

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Start Ollama service:

```bash
# Systemd service (auto-start on boot)
sudo systemctl enable ollama
sudo systemctl start ollama

# Or run manually
ollama serve
```

Verify Ollama is running:

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

---

## 🤖 Method 2: Automated Installation

For a fully automated setup:

```bash
git clone https://github.com/smileformylove/MemScreen.git && cd MemScreen
./setup/install/install.sh
```

This script handles:
- ✅ Python version check
- ✅ Virtual environment creation
- ✅ Dependency installation
- ✅ Ollama installation
- ✅ AI model download
- ✅ Configuration file creation

---

## 🐳 Method 3: Docker Installation

For containerized deployment:

```bash
cd setup/docker
docker-compose up --build
```

See [Docker Guide](DOCKER_TEST.md) for details.

---

## 🔧 Common Issues on Linux

### Issue 1: "ModuleNotFoundError: No module named 'cv2'"

**Solution**: Install OpenCV dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install libopencv-dev python3-opencv

# Or reinstall in venv
pip uninstall opencv-python opencv-contrib-python
pip install opencv-python opencv-contrib-python
```

### Issue 2: "Kivy window fails to open"

**Solution**: Install SDL2 and GL libraries:

```bash
# Ubuntu/Debian
sudo apt-get install libsdl2-2.0-0 libgl1-mesa-glx libglib2.0-0

# Fedora
sudo dnf install SDL2 mesa-libGL glib2

# Arch Linux
sudo pacman -S sdl2 mesa glib2
```

### Issue 3: "Audio recording not working"

**Solution**: Install PulseAudio/PortAudio:

```bash
# Ubuntu/Debian
sudo apt-get install libportaudio2 libpulse-dev pulseaudio

# Fedora
sudo dnf install portaudio pulseaudio pulseaudio-libs

# Start PulseAudio
pulseaudio --check || pulseaudio -D
```

### Issue 4: "Screen capture permission denied"

**Solution**: Add user to appropriate groups:

```bash
# For screen recording (Ubuntu/Debian)
sudo usermod -a -G video $USER
sudo usermod -a -G render $USER

# Log out and log back in for changes to take effect
```

### Issue 5: "Wayland compatibility issues"

**Solution**: Run with XWayland or switch to X11:

```bash
# Option A: Force XWayland
export GDK_BACKEND=x11
python setup/start.py

# Option B: Switch to X11 session
# Log out, select X11 session from login screen
```

### Issue 6: "Ollama fails to start"

**Solution**: Check Ollama service:

```bash
# Check status
sudo systemctl status ollama

# View logs
sudo journalctl -u ollama -n 50

# Restart service
sudo systemctl restart ollama

# Or run manually
ollama serve
```

---

## 📱 Linux-Specific Features

### Screen Recording

MemScreen on Linux supports:
- **Full screen recording**
- **Window-specific recording**
- **Custom region recording**

### Display Server Support

**X11**: Full support for all features

**Wayland**: Limited support
- Use XWayland for best compatibility
- Some features may require additional permissions

### Keyboard Shortcuts

- `Ctrl+R`: Start/Stop Recording
- `Ctrl+Shift+R`: Select Region
- `Ctrl+Q`: Quit

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

# Remove Ollama
sudo systemctl stop ollama
sudo systemctl disable ollama
curl -fsSL https://ollama.com/install.sh | sh  # Run again, select uninstall

# Remove user data (optional)
rm -rf ~/.memscreen

# Remove system dependencies (optional)
# Ubuntu/Debian
sudo apt-get remove libopencv-dev python3-opencv
```

---

## 📚 Distribution-Specific Notes

### Ubuntu 22.04+

```bash
# Python 3.10 comes preinstalled
# Just install dependencies
sudo apt-get install python3-pip python3-venv
```

### Debian 12 (Bookworm)

```bash
# Use newer Python from backports if needed
sudo apt-get install python3.11 python3.11-venv
```

### Fedora 39+

```bash
# Python 3.12 comes preinstalled
sudo dnf install python3-pip gcc gcc-c++
```

### Arch Linux

```bash
# Rolling release, always has latest Python
sudo pacman -S python python-pip base-devel
```

---

## ✅ Installation Checklist

- [ ] System dependencies installed
- [ ] Python 3.8+ installed
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Python dependencies installed
- [ ] Ollama installed and running
- [ ] AI models downloaded (or ready to auto-download)
- [ ] Screen recording permissions granted
- [ ] MemScreen launches successfully

**All checked? You're ready to go!** 🎉

---

## 📚 Next Steps

1. **Read User Guide**: [USER_GUIDE.md](../USER_GUIDE.md)
2. **Configure Hotkeys**: Set up custom keyboard shortcuts
3. **Start Recording**: Try your first screen recording
4. **Explore AI Features**: Chat with your screen history

---

## 🆘 Getting Help

### Linux-Specific Resources

- 📖 [Kivy Linux Guide](https://kivy.org/doc/stable/installation/installation-linux.html)
- 🔧 [Ollama Linux](https://ollama.com/download/linux)
- 📹 [Linux Screen Recording](https://trac.ffmpeg.org/wiki/Capture/Desktop)

### Community Support

- 🐛 [Report Linux Issues](https://github.com/smileformylove/MemScreen/issues)
- 💬 [Linux Discussion](https://github.com/smileformylove/MemScreen/discussions)
- 📧 [Email Support](mailto:jixiangluo85@gmail.com)

---

**Enjoy using MemScreen on Linux!** 🐧
