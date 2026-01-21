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

### 🆚 MemScreen vs Commercial Solutions

| Aspect | **MemScreen** | **Waylight.ai** | **Limitless.ai** |
|--------|--------------|-----------------|------------------|
| **Privacy** | ✅ 100% Local | ❌ Cloud-based | ❌ Cloud-based |
| **Data Control** | ✅ You own your data | ❌ Data sent to servers | ❌ Data sent to servers |
| **Cost** | ✅ Free Forever | ❌ Paid subscription | ❌ Paid subscription |
| **Customization** | ✅ Fully customizable | ❌ Limited | ❌ Limited |
| **Models** | ✅ Run any local model | ❌ Fixed cloud models | ❌ Fixed cloud models |
| **Internet Required** | ❌ Works offline | ✅ Always required | ✅ Always required |
| **Open Source** | ✅ MIT License | ❌ Proprietary | ❌ Proprietary |
| **Hardware Req** | ⚠️ Requires GPU/RAM | ✅ Any device | ✅ Any device |

### 💪 The Advantages

**Waylight.ai**: [https://www.waylight.ai/?ref=producthunt](https://www.waylight.ai/?ref=producthunt)
**Limitless.ai**: [https://www.limitless.ai/](https://www.limitless.ai/)

While these commercial solutions offer convenience and lower hardware requirements, **MemScreen** gives you:

- 🔒 **True Privacy** - Your data never leaves your machine
- 💰 **Zero Cost** - Free forever, no subscriptions
- 🎛️ **Total Control** - Customize models, features, and behavior
- 🚀 **Offline Capability** - Work anywhere, anytime
- 📖 **Open & Transparent** - Study, modify, and improve the code

</div>

---

## ⚡ Quick Start

Get up and running in **5 minutes**:

```bash
# 1. Clone and install
git clone https://github.com/smileformylove/MemScreen
cd MemScreen
pip install -r requirements.txt

# 2. Pull models (one-time setup)
ollama pull qwen3:1.7b
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large:latest

# 3. Start capturing your screen
python -W ignore memscreen.py

# 4. In another terminal, start chatting
python chat_ui.py
```

That's it! Start asking questions about your screen history. 🎉

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/smileformylove/MemScreen
cd MemScreen

# Install dependencies
pip install -r requirements.txt
```

### 🤖 Pull Models

```bash
ollama pull qwen3:1.7b
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large:latest
```

> 💡 **Pro Tip**: Want better performance? Download larger models for improved accuracy!

---

## 🎬 Usage

### 1️⃣ Capture Your Screen

```bash
python -W ignore memscreen.py
```

**Recording Features:**
- 🎥 Automatic video generation every minute
- 💾 Memory-efficient storage (auto-cleanup)
- 🔄 Continuous recording without manual intervention
- ⚡ Real-time OCR and memory analysis

**Command Line Options:**
```bash
# Basic recording (60s duration, 10min interval, 2s screenshot interval)
python -W ignore memscreen.py

# Custom settings
python -W ignore memscreen.py --duration 120 --interval 5 --screenshot-interval 1.0

# Continuous recording mode
python -W ignore memscreen.py --interval 0
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--interval` | 10 | Recording interval in minutes (0 = continuous) |
| `--duration` | 60 | Recording duration per session (seconds) |
| `--screenshot-interval` | 2.0 | Screenshot interval (seconds) |
| `--output` | ./db/videos | Video output directory |

---

### 2️⃣ Visualize Your Screen 📸

Browse through your captured screen history with an intuitive interface.

```bash
python screenshot_ui.py
```

**Features:**
- 🖼️ **Timeline View**: Navigate through all captured screens chronologically
- 🔍 **Instant Search**: Find any screen content instantly with keyword search
- 📊 **Smart Filtering**: Filter by date, app, or content type
- 💾 **Export Options**: Save screenshots or generate compilations
- 🎯 **Quick Actions**: Copy text, save image, or add notes with one click

<div align="center">

```
┌─────────────────────────────────────────────────────────┐
│  📅 Timeline  🔍 Search  🏷️ Filter  ⚙️ Settings         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ SCREEN  │  │ SCREEN  │  │ SCREEN  │  │ SCREEN  │   │
│  │  10:30  │  │  10:32  │  │  10:35  │  │  10:38  │   │
│  │  📝 VS  │  │  🌐 Web │  │  📧 Mail│  │  📝 Doc  │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
│                                                         │
│  [Selected Screen Preview - Click to Enlarge]          │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                 │   │
│  │              Full Screen Preview                │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  💬 "This is the article about React hooks..."         │
│  🏷️ Tags: #react #javascript #tutorial                 │
└─────────────────────────────────────────────────────────┘
```

</div>

> 📌 **Use Case**: "I need to find that tutorial I was reading yesterday afternoon about React hooks"
> → Open screenshot_ui.py → Search "React hooks" → Found in 3 clicks!

---

### 3️⃣ Chat with MemScreen 💬

Ask anything about your screen history in natural language.

```bash
python chat_ui.py
```

**Features:**
- 🤖 **Natural Conversations**: Ask questions like you would to a human
- 🔗 **Context-Aware**: Understands follow-up questions and references
- 📎 **Source Attribution**: Every answer shows the exact screen source
- 💡 **Proactive Insights**: Suggests related content you might have missed
- 🎯 **Multi-Modal**: Can reference screenshots, text, and patterns together

<div align="center">

```
┌─────────────────────────────────────────────────────────┐
│  💬 MemScreen Chat — Your Visual Memory Assistant       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  👤 You:                                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │ What was the API endpoint I used for the user    │   │
│  │ authentication in last week's project?          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  🤖 MemScreen:                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Based on your screen history, I found the API   │   │
│  │ endpoint you used:                               │   │
│  │                                                 │   │
│  │ 🔹 Endpoint: POST /api/v1/auth/login           │   │
│  │ 🔹 Location: auth_service.py line 47           │   │
│  │ 🔹 Last modified: 2025-01-15                   │   │
│  │                                                 │   │
│  │ [📸 Screenshot attached]                        │   │
│  │                                                 │   │
│  │ Would you like me to show the full function     │   │
│  │ implementation?                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  💡 Try: "Show me the code" | "When did I last        │
│     work on this?" | "Find similar patterns"          │
└─────────────────────────────────────────────────────────┘
```

</div>

> 📌 **Use Case Examples:**
> - "What was that error message I got last Thursday?"
> - "Show me all the design inspiration I collected for the dashboard project"
> - "When did I last work on the payment feature?"
> - "Find that article about optimization techniques"

---

## 🔬 Process Mining Analysis

Discover your work patterns and optimize productivity!

### What It Analyzes

- **Activity Frequency**: Most common keyboard and mouse actions
- **Frequent Sequences**: Common patterns of user interactions
- **Time Patterns**: Hourly and daily activity distributions
- **Workflow Discovery**: Directly-follows relationships and transition probabilities
- **Common Patterns**: Typing sessions, click patterns, keyboard shortcuts

### Quick Start

```bash
# Analyze all collected data
python memscreen.py --analyze

# Analyze specific time range
python memscreen.py --analyze --start-time "2025-01-01 00:00:00" --end-time "2025-01-02 00:00:00"

# Export to JSON
python memscreen.py --analyze --export-json process_mining_report.json
```

### Standalone Script

```bash
python process_mining.py --db ./db/screen_capture.db --start "2025-01-01T00:00:00" --end "2025-01-02T00:00:00" --output report.json
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
- 📧 [Email](mailto:support@example.com) - Direct support

---

<div align="center">

**⭐ Star us on GitHub to support the project!**

Made with ❤️ by the [MemScreen Team](https://github.com/smileformylove/MemScreen)

</div>
