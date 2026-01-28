<div align="center">

  # 🖥️ MemScreen

  ### **Your AI-Powered Visual Memory System**

  [![GitHub Stars](https://img.shields.io/github/stars/smileformylove/MemScreen?style=for-the-badge&logo=github&logoColor=white&labelColor=333&color=blue)](https://github.com/smileformylove/MemScreen/stargazers)
  [![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0xMCAyMEgyMm0tOCAwaDgiLz48cGF0aCBkPSJNOSAxOWg2Ii8+PHBhdGggZD0iTTEwIDVoNG0tMiAwaDQiLz48L3N2Zz4=)](LICENSE)
  [![Python](https://img.shields.io/badge/python-3.8+-green?style=for-the-badge&logo=python&logoColor=white&labelColor=333)](https://www.python.org/downloads/)
  [![Ollama](https://img.shields.io/badge/ollama-supported-orange?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIj48cGF0aCBkPSJNMTIgMmwwIDdjMi42NyAwIDguMTYgMS4zNCA4IDl2MmMwIDUuNjItNS4zMyA4LTggOGwwLTd6Ii8+PC9zdmc+)](https://ollama.com)
  [![Version](https://img.shields.io/badge/version-v0.3.5-brightgreen?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIvPjxwYXRoIGQ9Ik0xMiA2djZsNCAzIi8+PC9zdmc+&labelColor=333)](https://github.com/smileformylove/MemScreen/releases/tag/v0.3.5)

  **Transform your screen into an intelligent memory that you can query anytime**

  [⚡ Quick Start](#-quick-start) • [🎨 Features](#-features) • [📖 Docs](#-documentation) • [🆚 Why MemScreen](#-why-memscreen)

  [![Demo](https://img.shields.io/badge/🎬-See%20Demo-purple?style=for-the-badge)](#features)

</div>

---

## ✨ What is MemScreen?

**MemScreen** is your personal AI-powered visual memory system. It captures, understands, and remembers everything on your screen using local AI models. All data stays on your machine — **100% privacy-focused**.

> **Imagine having a photographic memory for your digital life.**
> - Need to find that article you skimmed yesterday?
> - That code snippet from last week?
> - That design inspiration from months ago?
> - Just ask MemScreen.

<div align="center">

  **🎉 v0.3.5 Released — Timeline UI Improvements!**

  Fixed timeline marker alignment and enhanced visual layout for better user experience

  [View Changelog](https://github.com/smileformylove/MemScreen/compare/v0.3...v0.3.5)

</div>

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
brew install ollama        # macOS (visit ollama.com for Linux/Windows)
ollama pull qwen2.5vl:3b   # Vision-language model
ollama pull nomic-embed-text  # Text embedding model

# 4️⃣ Launch MemScreen
python start_kivy.py
```

That's it! 🎉 Start recording, viewing, and searching your screen.

---

## 🎨 Features

### 📱 Modern Kivy Interface

Experience a sleek, light-purple themed UI built with Kivy framework

<div align="center">

  **🔴 Recording**  •  **💬 AI Chat**  •  **🎬 Videos**  •  **📊 Process Mining**  •  **⚙️ About**

</div>

### 🚀 Core Capabilities

| Feature | Description |
|---------|-------------|
| 📸 **Screen Recording** | Real-time preview, continuous recording with configurable intervals |
| 🎬 **Video Player** | Built-in player with timeline navigation and playback controls |
| 🧠 **AI Understanding** | Local MLLM (qwen2.5vl) understands screen content visually |
| 💬 **Visual Chat** | Ask questions about your screen history in natural language |
| 🔍 **Semantic Search** | AI-powered vector search finds anything instantly |
| 📊 **Process Mining** | Track keyboard/mouse patterns and discover workflow insights |
| 🎯 **Timeline View** | Visual timeline with video markers for easy navigation |
| 🔒 **Privacy First** | All AI models and data stored locally on your machine |

### 💡 What Can It Do?

```
"Show me the article about Python decorators I read yesterday"
"What was that function I wrote last Tuesday?"
"Find the UI mockup with the dark blue button"
"When did I last work on the payment feature?"
"Analyze my workflow patterns and suggest improvements"
```

---

## 🎬 Interface Preview

### 🔴 Recording Tab

- **Live Screen Preview**: See exactly what's being captured
- **Flexible Recording**: Set duration (30s - 5min) and interval (0.5s - 5s)
- **Real-time Stats**: Track frame count and elapsed time
- **Auto-save**: Videos automatically saved and indexed

### 💬 AI Chat Tab

- **Natural Language Interface**: Just ask, MemScreen answers
- **Memory Integration**: Searches through your screen history automatically
- **Context-Aware**: Uses previous recordings to provide relevant answers
- **Multiple Models**: Switch between different AI models (qwen2.5vl, llama2, mistral)

### 🎬 Videos Tab

- **Timeline Navigation**: Visual timeline with clickable video markers
- **Smart Markers**: Purple dots show when videos were recorded
- **Play Position**: Orange indicator shows current playback position
- **Video Controls**: Play/pause, seek, progress bar with time display
- **Management**: View details and delete unwanted recordings

### 📊 Process Mining Tab

- **Live Event Feed**: Real-time display of keyboard/mouse events
- **Pattern Analysis**: Discover frequent actions and workflows
- **Training Recommendations**: Get AI-powered suggestions
- **Export**: Save event data to JSON for further analysis

---

## 📦 Installation

### 🍎 macOS (Recommended)

```bash
# Install Ollama (required for AI)
brew install ollama

# Pull AI models (one-time, ~2GB total)
ollama pull qwen2.5vl:3b
ollama pull nomic-embed-text

# Clone and install MemScreen
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
pip install -r requirements.txt

# Launch
python start_kivy.py
```

### 🐧 Linux / 🪟 Windows

```bash
# Install Ollama from https://ollama.com
# Pull AI models
ollama pull qwen2.5vl:3b
ollama pull nomic-embed-text

# Install Python dependencies
pip install -r requirements.txt

# Launch
python start_kivy.py
```

### 🔧 Requirements

- **Python**: 3.8 or higher
- **Ollama**: For local AI models
- **OS**: macOS, Linux, or Windows
- **Disk**: ~5GB for models + recordings

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────┐
│                 Your Screen                     │
└──────────────────┬──────────────────────────────┘
                   │ Screen Capture
                   ▼
┌─────────────────────────────────────────────────┐
│              MemScreen Core                     │
│  ┌──────────────────────────────────────────┐  │
│  │  🎥 Recording Module                     │  │
│  │  - Real-time screen capture              │  │
│  │  - Video encoding (OpenCV)               │  │
│  │  - Configurable intervals                │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │  🧠 AI & Memory Module                   │  │
│  │  - Ollama MLLM (qwen2.5vl)               │  │
│  │  - Text Embeddings (nomic-embed)         │  │
│  │  - ChromaDB Vector Store                 │  │
│  │  - SQLite Metadata DB                    │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │  📊 Process Mining Module                │  │
│  │  - Keyboard/Mouse tracking               │  │
│  │  - Pattern analysis                      │  │
│  │  - Workflow discovery                    │  │
│  └──────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│            Kivy UI Layer                        │
│  🔴 Recording  •  💬 Chat  •  🎬 Videos       │
│  📊 Process   •  ⚙️ Settings                  │
└─────────────────────────────────────────────────┘
```

---

## 🆚 Why MemScreen?

### Compared to Screen Recorders

| Feature | MemScreen | OBS | Loom | CleanShot X |
|---------|-----------|-----|------|-------------|
| **Privacy** | ✅ 100% Local | ✅ Local | ❌ Cloud | ✅ Local |
| **AI Understanding** | ✅ MLLM + OCR | ❌ No | ✅ Cloud | ❌ OCR only |
| **Process Mining** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Open Source** | ✅ MIT | ✅ GPL | ❌ No | ❌ No |
| **Cost** | **Free** | Free | $15-30/mo | Paid |
| **Natural Language** | ✅ Yes | ❌ No | ❌ No | ❌ No |

### Unique Advantages

- 🧠 **AI-Powered Memory** — Not just recording, but **understanding** your screen
- 🔒 **True Privacy** — All AI runs locally, no data ever leaves your machine
- 💬 **Natural Language** — Ask questions in plain English
- 📊 **Process Mining** — Discover work patterns (unique feature!)
- 🎯 **Timeline Navigation** — Visual timeline for easy video browsing
- 💰 **Zero Cost Forever** — No subscriptions, no hidden fees
- 📖 **Open Source** — Study, improve, and verify the code yourself

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **GUI Framework** | Kivy (cross-platform, modern UI) |
| **Screen Capture** | PIL ImageGrab |
| **Video Processing** | OpenCV |
| **Databases** | SQLite (metadata) + ChromaDB (vectors) |
| **AI Models** | Ollama (qwen2.5vl:3b, nomic-embed-text) |
| **Input Tracking** | pynput |
| **Language** | Python 3.8+ |

---

## 📝 What's New

### ✨ v0.3.5 — Timeline UI Improvements

- 🎯 **Fixed Timeline Alignment**: Video markers now perfectly align with timeline
- 📍 **Play Position Indicator**: Accurate position tracking with proper padding
- 🎨 **Visual Improvements**: Better spacing and layout
- 🐛 **Bug Fixes**: Resolved text overlap issues

### 🎉 v0.3 — Process Mining & Major Features

- 📊 Process Mining tab with workflow analysis
- 🎬 Video player with timeline navigation
- 💬 Enhanced AI chat with memory integration
- 🎨 Modern Kivy UI with light purple theme

---

## 🤝 Contributing

Contributions welcome! Here's how to help:

- 🐛 Report bugs via [Issues](https://github.com/smileformylove/MemScreen/issues)
- 💡 Suggest features via [Discussions](https://github.com/smileformylove/MemScreen/discussions)
- 📝 Improve documentation
- 🔧 Submit pull requests

**Development Setup:**
```bash
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen
pip install -r requirements.txt
python start_kivy.py
```

---

## 📜 License

This project is released under the **MIT License** — feel free to use, modify, and distribute!

<div align="center">

  **⭐ Star us on GitHub — it helps the project grow!**

  [![Star](https://img.shields.io/github/stars/smileformylove/MemScreen?style=social)](https://github.com/smileformylove/MemScreen)

  Made with ❤️ by [Jixiang Luo](https://github.com/smileformylove)

  **v0.3.5** — Timeline UI Improvements & Enhanced User Experience

  [📧 Email](mailto:jixiangluo85@gmail.com) • [🐛 Report Bug](https://github.com/smileformylove/MemScreen/issues) • [💬 Discussion](https://github.com/smileformylove/MemScreen/discussions)

</div>
