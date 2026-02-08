# 📦 Installation Guide

Complete installation instructions for MemScreen across different platforms.

---

## 🚀 Quick Start (Source Code)

**Recommended for developers and users who want the latest features:**

```bash
# 1. Clone repository
git clone https://github.com/smileformylove/MemScreen.git && cd MemScreen

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e .

# 4. Launch 🚀
python setup/start.py
```

That's it! MemScreen will start and guide you through the initial setup.

---

## 📋 Platform-Specific Guides

Choose your platform for detailed installation instructions:

| Platform | Guide | Prerequisites |
|----------|-------|---------------|
| **macOS** | [INSTALL_MACOS.md](INSTALL_MACOS.md) | Python 3.8+, Homebrew (optional) |
| **Linux** | [INSTALL_LINUX.md](INSTALL_LINUX.md) | Python 3.8+, pip |
| **Windows** | [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md) | Python 3.8+, Git Bash |

---

## 🐋 Docker Installation

For containerized deployment, see [Docker Guide](DOCKER_TEST.md).

```bash
cd setup/docker
docker-compose up
```

---

## 📦 Automated Installation (Optional)

If you prefer fully automated setup:

```bash
./setup/install/install.sh
```

This script handles:
- ✅ Python version check
- ✅ Virtual environment creation
- ✅ Dependency installation
- ✅ Ollama setup
- ✅ AI model download
- ✅ Configuration file creation

---

## 🔧 System Requirements

### Common Requirements (All Platforms)

- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Disk**: 10GB free space (for AI models)
- **Ollama**: Required for AI features (installed automatically)

### Platform-Specific

#### macOS
- macOS 10.15 (Catalina) or later
- Xcode Command Line Tools

#### Linux
- Ubuntu 20.04+ / Debian 11+ / Fedora 35+
- Screen recording support

#### Windows
- Windows 10/11
- Git Bash or WSL2

---

## 🤖 Ollama Setup

MemScreen uses Ollama for AI features. It will be installed automatically, but you can also install it manually:

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Verify installation
ollama list
```

### Download AI Models

MemScreen will download models on first use, or you can pre-download:

```bash
# Vision model (~3GB)
ollama pull qwen2.5vl:3b

# Embedding model (~500MB)
ollama pull mxbai-embed-large
```

---

## ✅ Verify Installation

After installation, verify everything is working:

```bash
# Check Python version
python --version  # Should be 3.8+

# Check Ollama
ollama list

# Check dependencies
pip list | grep -E "kivy|opencv|pyobjc"

# Run MemScreen
python setup/start.py
```

If MemScreen starts successfully and you see the floating ball (macOS) or main window, installation is complete! 🎉

---

## 🔧 Troubleshooting

### Issue: "Python 3.8+ required"

**Solution**: Install Python 3.8 or higher:
```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt-get install python3 python3-pip

# Windows
# Download from https://www.python.org/downloads/
```

### Issue: "Ollama not running"

**Solution**: Start Ollama service:
```bash
ollama serve
```

### Issue: "Kivy window not showing"

**Solution**: Check graphics drivers and SDL2 installation:
```bash
# Ubuntu/Debian
sudo apt-get install libsdl2-2.0-0

# macOS (usually works out of the box)
# Reinstall dependencies:
pip install -r requirements.txt --force-reinstall
```

### Issue: "Permission denied"

**Solution**: Make scripts executable:
```bash
chmod +x setup/install/*.sh
chmod +x setup/run.sh
```

---

## 📚 Next Steps

After successful installation:

1. **Read the User Guide**: [USER_GUIDE.md](../USER_GUIDE.md)
2. **Explore Features**: Check out [README.md](../../README.md)
3. **View Examples**: See `examples/` directory
4. **Join Community**: [Discussions](https://github.com/smileformylove/MemScreen/discussions)

---

## 🆘 Need Help?

- 📖 [Documentation](../../README.md)
- 🐛 [Report Issues](https://github.com/smileformylove/MemScreen/issues)
- 💬 [Community Discussion](https://github.com/smileformylove/MemScreen/discussions)
- 📧 [Email Support](mailto:jixiangluo85@gmail.com)

---

**Ready to start?** Jump to the [Quick Start](#-quick-start-source-code) section! 🚀
