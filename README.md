<div align="center">

  <!-- Main Logo -->
  <img src="assets/logo.png" alt="MemScreen Logo" width="280"/>

  # 🦉 MemScreen

  ### **AI-Powered Visual Memory. 100% Private.**

  <br/>

  [![Product Hunt](https://img.shields.io/badge/Product%20Hunt-Featured-orange?style=for-the-badge&logo=producthunt&logoColor=white&labelColor=FF6154)](https://www.producthunt.com/products/memscreen)
  [![ShipIt](https://img.shields.io/badge/ShipIt-Published-purple?style=for-the-badge&logoColor=white&labelColor=9B59B6)](https://www.shipit.buzz/products/memscreen)
  [![NXGenTools](https://img.shields.io/badge/NXGenTools-Published-blue?style=for-the-badge&logoColor=white&labelColor=4285F4)](https://www.nxgntools.com/tools/memscreen)
  [![100% Local](https://img.shields.io/badge/AI-100%25%20Local-success?style=for-the-badge&logoColor=white&labelColor=06D6A0)](https://github.com/smileformylove/MemScreen)
  [![No Cloud](https://img.shields.io/badge/Privacy-No%20Cloud-blue?style=for-the-badge&logoColor=white&labelColor=457B9D)](https://github.com/smileformylove/MemScreen)
  [![GitHub Stars](https://img.shields.io/github/stars/smileformylove/MemScreen?style=for-the-badge&logo=github&logoColor=white&labelColor=333&color=blue)](https://github.com/smileformylove/MemScreen/stargazers)
  [![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)](LICENSE)
  [![Python](https://img.shields.io/badge/python-3.8+-green?style=for-the-badge&logo=python&logoColor=white&labelColor=333)](https://www.python.org/downloads/)
  [![Ollama](https://img.shields.io/badge/ollama-supported-orange?style=for-the-badge)](https://ollama.com)
  [![vLLM](https://img.shields.io/badge/vLLM-supported-blue?style=for-the-badge)](https://docs.vllm.ai/)
  [![Version](https://img.shields.io/badge/version-v0.6.0-brightgreen?style=for-the-badge&labelColor=333)](https://github.com/smileformylove/MemScreen/releases/tag/v0.6.0)

  **100% Local • 100% Private • AI-Powered Visual Memory System**

  [⚡ Quick Start](#-quick-start) • [✨ Features](#-features) • [📖 Documentation](#-documentation)

</div>

---

## ✨ What is MemScreen?

**MemScreen** is your personal AI-powered visual memory system that captures, understands, and remembers everything on your screen — **100% locally, 100% privately**.

### 🚀 The Problem

> Ever forgotten something you saw on your screen?
> - "What was that article about Python decorators I read yesterday?"
> - "Where did I see that UI mockup with the dark blue button?"
> - "What was that function I wrote last Tuesday?"

### 💡 The Solution

**MemScreen** gives you a **photographic memory for your digital life**:

<table align="center">
<tr>
<td align="center" width="20%">

### 📸 Record

</td>
<td align="center" width="20%">

### 🤖 Understand

</td>
<td align="center" width="20%">

### 🔍 Search

</td>
<td align="center" width="20%">

### 💬 Ask

</td>
<td align="center" width="20%">

### 🔒 Private

</td>
</tr>
<tr>
<td align="center">

**Screen Recording**
<br/>
Capture continuously or on-demand

</td>
<td align="center">

**AI-Powered**
<br/>
Local vision models understand your screen

</td>
<td align="center">

**Semantic Search**
<br/>
Find anything by meaning, not keywords

</td>
<td align="center">

**Natural Language**
<br/>
Just ask like you would a person

</td>
<td align="center">

**100% Local**
<br/>
Everything runs on your machine

</td>
</tr>
</table>

<div align="center">

  **🎉 Featured on Product Hunt, ShipIt & NXGenTools!**

  **🎉 v0.6.0 — Floating Ball Mode & Brand New Experience!**

  ### 🚀 Core Features (v0.6.0)
  - 🔴 **Floating Ball First** — macOS starts with floating ball only, main window minimized
  - 🎨 **Branded Experience** — Floating ball displays your logo with circular masking
  - 🖱️ **Simplified Control** — All features accessible via right-click menu
  - 📱 **Cleaner Interface** — Drag anywhere, left-click to toggle window, right-click for menu

  ### 📦 What's Included
  - 🎯 **Custom Region Recording** — Select any area of your screen to record
  - 🤖 **Intelligent Agent** — Auto-classification & smart routing (3-5x faster)
  - 📊 **Dynamic Memory** — 15 categories for intelligent organization
  - 🔴 **Native Floating Ball** (macOS) — Real floating window for recording control

  ### ⚡ Advanced Optimizations (Phase 1-6)
  - 👁️ **Visual Encoder** — SigLIP/CLIP models for accurate visual search
  - 🔍 **Multimodal Search** — Text + Visual hybrid retrieval (30-50% better)
  - 📚 **Tiered Memory** — Working → Short-term → Long-term management
  - 🛡️ **Conflict Resolution** — Smart duplicate detection & merging
  - 🎬 **Multi-granular Vision** — Scene/Object/Text level understanding
  - 💬 **Visual QA Optimization** — Chain-of-thought for 7b models

  [View Full Changelog](https://github.com/smileformylove/MemScreen/compare/v0.5.0...v0.6.0) • [User Guide](docs/USER_GUIDE.md)

</div>

---

## ⚡ Quick Start

Get up and running in **3 minutes** — **no API keys, no cloud, no signup!**

### 📦 Option 1: Download Pre-built App (Easiest)

**For macOS users** - Download and run without installing dependencies!

```bash
# 1️⃣ Download the latest DMG from [Releases](https://github.com/smileformylove/MemScreen/releases)

# 2️⃣ Open DMG and drag MemScreen.app to Applications

# 3️⃣ Launch and grant permissions when prompted:
#     - Screen Recording (required)
#     - Accessibility (required for process tracking)
#     - Microphone (optional, for audio recording)
```

✅ **Pros:** No Python/dependencies installation, standalone app
📚 **See:** [Installation Guide](docs/INSTALLATION.md) for platform-specific instructions

---

### 🐳 Option 2: Docker (Recommended)

**Easiest way** - No dependencies to install!

```bash
# 1️⃣ Clone and start
git clone https://github.com/smileformylove/MemScreen.git && cd MemScreen
docker-compose -f setup/docker/docker-compose.yml up -d

# 2️⃣ Check logs
docker-compose -f setup/docker/docker-compose.yml logs -f memscreen
```

✅ **Pros:** Auto-installs everything, isolated environment
📚 **See:** [Docker Guide](docs/DOCKER.md) for advanced options

---

### 💻 Option 3: Local Installation

```bash
# 1️⃣ Install Ollama
brew install ollama  # macOS (visit ollama.com for Linux/Windows)

# 2️⃣ Download AI Models (one-time, ~3GB)
ollama pull qwen2.5vl:3b          # Vision model
ollama pull mxbai-embed-large     # Text embeddings

# 3️⃣ Install MemScreen
git clone https://github.com/smileformylove/MemScreen.git && cd MemScreen
pip install -r requirements.txt

# 4️⃣ Launch 🚀
python start.py
```

> **💡 Floating Ball Mode (macOS):**
> - On macOS, MemScreen starts with a **floating ball** in the top-right corner
> - The main window stays minimized - use the floating ball to control everything
> - **Right-click** the ball to access all features (Recording, Videos, AI Chat, etc.)
> - **Left-click** to show/hide the main window
> - **Drag** the ball to any position on screen

> **💡 Pro Tip:** Once models are downloaded, MemScreen works **completely offline**.

---

## ✨ Features

<div align="center">

  <img src="assets/logo_small.png" alt="Features" width="50"/>

  **Comprehensive Screen Memory System**

</div>

### 🎯 Screen Recording

- **🖥️ Full Screen & Custom Region** — Record everything or select specific areas
- **📐 Visual Guides** — Crosshair guides for precise region selection
- **⏱️ Flexible Intervals** — Set capture frequency (0.5s - 5s)
- **👁️ Live Preview** — See exactly what's being captured
- **🔴 Native Floating Ball** (macOS) — Real floating window with drag-and-drop control
  - **Cross-Space Visibility** — Stays visible across all desktop spaces
  - **Smart Interaction** — Left-click to show window, right-click for menu
  - **Recording Status** — Visual feedback (purple/red/yellow indicators)
  - **Draggable** — Move anywhere on screen

### 🤖 AI-Powered Understanding

- **🧠 Vision Intelligence** — Local MLLM (qwen2.5vl) understands your screen
- **📝 OCR Text Extraction** — Extract text from any screen content
- **🎨 Scene Recognition** — Identifies applications, activities, and UI elements
- **🔍 Semantic Search** — Find anything by meaning, not just keywords

### 🤖 Intelligent Agent (New!)

- **⚡ Auto Classification** — Recognizes 15 input types automatically
- **🎯 Intent Recognition** — Identifies 7 query intents for smart routing
- **🚀 3-5x Faster** — Category-based routing speeds up responses
- **💰 70% Fewer Tokens** — Targeted context retrieval

### 📊 Dynamic Memory System

- **🗂️ 15 Categories** — Intelligent memory organization
- **🔍 Smart Search** — Search only relevant categories
- **🎯 Context Optimization** — Retrieves the most relevant context
- **🌏 Multi-Language** — Chinese and English support

### 🔒 Privacy First

- **✅ 100% Local** — All AI processing on your machine
- **🚫 No Cloud** — No data sent to external servers
- **🔐 No API Keys** — Works out of the box
- **📖 Open Source** — Verify the code yourself

### 🚀 Advanced Optimizations (Phase 1-6)

> **30-50% better visual recall, 40-60% more accurate Q&A!**

- **👁️ Visual Encoder (SigLIP/CLIP)** — Native visual embeddings for accurate image search
- **🔍 Multimodal Search** — Hybrid text+visual retrieval with RRF fusion
- **📚 Tiered Memory** — Working → Short-term → Long-term automatic management
- **🛡️ Conflict Resolution** — Smart duplicate detection and automatic merging
- **🎬 Multi-granular Vision** — Scene/Object/Text level understanding
- **💬 Visual QA Optimization** — Chain-of-thought prompts for 7b models

📖 **See:** [Optimization Guide](docs/IMPLEMENTATION_SUMMARY.md) • [Integration Guide](docs/integration_guide.py)

---

## 🆚 Why MemScreen?

| Feature | MemScreen | OBS | Loom | CleanShot X |
|---------|-----------|-----|------|-------------|
| **Privacy** | ✅ **100% Local** | ✅ Local | ❌ Cloud | ✅ Local |
| **AI Understanding** | ✅ **Local MLLM** | ❌ No | ✅ Cloud AI | ❌ OCR only |
| **Semantic Search** | ✅ **Yes** | ❌ No | ❌ No | ❌ No |
| **Natural Language** | ✅ **Yes** | ❌ No | ❌ No | ❌ No |
| **Custom Region** | ✅ **Yes** | ✅ Yes | ❌ No | ✅ Yes |
| **Process Mining** | ✅ **Yes** | ❌ No | ❌ No | ❌ No |
| **Open Source** | ✅ **MIT** | ✅ GPL | ❌ No | ❌ No |
| **Cost** | **Free Forever** | Free | $15-30/mo | Paid |

---

## 🧠 AI Inference Backends

MemScreen supports **multiple local AI inference backends**:

| Backend | Setup | Hardware | Best For |
|---------|-------|----------|----------|
| **🦙 Ollama** | ⭐ Easy | CPU/GPU | Development, Mac users |
| **⚡ vLLM** | ⭐⭐ Medium | GPU (12GB+) | Production, throughput |
| **🚀 Step-3.5-Flash** | ⭐⭐⭐ Hard | 4x GPU (200GB+) | Complex reasoning |

### Quick Switch

```bash
# Use Ollama (default)
export MEMSCREEN_LLM_BACKEND=ollama

# Use vLLM
export MEMSCREEN_LLM_BACKEND=vllm
export MEMSCREEN_VLLM_URL=http://localhost:8000

# Use Step-3.5-Flash
export MEMSCREEN_LLM_BACKEND=vllm
export MEMSCREEN_VLLM_URL=http://localhost:8001
export MEMSCREEN_VLLM_LLM_MODEL=stepfun-ai/Step-3.5-Flash
```

📚 **See:** [vLLM Backend Guide](docs/VLLM_BACKEND.md) • [Step-3.5-Flash Guide](docs/STEP35FLASH.md)

---

## 📖 Documentation

**🚀 Getting Started:**
- [Installation Guide](docs/INSTALLATION.md) — Detailed setup instructions for all platforms
- [Docker Deployment](docs/DOCKER.md) — Containerized deployment guide
- [macOS Build Guide](docs/MACOS_BUILD_GUIDE.md) — Build for macOS
- [Ubuntu Installation Guide](docs/UBUNTU_INSTALLATION_GUIDE.md) — Linux setup
- [macOS Permission Guide](docs/MACOS_PERMISSION_GUIDE.md) — macOS permissions explained

**💡 User Guides:**
- [Accessibility Guide](docs/guides/ACCESSIBILITY.md) — Accessibility features setup
- [Process Mining Guide](docs/guides/PROCESS_MINING.md) — Track keyboard and mouse usage
- [Docker Test Guide](docs/guides/DOCKER_TEST.md) — Test Docker deployment
- [Recording Guide](docs/RECORDING_GUIDE.md) — Screen recording features
- [Audio Recording Guide](docs/AUDIO_RECORDING.md) — Audio capture setup
- [Floating Ball Guide](docs/FLOATING_BALL.md) — Native floating ball usage (macOS)

**🤖 AI Backend Configuration:**
- [vLLM Backend](docs/VLLM_BACKEND.md) — High-performance inference backend
- [vLLM Implementation Summary](docs/history/VLLM_IMPLEMENTATION_SUMMARY.md) — Implementation details

**🏗️ System Architecture:**
- [Architecture Overview](docs/ARCHITECTURE.md) — System design and components
- [Project Structure](docs/PROJECT_STRUCTURE.md) — Code organization
- [Intelligent Agent System](docs/INTELLIGENT_AGENT.md) — Auto-classification and smart dispatch
- [Dynamic Memory System](docs/DYNAMIC_MEMORY.md) — Categorized memory and search
- [Core API Documentation](docs/CORE_API.md) — API reference

**🔧 Development:**
- [Testing Guide](docs/TESTING_GUIDE.md) — How to test the system
- [Packaging Guide](docs/PACKAGING.md) — Package for distribution
- [Logo & Brand Guidelines](docs/LOGO_GUIDELINES.md) — Logo usage and branding

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **GUI Framework** | Kivy |
| **Screen Capture** | PIL ImageGrab |
| **Video Processing** | OpenCV |
| **Databases** | SQLite + ChromaDB |
| **AI Backends** | Ollama / vLLM |
| **Vision Models** | qwen2.5vl:3b / Qwen2-VL |
| **Advanced Reasoning** | Step-3.5-Flash (optional) |
| **Language** | Python 3.8+ |

---

## 📝 What's New

### ✨ v0.6.0 — Floating Ball Mode & UI Polish (February 2026)

- 🔴 **Floating Ball First** — macOS starts with floating ball, main window stays minimized
- 🎨 **Branded Experience** — Floating ball displays your logo with circular masking
- 🖱️ **Simplified Control** — All features accessible via right-click menu
- 📱 **Cleaner Interface** — Drag anywhere, left-click to toggle window, right-click for menu
- 🧹 **Code Cleanup** — Removed 15+ test/debug files, cleaned up project structure
- 📚 **Better Docs** — Added comprehensive user guide, updated README
- 🐛 **Bug Fixes** — Fixed duplicate floating ball issue, improved state management

### ✨ v0.5.0 — Dynamic Memory System & Native Floating Ball (February 2026)

- 🤖 **Intelligent Agent** — Auto-classification & smart routing (3-5x faster, 70% fewer tokens)
- 📊 **Dynamic Memory** — 15 categories, 7 query intents, smart search
- 🎯 **Custom Region Recording** — Visual crosshair guides, re-selectable regions
- 🔴 **Native Floating Ball** (macOS) — Real floating window with cross-space visibility
- 📁 **Improved Structure** — Centralized documentation in `docs/` directory

### ✨ v0.4.0 — Local AI Agent & Privacy-First Design

- 🤖 **Local AI Agent** — Task planning & skill execution
- 💬 **Enhanced AI Chat** — Humanized, warm responses
- 🔒 **Zero Cloud** — No API keys, no data transmission

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=smileformylove/MemScreen&type=Date)](https://star-history.com/#smileformylove/MemScreen&Date)

---

## 📁 Project Structure

```
MemScreen/
├── start.py                 # Application entry point
├── config_example.yaml      # Configuration template
│
├── memscreen/              # Main package
│   ├── ui/                # UI components (Kivy)
│   ├── presenters/        # Business logic (MVP)
│   ├── memory/            # Memory system
│   ├── llm/               # LLM integration
│   ├── audio/             # Audio recording
│   └── ...
│
├── tests/                 # Test files
├── examples/              # Demo scripts
└── docs/                  # Documentation
```

**User data** is stored in `~/.memscreen/`:
- Databases: `~/.memscreen/db/`
- Videos: `~/.memscreen/videos/`
- Logs: `~/.memscreen/logs/`

📖 **See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed documentation.**

---

## 🤝 Contributing

Contributions welcome! Here's how to help:

- 🐛 Report bugs via [Issues](https://github.com/smileformylove/MemScreen/issues)
- 💡 Suggest features via [Discussions](https://github.com/smileformylove/MemScreen/discussions)
- 📝 Improve documentation
- 🔧 Submit pull requests

---

## 📜 License

This project is released under the **MIT License** — free to use, modify, and distribute!

<div align="center">

  <img src="assets/logo_small.png" alt="MemScreen" width="80"/>

  **⭐ Star us on GitHub — it helps the project grow!**

  [![Star](https://img.shields.io/github/stars/smileformylove/MemScreen?style=social)](https://github.com/smileformylove/MemScreen/stargazers)

  **Featured on [Product Hunt](https://www.producthunt.com/products/memscreen), [ShipIt](https://www.shipit.buzz/products/memscreen) & [NXGenTools](https://www.nxgntools.com/tools/memscreen)**

  Made with ❤️ and 🦉 by [Jixiang Luo](https://github.com/smileformylove)

  **v0.6.0** — Floating Ball Mode & UI Polish (February 2026)

  [📧 Email](mailto:jixiangluo85@gmail.com) • [🐛 Report Bug](https://github.com/smileformylove/MemScreen/issues) • [💬 Discussion](https://github.com/smileformylove/MemScreen/discussions)

  ---

  **[🔝 Back to Top](#-memscreen)**

</div>
