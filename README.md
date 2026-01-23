<div align="center">

# 🖥️ MemScreen

**Ask Screen Anything** — Your AI-Powered Visual Memory System

[![GitHub Stars](https://img.shields.io/github/stars/smileformylove/MemScreen?style=social)](https://github.com/smileformylove/MemScreen/stargazers)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/ollama-supported-orange.svg)](https://ollama.com)

*Transform your screen into an intelligent memory that you can query anytime*

</div>

---

## ✨ What is MemScreen?

MemScreen (ASA — **Ask Screen Anything**) is your personal visual memory system. It captures, understands, and remembers everything on your screen using local AI models. All data stays on your machine — **100% privacy-focused**.

> Imagine having a photographic memory for your digital life. Need to find that article you skimmed yesterday? That code snippet from last week? That design inspiration from months ago? Just ask MemScreen.

---

## 🚀 Key Features

<div align="center">

| Feature | Description |
|---------|-------------|
| 📸 **Screen Capture** | Automatically capture and record your screen locally |
| 🧠 **AI Understanding** | Understands screen content with local MLLM & OCR models |
| 💬 **Visual Chat** | Ask questions about any screen content in natural language |
| 🔍 **Process Mining** | Analyze keyboard/mouse patterns to discover workflows |
| 🔒 **Privacy First** | All data and models stored locally on your machine |

</div>

### 🎯 What Can It Do?

- **Search Your Screen History**: "Show me the article about Python decorators I read yesterday"
- **Find Code Snippets**: "What was that function I wrote last Tuesday?"
- **Recall Designs**: "Find the UI mockup with the dark blue button"
- **Analyze Work Patterns**: Discover how you spend time and optimize your workflow

---

## 🔥 Why MemScreen?

<div align="center">

### 🆚 MemScreen vs Screen Recording & Analysis Tools

| Aspect | **MemScreen** | **OpenScreen** | **OBS Studio** | **Loom** | **CleanShot X** |
|--------|--------------|----------------|-----------------|----------|-----------------|
| **Privacy** | ✅ 100% Local | ✅ 100% Local | ✅ 100% Local | ❌ Cloud-based | ✅ Local |
| **Data Control** | ✅ You own your data | ✅ You own your data | ✅ You own your data | ❌ Data sent to servers | ✅ You own your data |
| **AI Understanding** | ✅ Local MLLM | ❌ No | ❌ No | ✅ Cloud AI | ❌ Only OCR |
| **Natural Language Query** | ✅ Chat with screen | ❌ No | ❌ No | ❌ Limited search | ❌ No |
| **Screen Search** | ✅ Semantic + OCR | ❌ No | ❌ No | ✅ Limited | ✅ OCR only |
| **Process Mining** | ✅ Mouse/Keyboard analysis | ❌ No | ❌ No | ❌ No | ❌ No |
| **Open Source** | ✅ MIT License | ✅ MIT License | ✅ GNU GPL v2 | ❌ Proprietary | ❌ Proprietary |
| **Cost** | ✅ Free  | ✅ Free | ✅ Free | ❌ $15-30+/mo | ❌ Paid |
| **Platform** | ✅ Cross-platform | ✅ Cross-platform | ✅ Cross-platform | ✅ Web/App | Mac only |

#### 📋 Detailed Tool Comparison

**AI-Powered Solutions:**

| Tool | Privacy | AI Features | Open Source | Cost | Key Strength |
|------|---------|-------------|-------------|------|---------------|
| **MemScreen** | ✅ 100% Local | MLLM, OCR, Process Mining | ✅ MIT | Free | Complete privacy + AI understanding |
| **Loom** | ❌ Cloud | Transcriptions, Summaries | ❌ No | $15-30+/mo | Team collaboration features |

**Privacy-First Screen Recorders:**

| Tool | Privacy | AI Features | Open Source | Cost | Key Strength |
|------|---------|-------------|-------------|------|---------------|
| **MemScreen** | ✅ 100% Local | ✅ MLLM + Process Mining | ✅ MIT | Free | AI-powered screen understanding |
| **OpenScreen** | ✅ 100% Local | ❌ No | ✅ MIT | Free | Simple, privacy-focused recording |
| **OBS Studio** | ✅ 100% Local | ❌ No | ✅ GPL v2 | Free | Professional streaming/recording |
| **Kap** | ✅ 100% Local | ❌ No | ✅ MIT | Free | Lightweight Mac recordings |
| **CleanShot X** | ✅ Local | ❌ OCR only | ❌ No | Paid | Professional screenshots + recording |
| **Snagit** | ✅ Local | ❌ No | ❌ No | Paid | Business documentation |
| **Shottr** | ✅ Local | ❌ OCR only | ❌ No | Free | Fast screenshots with OCR |
| **Raycast** | ✅ Local | ❌ No | ❌ No | Freemium | Integrated Mac productivity |

> 🌐 Explore more tools: [Product Hunt - Screenshots & Screen Recording](https://www.producthunt.com/categories/screenshots-and-screen-recording)

### 💪 The Unique Advantages of MemScreen

**Compared to Traditional Screen Recorders:**
- **OBS Studio**: [https://github.com/obsproject/obs-studio](https://github.com/obsproject/obs-studio) — Professional recording, but no AI understanding or search
- **Kap**: [https://getkap.co/](https://getkap.co/) — Simple and local, but just records, doesn't analyze
- **CleanShot X**: Powerful screenshots with OCR, but can't chat with your screen history

**Compared to AI-Powered Tools:**
- **Loom**: [https://www.loom.com/](https://www.loom.com/) — Cloud-based with AI, but your data leaves your device and costs money
- **Waylight.ai**: [https://www.waylight.ai/?ref=producthunt](https://www.waylight.ai/?ref=producthunt) — Cloud subscription, no data ownership
- **Limitless.ai**: [https://www.limitless.ai/](https://www.limitless.ai/) — Same privacy concerns, recurring cost

**What Makes MemScreen Different:**

- 🧠 **AI-Powered Visual Memory** — Not just recording, but understanding your screen
- 🔒 **True Privacy** — All AI runs locally, no data ever leaves your machine
- 💬 **Natural Language Interface** — Ask questions like "What was that API endpoint I used?"
- 📊 **Process Mining** — Discover your work patterns and optimize productivity
- 💰 **Zero Cost Forever** — No subscriptions, no hidden fees
- 🎛️ **Fully Customizable** — Swap models, modify behavior, extend features
- 📖 **Open Source** — Study, improve, and verify the code yourself

</div>

---

## ⚡ Quick Start

Get up and running in **5 minutes**:

```bash
# 1. Install via pip
pip install git+https://github.com/smileformylove/MemScreen.git

# 2. Pull AI models (one-time setup)
ollama pull qwen3:1.7b
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large:latest

# 3. Start capturing your screen
memscreen

# 4. In another terminal, start chatting
memscreen-chat
```

That's it! Start asking questions about your screen history. 🎉

---

## 📦 Installation

### 🍎 macOS Installation (Easiest)

#### Automated Installer

```bash
# Download and run the macOS installer
curl -fsSL https://raw.githubusercontent.com/smileformylove/MemScreen/main/macos/install.sh | bash
```

This script will:
- ✓ Install Python dependencies
- ✓ Install MemScreen
- ✓ Set up command-line shortcuts
- ✓ Download AI models
- ✓ Configure Ollama

#### Manual Installation

```bash
# 1. Install Ollama (required for AI features)
brew install ollama

# 2. Pull AI models
ollama pull qwen3:1.7b
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large:latest

# 3. Install MemScreen
pip install git+https://github.com/smileformylove/MemScreen.git

# 4. Launch MemScreen Unified UI (Recommended)
memscreen-ui

# Or launch individual components
memscreen
memscreen-chat
memscreen-screenshots
memscreen-process-mining
```

### 🎨 Introducing MemScreen Unified UI

The new **MemScreen Unified UI** brings all features together in one beautiful, modern interface:

- **💬 Chat Tab**: Talk to your screen memory with AI
- **🎬 Videos Tab**: Browse and play your screen recordings
- **🔍 Search Tab**: Search through your screen content
- **⚙️ Settings Tab**: Configure your MemScreen experience

Launch it with: `memscreen-ui`

### 🚀 Option 2: Install via pip (Cross-Platform)

```bash
# Install directly from GitHub
pip install git+https://github.com/smileformylove/MemScreen.git
```

### 🔧 Option 3: Install from Source

```bash
# Clone the repository
git clone https://github.com/smileformylove/MemScreen.git
cd MemScreen

# Install in development mode
pip install -e .
```

> 💡 **Pro Tip**: Want better performance? Download larger models for improved accuracy!

---

## 🎬 Usage

After installation, the following commands will be available:

| Command | Description |
|----------|-------------|
| `memscreen-ui` | **NEW**: Unified modern interface with all features |
| `memscreen` | Capture and record your screen |
| `memscreen-chat` | Chat with your screen history |
| `memscreen-screenshots` | Browse and search screenshots |
| `memscreen-process-mining` | Analyze keyboard/mouse patterns |

### 🌟 MemScreen Unified UI (Recommended)

Launch the beautiful, modern interface that integrates all MemScreen features:

```bash
memscreen-ui
```

**Features:**
- 🎨 **Modern Design**: Clean, intuitive interface with purple gradient theme
- 💬 **AI Chat**: Ask questions about your screen in natural language
- 🎬 **Video Browser**: Play and manage your screen recordings
- 🔍 **Smart Search**: Find content across all your recordings
- ⚙️ **Settings**: Configure models, storage, and appearance

**Tabs:**
1. **Chat**: Interact with your screen memory using AI
2. **Videos**: Browse, play, and delete recordings
3. **Search**: Search through your screen content
4. **Settings**: View and configure your MemScreen setup

### 1️⃣ Capture Your Screen

```bash
# Start screen recording with default settings
memscreen

# Custom settings
memscreen --duration 120 --interval 5 --screenshot-interval 1.0

# Continuous recording mode
memscreen --interval 0
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--interval` | 10 | Recording interval in minutes (0 = continuous) |
| `--duration` | 60 | Recording duration per session (seconds) |
| `--screenshot-interval` | 2.0 | Screenshot interval (seconds) |
| `--output` | ./db/videos | Video output directory |

**Recording Features:**
- 🎥 Automatic video generation every minute
- 💾 Memory-efficient storage (auto-cleanup)
- 🔄 Continuous recording without manual intervention
- ⚡ Real-time OCR and memory analysis

---

### 2️⃣ Visualize Your Screen 📸

Browse through your captured screen history with an intuitive interface.

```bash
memscreen-screenshots
```

**Features:**
- 🖼️ **Timeline View**: Navigate through all captured screens chronologically
- 🔍 **Instant Search**: Find any screen content instantly with keyword search
- 📊 **Smart Filtering**: Filter by date, app, or content type
- 💾 **Export Options**: Save screenshots or generate compilations
- 🎯 **Quick Actions**: Copy text, save image, or add notes with one click

> 📌 **Use Case**: "I need to find that tutorial I was reading yesterday afternoon about React hooks"
> → Open `memscreen-screenshots` → Search "React hooks" → Found in 3 clicks!

---

### 3️⃣ Chat with MemScreen 💬

Ask anything about your screen history in natural language.

```bash
memscreen-chat
```

**Features:**
- 🤖 **Natural Conversations**: Ask questions like you would to a human
- 🔗 **Context-Aware**: Understands follow-up questions and references
- 📎 **Source Attribution**: Every answer shows the exact screen source
- 💡 **Proactive Insights**: Suggests related content you might have missed
- 🎯 **Multi-Modal**: Can reference screenshots, text, and patterns together

> 📌 **Use Case Examples:**
> - "What was that error message I got last Thursday?"
> - "Show me all the design inspiration I collected for the dashboard project"
> - "When did I last work on the payment feature?"
> - "Find that article about optimization techniques"

---

### 4️⃣ Process Mining Analysis 📊

Discover your work patterns and optimize productivity!

```bash
# Analyze all collected data
memscreen --analyze

# Analyze specific time range
memscreen --analyze --start-time "2025-01-01 00:00:00" --end-time "2025-01-02 00:00:00"

# Export to JSON
memscreen --analyze --export-json process_mining_report.json
```

**What It Analyzes:**
- **Activity Frequency**: Most common keyboard and mouse actions
- **Frequent Sequences**: Common patterns of user interactions
- **Time Patterns**: Hourly and daily activity distributions
- **Workflow Discovery**: Directly-follows relationships and transition probabilities
- **Common Patterns**: Typing sessions, click patterns, keyboard shortcuts

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

## 📝 Citation

If you use MemScreen in your research, please cite:

```bibtex
@misc{memscreen,
  title={Memscreen: Ask Screen Anything with a visual memory screen},
  url={https://github.com/smileformylove/MemScreen},
}
```

---

## 🤝 Contributing

We welcome contributions from everyone! Here's how you can help:

- 🐛 **Report bugs** - Open an issue with details
- 💡 **Suggest features** - Share your ideas
- 📝 **Improve docs** - Fix typos or add examples
- 🔧 **Fix bugs** - Submit a pull request
- ✨ **Add features** - Build something cool

**Get Started:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🙏 Acknowledgments

- Inspired by [mem0](https://github.com/mem0ai/mem0) - Memory framework for AI
- **Related Tools**: [OpenScreen](https://github.com/siddharthvaddem/openscreen) - Privacy-focused screen recording
- Built with ❤️ for the open-source community
- Thanks to all contributors and users!

---

## 📜 License

This project is released under the **MIT License** — feel free to use, modify, and distribute!

---

## 📞 Support & Community

- 📖 [Documentation](https://github.com/smileformylove/MemScreen/wiki) - Detailed guides and API docs
- 🐛 [Issues](https://github.com/smileformylove/MemScreen/issues) - Bug reports and feature requests
- 💬 [Discussions](https://github.com/smileformylove/MemScreen/discussions) - Community discussions and Q&A
- 📧 [Email](mailto:jixiangluo85@gmail.com) - Direct support

---

<div align="center">

**⭐ Star us on GitHub to support the project!**

Made with ❤️ by the [MemScreen Team](https://github.com/smileformylove/MemScreen)

</div>
