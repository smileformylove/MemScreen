<div align="center">

# 🖥️ MemScreen

**Ask Screen Anything** — Your AI-Powered Visual Memory System

[![GitHub Stars](https://img.shields.io/github/stars/smileformylove/MemScreen?style=social)](https://github.com/smileformylove/MemScreen/stargazers)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/ollama-supported-orange.svg)](https://ollama.com)
[![Version](https://img.shields.io/badge/version-v0.3.5-brightgreen.svg)](https://github.com/smileformylove/MemScreen)

*Transform your screen into an intelligent memory that you can query anytime*

[⚡ Quick Start](#-quick-start) • [🎨 Demo](#-features) • [📖 Docs](#-documentation) • [🆚 Comparison](#-why-memscreen)

</div>

---

## ✨ What is MemScreen?

MemScreen is your **personal AI-powered visual memory system**. It captures, understands, and remembers everything on your screen using local AI models. All data stays on your machine — **100% privacy-focused**.

> **Imagine having a photographic memory for your digital life.** Need to find that article you skimmed yesterday? That code snippet from last week? That design inspiration from months ago? Just ask MemScreen.

**🎉 v0.3.5 Released — Timeline UI improvements!** Fixed timeline alignment and video marker positioning for better user experience.

---

## ⚡ Quick Start

Get up and running in **3 minutes**:

```bash
# 1️⃣ Clone the repository
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen

# 2️⃣ Install dependencies
pip install -r requirements.txt

# 3️⃣ Install Ollama & pull models
brew install ollama  # macOS
ollama pull qwen2.5vl:3b
ollama pull nomic-embed-text

# 4️⃣ Launch MemScreen
python start.py
```

That's it! Start recording, viewing, searching, and analyzing your screen. 🎉

---

## 🎨 Features

### 📱 Unified Interface

**🔴 Record**  •  **💬 AI Chat**  •  **🎬 Videos**  •  **📊 Process**  •  **⚙️ Settings**

| Feature | What It Does |
|---------|--------------|
| 🔴 **Record** | Real-time screen preview, continuous recording with auto-segmentation |
| 💬 **AI Chat** | Ask questions about your screen history in natural language |
| 🎬 **Videos** | Browse and play recordings with built-in video player |
| 📊 **Process Mining** | Track keyboard/mouse patterns, analyze workflows, get training recommendations |
| ⚙️ **Settings** | Configure AI models, storage, and view usage stats |

### 🚀 Key Capabilities

| Feature | Description |
|---------|-------------|
| 📸 **Screen Capture** | Automatically capture and record your screen locally |
| 🧠 **AI Understanding** | Understands screen content with local MLLM & OCR models |
| 💬 **Visual Chat** | Ask questions about any screen content in natural language |
| 🔍 **Semantic Search** | Find anything on your screen with AI-powered search |
| 📊 **Process Mining** | Analyze keyboard/mouse patterns to discover workflows |
| ⚡ **Live Event Display** | Real-time view of your keyboard/mouse events |
| 🔒 **Privacy First** | All data and models stored locally on your machine |

### What Can It Do?

- **"Show me the article about Python decorators I read yesterday"**
- **"What was that function I wrote last Tuesday?"**
- **"Find the UI mockup with the dark blue button"**
- **"When did I last work on the payment feature?"**
- **"Analyze my workflow patterns and suggest improvements"**

---

## 📦 Installation

### 🍎 macOS (Recommended)

```bash
# 1. Install Ollama (required for AI)
brew install ollama

# 2. Pull AI models (one-time)
ollama pull qwen2.5vl:3b
ollama pull nomic-embed-text

# 3. Clone and install
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
pip install -r requirements.txt

# 4. Launch MemScreen
python start.py
```

### 🐧 Linux / Windows

```bash
# 1. Install Ollama
# Visit: https://ollama.com

# 2. Pull AI models
ollama pull qwen2.5vl:3b
ollama pull nomic-embed-text

# 3. Clone and install
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
pip install -r requirements.txt

# 4. Launch MemScreen
python start.py
```

### 🔧 Requirements

- Python 3.8+
- Ollama (for local AI models)
- macOS/Linux/Windows

---

## 🎬 Usage

### 🌟 Launch the Application

```bash
python start.py
```

### 🔴 Recording

1. Navigate to the **Record** tab
2. Click **▶️ Start Recording**
3. Perform your work
4. Click **⏹️ Stop Recording** when done
5. Videos are automatically added to memory and can be searched

**Features:**
- Real-time screen preview
- Continuous recording with automatic segmentation
- Configurable segment duration (default: 60 seconds)
- OCR text extraction from video frames

### 💬 AI Chat

1. Navigate to the **AI Chat** tab
2. Select a model (default: qwen2.5vl:3b)
3. Ask questions in natural language:
   - "What text was on my screen earlier?"
   - "Show me the code I was working on"
   - "When did I last open the dashboard?"

**Features:**
- Semantic search through your screen history
- Context-aware responses
- Video content integration

### 📊 Process Mining (NEW!)

1. Navigate to the **Process** tab
2. Click **▶️ Start Tracking** to capture keyboard/mouse events
3. Watch the **live event feed** showing your actions in real-time:
   - ⌨️ Keyboard events (blue)
   - 🖱️ Mouse events (green)
4. Perform your usual work activities
5. Click **⏹️ Stop Tracking** when done
6. Select a time range and click **🔍 Analyze Workflow**
7. View patterns and training recommendations

**Analysis includes:**
- Activity frequency (most common actions)
- Frequent sequences (repeated patterns)
- Time patterns (typing sessions, shortcuts)
- Workflow patterns (action transitions)
- Training recommendations

### 🎬 Videos

1. Navigate to the **Videos** tab
2. Browse your recordings
3. Click **▶️ Play** to watch
4. Videos can be deleted from disk

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
│   (ChromaDB)        │
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

| Tool | Privacy | AI Features | Process Mining | Open Source | Cost |
|------|---------|-------------|----------------|-------------|------|
| **MemScreen** | ✅ 100% Local | ✅ MLLM + OCR | ✅ Yes | ✅ MIT | **Free** |
| **OBS Studio** | ✅ Local | ❌ No | ❌ No | ✅ GPL v2 | Free |
| **Loom** | ❌ Cloud | ✅ Cloud AI | ❌ No | ❌ No | $15-30/mo |
| **CleanShot X** | ✅ Local | ❌ OCR only | ❌ No | ❌ No | Paid |

### Unique Advantages

- 🧠 **AI-Powered Memory** — Not just recording, but **understanding** your screen
- 🔒 **True Privacy** — All AI runs locally, no data ever leaves your machine
- 💬 **Natural Language** — Ask questions like *"What was that API endpoint I used?"*
- 📊 **Process Mining** — Discover work patterns and optimize productivity (unique!)
- ⚡ **Live Event Tracking** — Real-time keyboard/mouse event display
- 💰 **Zero Cost Forever** — No subscriptions, no hidden fees
- 📖 **Open Source** — Study, improve, and verify the code yourself

---

## 🛠️ Tech Stack

- **GUI**: tkinter (modern, high-contrast design)
- **Screen Capture**: PIL ImageGrab
- **Video Processing**: OpenCV
- **Databases**: SQLite + ChromaDB (vector search)
- **AI Models**: Ollama (local MLLM & Embeddings)
- **OCR**: Ollama Vision API (qwen2.5vl:3b)
- **Input Tracking**: pynput
- **Language**: Python 3.8+

---

## 📝 What's New in v0.3

### ✨ New Features

- **📊 Process Mining Tab**
  - Real-time keyboard/mouse event tracking
  - Live event feed with color-coded display
  - Workflow pattern analysis
  - Training recommendations
  - Export to JSON

### 🐛 Bug Fixes

- Fixed AI chat hanging on second message
- Improved error handling
- Better memory integration
- Enhanced video processing

### 🔧 Improvements

- Merged search functionality into AI Chat tab
- Improved button visibility and layout
- Better text contrast for accessibility
- Continuous recording with user-specified intervals

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

- 🐛 [Issues](https://github.com/smileformylove/MemScreen/issues) — Bug reports and feature requests
- 💬 [Discussions](https://github.com/smileformylove/MemScreen/discussions) — Community discussions
- 📧 [Email](mailto:jixiangluo85@gmail.com) — Direct support

---

<div align="center">

**⭐ Star us on GitHub — it helps the project grow!**

Made with ❤️ by [MemScreen Team](https://github.com/smileformylove/MemScreen)

**v0.3** — Process Mining & Live Event Tracking

</div>
