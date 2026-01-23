# MemScreen Unified UI

A modern, beautiful interface that brings all MemScreen features together.

## 🎨 Design Philosophy

The Unified UI follows modern design principles:
- **Clean & Minimal**: Reduce clutter, focus on content
- **Intuitive Navigation**: Tab-based interface for easy access
- **Visual Hierarchy**: Clear typography and color scheme
- **Responsive Layout**: Adapts to different screen sizes
- **Purple Gradient Theme**: Modern, professional appearance

## 🚀 Quick Start

```bash
# Launch the unified interface
memscreen-ui
```

## 📱 Interface Overview

### Header Bar
- **Logo & Title**: MemScreen branding
- **Status Indicator**: Shows connection status to Ollama
- **Purple Gradient Background**: Eye-catching header

### Navigation Tabs

#### 💬 Chat Tab
- **Model Selector**: Choose from available Ollama models
- **Refresh Button**: Reload model list
- **Chat History**: View conversation with AI
- **Input Area**: Type your questions
- **Send Button**: Send messages (or press Enter)

**Features:**
- Real-time streaming responses
- Screen memory context integration
- Beautiful chat bubbles
- Typing indicator

#### 🎬 Videos Tab
- **Video List**: Browse all recordings
- **Video Player**: Play recordings with controls
- **Timeline Scrubber**: Navigate through video
- **Video Info**: Display file details
- **Playback Controls**: Play, pause, stop

**Features:**
- Thumbnail previews
- Time display
- Delete functionality
- Full-screen capable

#### 🔍 Search Tab
- **Search Bar**: Enter search queries
- **Results Display**: View matching content
- **Context Snippets**: See relevant portions

**Features:**
- Semantic search
- OCR text search
- Ranked results
- Quick navigation

#### ⚙️ Settings Tab
- **AI Models**: View configured models
- **Storage**: Database location
- **Appearance**: Theme information
- **Statistics**: Usage metrics

## 🎨 Color Scheme

```python
Primary: #667eea (Purple)
Primary Dark: #5a67d8
Secondary: #764ba2 (Deep Purple)
Accent: #f093fb (Pink)
Background: #f7fafc (Light Gray)
Surface: #ffffff (White)
Text: #2d3748 (Dark Gray)
```

## 📝 Typography

```python
Title: Segoe UI, 24pt, Bold
Heading: Segoe UI, 16pt, Bold
Body: Segoe UI, 11pt
Small: Segoe UI, 9pt
Code: Consolas, 10pt
```

## 🔧 Customization

### Change Theme
The UI uses ttkthemes with the "arc" theme. You can modify this in `unified_ui.py`:

```python
root = ThemedTk(theme="arc")  # Options: arc, adapt, etc.
```

### Adjust Colors
Modify the `COLORS` dictionary in `unified_ui.py`:

```python
COLORS = {
    "primary": "#667eea",
    "secondary": "#764ba2",
    # ... more colors
}
```

### Change Fonts
Update the `FONTS` dictionary:

```python
FONTS = {
    "title": ("Segoe UI", 24, "bold"),
    "body": ("Segoe UI", 11),
    # ... more fonts
}
```

## 💡 Tips & Tricks

1. **Keyboard Shortcuts**:
   - `Enter`: Send message in chat
   - `Ctrl+Enter`: New line in chat

2. **Video Playback**:
   - Click and drag timeline to scrub
   - Use play/pause button for control

3. **Search**:
   - Use natural language queries
   - Results are ranked by relevance

4. **Navigation**:
   - Click tabs to switch views
   - Active tab is highlighted

## 🐛 Troubleshooting

### UI doesn't launch
- Check Python dependencies: `pip install ttkthemes`
- Verify tkinter is installed

### Chat not working
- Ensure Ollama is running: `ollama serve`
- Check model is downloaded: `ollama list`

### Videos not playing
- Verify video files exist in `db/videos/`
- Check database: `db/screen_capture.db`

## 🔄 Comparing Interfaces

| Feature | Unified UI | Individual Commands |
|---------|------------|---------------------|
| Chat | ✅ Integrated | ✅ `memscreen-chat` |
| Videos | ✅ Integrated | ✅ `memscreen-screenshots` |
| Search | ✅ Integrated | ❌ Separate |
| Settings | ✅ Integrated | ❌ N/A |
| Modern Design | ✅ Yes | ⚠️ Basic |
| Tab Navigation | ✅ Yes | ❌ No |

## 📸 Screenshots

### Main Interface
```
┌─────────────────────────────────────────────────────┐
│  🖥️ MemScreen                      ● Online        │
├─────────────────────────────────────────────────────┤
│  💬 Chat  🎬 Videos  🔍 Search  ⚙️ Settings        │
├─────────────────────────────────────────────────────┤
│                                                       │
│              [Current Tab Content]                   │
│                                                       │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### Chat Tab
```
┌─────────────────────────────────────────────────────┐
│ Model: qwen3:1.7b  [🔄 Refresh]                     │
├─────────────────────────────────────────────────────┤
│ You: What did I work on yesterday?                  │
│                                                       │
│ AI: Based on your screen history...                  │
│                                                       │
├─────────────────────────────────────────────────────┤
│ [Type your message...]              [Send ➤]        │
└─────────────────────────────────────────────────────┘
```

### Videos Tab
```
┌──────────────┬──────────────────────────────────────┐
│ 📹 Recordings│  [Video Player Canvas]               │
│              │                                       │
│ [Refresh]    │                                       │
│ [Delete]     │                                       │
│              │                                       │
│ 2025-01-23   │  📁 video.mp4                         │
│ 15:30 - 5min │  ⏱️ 300s | 📊 25 MB                   │
│              │                                       │
│              │  [Timeline] 00:15 [▶️ Play]           │
└──────────────┴──────────────────────────────────────┘
```

## 🚀 Future Enhancements

- [ ] Dark mode toggle
- [ ] Custom themes
- [ ] Keyboard shortcut customization
- [ ] Export chat history
- [ ] Video editing capabilities
- [ ] Advanced search filters
- [ ] Statistics dashboard
- [ ] Plugin system

## 📞 Support

- GitHub Issues: https://github.com/smileformylove/MemScreen/issues
- Email: jixiangluo85@gmail.com

---

**Enjoy your beautiful screen memory experience!** 🎉
