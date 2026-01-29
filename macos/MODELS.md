# Model Integration Strategy for macOS App

## Why Aren't Models Bundled?

**Short Answer**: Models are too large (2.5GB+) and better managed separately.

### Detailed Reasons:

1. **Size Considerations**
   - qwen2.5vl:3b ≈ 2GB
   - mxbai-embed-large ≈ 470MB
   - Total: ~2.5GB
   - This would make every release download 2.5GB+ larger

2. **Ollama Design Philosophy**
   - Ollama is designed to manage models centrally
   - Models stored in `~/.ollama/models/`
   - All Ollama apps share the same model cache
   - Efficient model management and updates

3. **Flexibility**
   - Users can choose different model variants
   - Easy to update models without updating MemScreen
   - Can reuse models across multiple applications

4. **Updates**
   - Models are updated frequently by Ollama
   - Bundling would require app updates for model changes
   - Separate model management allows independent updates

## Current Implementation

### First-Run Model Download

**When does it happen?**
- First time user launches MemScreen.app
- Checks if models exist in Ollama
- Automatically downloads if missing

**User Experience:**
1. User opens MemScreen.app
2. App checks for Ollama → shows install dialog if missing
3. App checks for models → shows download dialog if missing
4. Background download starts
5. Progress shown in Terminal (transparent to user)
6. Notification appears when ready
7. User can close app and reopen when download completes

**Download Scripts:**
- Background download via Terminal
- Progress tracking
- Desktop notification when complete
- No blocking UI - users can continue using Mac

### Alternative: Complete Installer

For users who want everything installed at once:

```bash
# Run the complete installer
cd macos
chmod +x install_complete.sh
./install_complete.sh
```

This installs:
1. ✅ Ollama
2. ✅ AI models
3. ✅ Python dependencies
4. ✅ MemScreen

## Implementation Details

### Model Check Logic

```python
# In memscreen/memory/memory.py (on initialization)
import subprocess

def check_ollama_models():
    """Check if required models are installed"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )

        models = result.stdout

        has_vision = "qwen2.5vl:3b" in models
        has_embedding = "mxbai-embed-large" in models

        return {
            "ollama_installed": True,
            "has_vision_model": has_vision,
            "has_embedding_model": has_embedding,
            "needs_download": not (has_vision and has_embedding)
        }
    except:
        return {"ollama_installed": False, "needs_download": True}
```

### Download Progress Tracking

Models are downloaded in background Terminal with progress:
```
[1/2] Downloading qwen2.5vl:3b (~2GB)...
███████████████████████ 100%
✓ qwen2.5vl:3b downloaded (45s)

[2/2] Downloading mxbai-embed-large (~470MB)...
███████████████████████ 100%
✓ mxbai-embed-large downloaded (12s)
```

### User Notifications

Desktop notifications using `osascript`:
```bash
osascript -e 'display notification "MemScreen" with title "AI Models Ready!"'
```

## Future Enhancements

### Possible Improvements:

1. **In-App Progress Bar**
   - Show download progress in Kivy UI
   - Allow canceling downloads
   - Show current model being downloaded

2. **Model Selection**
   - Settings panel to choose models
   - Support for multiple model variants
   - Easy model switching

3. **Caching Strategy**
   - Cache downloaded models in app bundle
   - Check for model updates
   - Prompt before updating models

4. **Offline Mode**
   - Detect if models are available offline
   - Warn user before starting tasks requiring AI
   - Graceful degradation when models missing

## Build vs Download Decision Matrix

| Approach | Bundle Size | Download Time | Update Flexibility | Recommended |
|----------|-------------|---------------|-------------------|--------------|
| **No models (current)** | ~50MB | 2-3 min (one-time) | ⭐⭐⭐⭐⭐ | ✅ Yes |
| **Include models** | ~2.5GB | 10-20 min (one-time) | ⭐⭐ | ❌ No |
| **Hybrid (lightweight model)** | ~500MB | 5-10 min (one-time) | ⭐⭐⭐⭐ | ✅ Future |

## Current Recommendation

**Keep models separate** (current implementation):
- ✅ Smaller app bundle
- ✅ Faster downloads
- ✅ Shared models across apps
- ✅ Easier updates
- ✅ Better user experience

Users get:
- Quick app download and install
- Guided first-time setup
- Background model download
- Clear progress indication
- Desktop notification when ready
