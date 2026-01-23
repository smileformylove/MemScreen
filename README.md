<div align="center">

# 🖥️ MemScreen

**Ask Screen Anything** — Your AI-Powered Visual Memory System

[![GitHub Stars](https://img.shields.io/github/stars/smileformylove/MemScreen?style=social)](https://github.com/smileformylove/MemScreen/stargazers)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/ollama-supported-orange.svg)](https://ollama.com)

*Transform your screen into an intelligent memory that you can query anytime*

[⚡ Quick Start](#-quick-start) • [🎨 Demo](#-memscreen-unified-ui) • [📖 Docs](#-documentation) • [🆚 Comparison](#-why-memscreen)

</div>

---

## ✨ What is MemScreen?

MemScreen is your **personal AI-powered visual memory system**. It captures, understands, and remembers everything on your screen using local AI models. All data stays on your machine — **100% privacy-focused**.

> **Imagine having a photographic memory for your digital life.** Need to find that article you skimmed yesterday? That code snippet from last week? That design inspiration from months ago? Just ask MemScreen.

---

## ⚡ Quick Start

Get up and running in **3 minutes**:

```bash
# 1️⃣ Install (macOS - one command)
curl -fsSL https://raw.githubusercontent.com/smileformylove/MemScreen/main/macos/install.sh | bash

# 2️⃣ Or install via pip (cross-platform)
pip install git+https://github.com/smileformylove/MemScreen.git

# 3️⃣ Launch the Unified UI
memscreen-ui
```

That's it! Start recording, viewing, searching, and chatting with your screen. 🎉

---

## 🎨 MemScreen Unified UI

**NEW**: One beautiful interface for everything — [memscreen/unified_ui.py](memscreen/unified_ui.py) (1400+ lines)

<div align="center">

**🔴 Record**  •  **💬 Chat**  •  **🎬 Videos**  •  **🔍 Search**  •  **⚙️ Settings**

| Feature | What It Does |
|---------|--------------|
| 🔴 **Record** | Real-time screen preview, one-click recording with auto-save |
| 💬 **Chat** | Ask questions about your screen history in natural language |
| 🎬 **Videos** | Browse and play recordings with built-in video player |
| 🔍 **Search** | Semantic search + OCR to find anything on your screen |
| ⚙️ **Settings** | Configure AI models, storage, and view usage stats |

</div>

**Launch**: `memscreen-ui`

[→ Full Feature Documentation](FEATURE_COMPLETE.md) • [→ Testing Guide](TESTING_GUIDE.md)

---

## 🚀 Key Features

| Feature | Description |
|---------|-------------|
| 📸 **Screen Capture** | Automatically capture and record your screen locally |
| 🧠 **AI Understanding** | Understands screen content with local MLLM & OCR models |
| 💬 **Visual Chat** | Ask questions about any screen content in natural language |
| 🔍 **Process Mining** | Analyze keyboard/mouse patterns to discover workflows |
| 🔒 **Privacy First** | All data and models stored locally on your machine |

### What Can It Do?

- **"Show me the article about Python decorators I read yesterday"**
- **"What was that function I wrote last Tuesday?"**
- **"Find the UI mockup with the dark blue button"**
- **"When did I last work on the payment feature?"**

---

## 📦 Installation

### 🍎 macOS (Recommended - One Command)

```bash
curl -fsSL https://raw.githubusercontent.com/smileformylove/MemScreen/main/macos/install.sh | bash
```

This automated installer will:
- ✓ Install Python dependencies
- ✓ Install MemScreen package
- ✓ Set up command-line shortcuts
- ✓ Download AI models (Ollama)
- ✓ Configure everything for you

### 🐧 Cross-Platform (pip)

```bash
# 1. Install Ollama (required for AI)
brew install ollama  # macOS
# or visit: https://ollama.com

# 2. Pull AI models (one-time)
ollama pull qwen3:1.7b
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large:latest

# 3. Install MemScreen
pip install git+https://github.com/smileformylove/MemScreen.git

# 4. Launch the Unified UI
memscreen-ui
```

### 🔧 From Source

```bash
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
pip install -e .
```

> 💡 **Pro Tip**: The unified UI (`memscreen-ui`) is the easiest way to use all features!

---

## 🎬 Usage

### 🌟 Unified UI (Recommended)

```bash
memscreen-ui
```

Everything in one modern interface:
- 🔴 **Record Tab**: Real-time preview, one-click recording
- 💬 **Chat Tab**: Ask questions about your screen history
- 🎬 **Videos Tab**: Browse and play recordings
- 🔍 **Search Tab**: Find anything with semantic search
- ⚙️ **Settings Tab**: Configure models and storage

### Command Line Tools

| Command | Description |
|----------|-------------|
| `memscreen-ui` | **Unified UI** - All features in one interface |
| `memscreen` | Screen recording with customizable settings |
| `memscreen-chat` | Chat with your screen history |
| `memscreen-screenshots` | Browse and search screenshots |
| `memscreen-process-mining` | Analyze keyboard/mouse patterns |

**Example:**
```bash
# Record screen for 60 seconds
memscreen --duration 60 --interval 2.0

# Analyze work patterns
memscreen --analyze --export-json report.json
```

---

## 📊 Architecture

```
┌─────────────────┐
│   Your Screen   │
└────────┬────────┘
         │ Capture
         ▼
┌─────────────────┐
│  MemScreen Core │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬─────────┐
    ▼         ▼         ▼         ▼
┌──────┐ ┌─────────┐ ┌──────┐ ┌──────────┐
│ OCR  │ │  MLLM   │ │Embed │ │ Keyboard │
│ Engine│ │ Analysis│ │  ing │ │ & Mouse  │
└───┬──┘ └────┬────┘ └──┬───┘ └────┬─────┘
    │          │         │          │
    └──────────┴─────────┴──────────┘
              │
              ▼
┌─────────────────────┐
│   Vector Database   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Chat Interface     │
└─────────────────────┘
```

---

## 🆚 Why MemScreen?

### Compared to Screen Recorders

| Tool | Privacy | AI Features | Open Source | Cost |
|------|---------|-------------|-------------|------|
| **MemScreen** | ✅ 100% Local | ✅ MLLM + OCR + Process Mining | ✅ MIT | **Free** |
| **OBS Studio** | ✅ Local | ❌ No | ✅ GPL v2 | Free |
| **Loom** | ❌ Cloud | ✅ Cloud AI | ❌ No | $15-30/mo |
| **CleanShot X** | ✅ Local | ❌ OCR only | ❌ No | Paid |

### Unique Advantages

- 🧠 **AI-Powered Memory** — Not just recording, but **understanding** your screen
- 🔒 **True Privacy** — All AI runs locally, no data ever leaves your machine
- 💬 **Natural Language** — Ask questions like *"What was that API endpoint I used?"*
- 📊 **Process Mining** — Discover work patterns and optimize productivity
- 💰 **Zero Cost Forever** — No subscriptions, no hidden fees
- 📖 **Open Source** — Study, improve, and verify the code yourself

> 🌐 **Compare more tools**: [Product Hunt - Screenshots & Screen Recording](https://www.producthunt.com/categories/screenshots-and-screen-recording)

---

## 📚 Documentation

- **[FEATURE_COMPLETE.md](FEATURE_COMPLETE.md)** — Complete feature verification and usage guide
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** — Step-by-step testing workflow
- **[UI_OPTIMIZATION.md](UI_OPTIMIZATION.md)** — UI design and color scheme
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** — Project completion overview

---

## 🛠️ Tech Stack

- **GUI**: tkinter + ttkthemes (modern Arc theme)
- **Screen Capture**: PIL ImageGrab
- **Video Processing**: OpenCV
- **Databases**: SQLite + ChromaDB (vector search)
- **AI Models**: Ollama (local MLLM)
- **Language**: Python 3.8+

---

## 🤝 Contributing

Contributions welcome! Here's how to help:

- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🔧 Submit pull requests

**Get Started:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

This project is released under the **MIT License** — feel free to use, modify, and distribute!

---

## 📞 Support & Community

- 📖 [Documentation](FEATURE_COMPLETE.md) — Detailed guides and features
- 🐛 [Issues](https://github.com/smileformylove/MemScreen/issues) — Bug reports and feature requests
- 💬 [Discussions](https://github.com/smileformylove/MemScreen/discussions) — Community discussions
- 📧 [Email](mailto:jixiangluo85@gmail.com) — Direct support

---

<div align="center">

**⭐ Star us on GitHub — it helps the project grow!**

Made with ❤️ by [MemScreen Team](https://github.com/smileformylove/MemScreen)

</div>
