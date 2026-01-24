# 🚀 MemScreen Quick Start Guide

Get up and running with MemScreen in 3 minutes!

---

## Prerequisites

### Required
- **Python 3.8+**
- **Ollama** (for AI features)

### Optional
- **macOS** - automated installer available
- **Linux/Windows** - manual installation

---

## Installation

### Option 1: macOS (Easiest - One Command)

```bash
curl -fsSL https://raw.githubusercontent.com/smileformylove/MemScreen/main/macos/install.sh | bash
```

This will:
- ✅ Install Python dependencies
- ✅ Install MemScreen package
- ✅ Download AI models
- ✅ Configure everything

### Option 2: pip (Cross-Platform)

```bash
# 1. Install Ollama
# macOS/Linux:
brew install ollama

# Or download from: https://ollama.com

# 2. Start Ollama
ollama serve

# 3. Pull AI models (in another terminal)
ollama pull qwen3:1.7b
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large

# 4. Install MemScreen
pip install -e .
```

---

## Launch the Application

### Method 1: Unified UI (Recommended)

```bash
memscreen-ui
```

This opens the beautiful, modern interface with:
- 🔴 **Record** - Screen recording with real-time preview
- 💬 **Chat** - AI-powered memory assistant
- 🎬 **Videos** - Browse and play recordings
- 🔍 **Search** - Find anything with semantic search
- ⚙️ **Settings** - Configure models and storage

### Method 2: Command Line

```bash
# Record for 10 seconds
memscreen --duration 10

# Record with custom settings
memscreen --duration 60 --interval 2.0

# Analyze workflow patterns
memscreen --analyze
```

### Method 3: Individual Components

```bash
memscreen-chat              # Chat interface
memscreen-screenshots       # Screenshot browser
memscreen-process-mining    # Workflow analysis
```

---

## First Use

### Step 1: Launch the UI
```bash
memscreen-ui
```

### Step 2: Record Something
1. Click the **🔴 Record** tab (default)
2. Click **🔴 Start Recording**
3. Wait 10 seconds (do something on your screen)
4. Click **⏹️ Stop Recording**

### Step 3: View Your Recording
1. Click the **🎬 Videos** tab
2. Select your recording
3. Click **▶️ Play** to watch

### Step 4: Search Your Screen
1. Click the **🔍 Search** tab
2. Type what you're looking for
3. Click **Search**

### Step 5: Chat with Your Memory
1. Click the **💬 Chat** tab
2. Ask: "What did I just record?"
3. AI will describe your screen activity

---

## Configuration

### Default Settings

**Recording**:
- Duration: 60 seconds
- Interval: 2.0 seconds
- Output: `./db/videos/`

**AI Models**:
- LLM: `qwen3:1.7b`
- Vision: `qwen2.5vl:3b`
- Embedding: `mxbai-embed-large`

**Storage**:
- Database: `./db/screen_capture.db`
- Videos: `./db/videos/`
- Logs: `./db/logs/`

### Custom Configuration

Create `~/.memscreen_config.yaml`:

```yaml
ollama:
  base_url: http://127.0.0.1:11434
  llm_model: qwen3:1.7b
  vision_model: qwen2.5vl:3b
  embedding_model: mxbai-embed-large

recording:
  duration: 120
  interval: 1.0
  screenshot_interval: 2.0

db:
  dir: ./db
  name: screen_capture.db
```

Then run:
```bash
memscreen-ui --config ~/.memscreen_config.yaml
```

---

## Troubleshooting

### Issue: "Ollama not running"

**Solution**:
```bash
# Start Ollama
ollama serve

# In another terminal, verify
curl http://127.0.0.1:11434/api/tags
```

### Issue: "Models not found"

**Solution**:
```bash
ollama pull qwen3:1.7b
ollama pull qwen2.5vl:3b
ollama pull mxbai-embed-large
```

### Issue: "UI doesn't open"

**Solution**:
```bash
# Check installation
python3 -c "from memscreen.ui import MemScreenApp; print('OK')"

# Reinstall if needed
pip install -e . --force-reinstall
```

### Issue: "Recording not working"

**Solution**:
- Check permissions on `./db/videos/`
- Ensure enough disk space
- Try shorter duration first

---

## Tips & Tricks

### Better Quality Recordings
```bash
# Higher frame rate (larger files)
memscreen --duration 30 --screenshot-interval 0.5

# Lower frame rate (smaller files)
memscreen --duration 120 --screenshot-interval 5.0
```

### Quick Recording
```bash
# Record 10 seconds fast
memscreen --duration 10
```

### Long Recording
```bash
# Record 5 minutes
memscreen --duration 300 --interval 2.0
```

### Analyze Workflow
```bash
# See how you work
memscreen --analyze --export-json report.json
```

---

## Next Steps

1. **Explore the UI** - Try all 5 tabs
2. **Record your work** - Build your memory
3. **Search anything** - Find past work instantly
4. **Chat with memory** - Ask questions about your screen
5. **Analyze patterns** - Discover workflow insights

---

## Getting Help

- 📖 [Full Documentation](README.md)
- 🏗️ [Architecture Guide](ARCHITECTURE.md)
- 🧪 [Testing Results](TESTING_RESULTS.md)
- 📧 [Email Support](mailto:jixiangluo85@gmail.com)
- 🐛 [Report Issues](https://github.com/smileformylove/MemScreen/issues)

---

**Ready to transform your screen into intelligent memory?** 🚀

```bash
memscreen-ui
```
