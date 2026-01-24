# 🏗️ MemScreen Architecture Guide

## Overview

MemScreen has been refactored from a monolithic structure into a modern, modular architecture. This guide explains the new structure, how to use it, and how to extend it.

---

## 📦 Module Structure

```
memscreen/
├── config/              # Configuration management
├── llm/                 # Language Model providers
├── embeddings/          # Text embedding models
├── vector_store/        # Vector database abstraction
├── storage/             # Data persistence
├── memory/              # Memory system
├── ui/                  # User interface
│   ├── components/      # Reusable UI components
│   └── tabs/            # Individual tab implementations
├── chroma.py            # ChromaDB integration
├── prompts.py           # AI prompts
├── utils.py             # Utility functions
├── telemetry.py         # Analytics
├── memscreen.py         # Main recording module
├── chat_ui.py           # Chat interface
├── screenshot_ui.py     # Screenshot browser
├── process_mining.py    # Workflow analysis
├── memory.py            # Backward compatibility wrapper
└── unified_ui.py        # UI backward compatibility wrapper
```

---

## 🔧 Core Modules

### 1. Configuration (`memscreen/config`)

Centralized configuration system with validation and environment variable support.

**Usage**:
```python
from memscreen.config import get_config

# Load default configuration
config = get_config()

# Access configuration
db_path = config.db_path              # Path object
ollama_url = config.ollama_base_url   # str
model = config.ollama_llm_model      # str

# Load from file
config = get_config(config_path="~/memscreen_config.yaml")

# Environment variable overrides
# $ export MEMSCREEN_OLLAMA_URL=http://custom:11434
# $ export MEMSCREEN_LLM_MODEL=custom-model
```

**Features**:
- Single source of truth
- YAML/JSON file support
- Environment variable overrides
- Type-safe property access
- Validation

---

### 2. Language Models (`memscreen/llm`)

Abstractions for LLM providers with factory pattern.

**Usage**:
```python
from memscreen.llm import OllamaLLM, OllamaConfig, LlmFactory

# Direct instantiation
config = OllamaConfig(
    model="qwen3:1.7b",
    ollama_base_url="http://127.0.0.1:11434"
)
llm = OllamaLLM(config)

# Using factory
factory = LlmFactory()
llm = factory.create("ollama", config)

# Generate response
messages = [
    {"role": "user", "content": "Hello!"}
]
response = llm.generate_response(messages)
```

**Architecture**:
```
llm/
├── base.py          # BaseLlmConfig, LLMBase (abstract)
├── ollama.py        # Ollama implementation
└── factory.py       # LlmFactory for creating instances
```

---

### 3. Embeddings (`memscreen/embeddings`)

Text embedding generation for semantic search.

**Usage**:
```python
from memscreen.embeddings import OllamaEmbedding, EmbedderFactory

# Direct instantiation
embedder = OllamaEmbedding(config)
embedding = embedder.embed("Hello, world!")

# Using factory
factory = EmbedderFactory()
embedder = factory.create("ollama", config)

# Mock embeddings for testing
from memscreen.embeddings import MockEmbeddings
mock = MockEmbeddings()
embedding = mock.embed("test")  # Returns fixed vector
```

**Architecture**:
```
embeddings/
├── base.py          # BaseEmbedderConfig, EmbeddingBase
├── ollama.py        # Ollama embedding
├── mock.py          # Mock for testing
└── factory.py       # EmbedderFactory
```

---

### 4. Vector Store (`memscreen/vector_store`)

Abstraction layer for vector database operations.

**Usage**:
```python
from memscreen.vector_store import VectorStoreFactory

factory = VectorStoreFactory()
vector_store = factory.create("chroma", config)

# Add vectors
vector_store.add(
    documents=["doc1", "doc2"],
    embeddings=[[0.1, 0.2], [0.3, 0.4]],
    metadata=[{"id": 1}, {"id": 2}]
)

# Search
results = vector_store.search(
    query_embedding=[0.1, 0.2],
    top_k=5
)
```

**Architecture**:
```
vector_store/
├── factory.py       # VectorStoreFactory
└── (uses chroma.py for ChromaDB implementation)
```

---

### 5. Storage (`memscreen/storage`)

Database operations with thread-safe SQLite manager.

**Usage**:
```python
from memscreen.storage import SQLiteManager

# Initialize
db = SQLiteManager("./db/screen_capture.db")

# Add history
db.add_history(
    action="recording",
    details={"duration": 60, "frames": 30}
)

# Get history
history = db.get_history(limit=10)

# Cleanup
db.close()
```

**Features**:
- Thread-safe operations
- Automatic schema migration
- History tracking
- Connection management

**Architecture**:
```
storage/
├── sqlite.py        # SQLiteManager implementation
└── __init__.py      # Exports
```

---

### 6. Memory System (`memscreen/memory`)

Core memory management with AI-powered search.

**Usage**:
```python
from memscreen.memory import Memory, MemoryConfig
from memscreen.config import get_config

# Initialize
config = get_config()
memory = Memory.from_config(config.get_llm_config())

# Add memory
memory.add(
    messages="User asked about Python decorators",
    user_id="user1",
    metadata={"source": "chat", "timestamp": "2025-01-24"}
)

# Search
results = memory.search(
    query="What did user ask about Python?",
    user_id="user1"
)

# Get all memories
all_memories = memory.get_all(user_id="user1")

# Update
memory.update(
    memory_id="123",
    messages="Updated content"
)

# Delete
memory.delete(memory_id="123")
```

**Features**:
- Add, search, update, delete operations
- Semantic search + OCR
- Procedural memory generation
- History tracking
- Batch operations

**Architecture**:
```
memory/
├── base.py          # MemoryBase (abstract)
├── models.py        # Pydantic models (MemoryConfig, MemoryItem, MemoryType)
├── memory.py        # Memory implementation
└── __init__.py      # Exports
```

---

### 7. User Interface (`memscreen/ui`)

Modern, modular UI with separate components and tabs.

**Usage**:
```python
from memscreen.ui import MemScreenApp
import tkinter as tk

# Create main window
root = tk.Tk()
app = MemScreenApp(root)
root.mainloop()
```

**Architecture**:
```
ui/
├── app.py                    # Main MemScreenApp orchestration
├── components/
│   ├── colors.py            # Color scheme (19 colors + 5 fonts)
│   └── buttons.py           # ModernButton component
└── tabs/
    ├── base_tab.py          # BaseTab abstract class
    ├── recording_tab.py     # Screen recording (448 lines)
    ├── chat_tab.py          # AI chat (275 lines)
    ├── video_tab.py         # Video browser (334 lines)
    ├── search_tab.py        # Search (113 lines)
    └── settings_tab.py      # Settings (76 lines)
```

**UI Components**:
```python
# Colors
from memscreen.ui.components import COLORS
color = COLORS["primary"]  # "#4F46E5"

# Buttons
from memscreen.ui.components import ModernButton
btn = ModernButton(parent, text="Click Me", command=callback)

# Tabs
from memscreen.ui.tabs import RecordingTab, ChatTab
recording_tab = RecordingTab(parent, config)
recording_tab.create_ui()
```

---

## 🔄 Migration Guide

### Old vs New Imports

**Old (still works with deprecation warning)**:
```python
from memscreen.memory import Memory, OllamaLLM, SQLiteManager
from memscreen.unified_ui import MemScreenApp
```

**New (recommended)**:
```python
from memscreen.memory import Memory
from memscreen.llm import OllamaLLM
from memscreen.storage import SQLiteManager
from memscreen.ui import MemScreenApp
```

**Configuration**:
```python
# Old way - hardcoded
config = {
    "llm": {"provider": "ollama", "config": {...}},
    "mllm": {"provider": "ollama", "config": {...}}
}

# New way - centralized
from memscreen.config import get_config
config = get_config()
llm_config = config.get_llm_config()
```

---

## 🧪 Testing

### Unit Tests

```python
# Test LLM
from memscreen.llm import OllamaLLM, OllamaConfig

config = OllamaConfig(model="qwen3:1.7b")
llm = OllamaLLM(config)
messages = [{"role": "user", "content": "test"}]
response = llm.generate_response(messages)
assert response is not None

# Test Embeddings
from memscreen.embeddings import OllamaEmbedding

embedder = OllamaEmbedding(config)
embedding = embedder.embed("test text")
assert len(embedding) > 0

# Test Memory
from memscreen.memory import Memory

memory = Memory.from_config(config)
memory.add(messages="test memory", user_id="test")
results = memory.search("test", user_id="test")
assert len(results) > 0
```

### Integration Tests

```python
# Full workflow test
from memscreen.memory import Memory
from memscreen.config import get_config

config = get_config()
memory = Memory.from_config(config.get_llm_config())

# Add
memory.add(messages="Python decorators explanation", user_id="user1")

# Search
results = memory.search("What did I learn about Python?", user_id="user1")

# Verify
assert len(results) > 0
assert "Python" in results[0]["metadata"]["content"]
```

---

## 🔌 Extending the System

### Adding a New LLM Provider

```python
# 1. Create provider in llm/
# memscreen/llm/openai.py

from .base import LLMBase, BaseLlmConfig

class OpenAIConfig(BaseLlmConfig):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key

class OpenAILLM(LLMBase):
    def __init__(self, config: OpenAIConfig):
        super().__init__(config)

    def generate_response(self, messages, **kwargs):
        # Implementation
        pass

# 2. Register in factory
# memscreen/llm/factory.py

class LlmFactory:
    provider_to_class = {
        "ollama": ("OllamaLLM", OllamaConfig),
        "openai": ("OpenAILLM", OpenAIConfig),  # Add this
    }
```

### Adding a New UI Tab

```python
# 1. Create tab in tabs/
# memscreen/ui/tabs/custom_tab.py

from .base_tab import BaseTab

class CustomTab(BaseTab):
    def __init__(self, parent, config):
        super().__init__(parent, config)

    def create_ui(self):
        # Create your UI here
        pass

# 2. Register in tabs/__init__.py
from .custom_tab import CustomTab

__all__ = [..., "CustomTab"]

# 3. Add to app.py
from .tabs import CustomTab

# In create_main_content()
custom_tab = CustomTab(self.main_content, self.config)
custom_tab.create_ui()
```

---

## 📊 Performance Considerations

### Memory Usage

```python
# Large recordings
config = get_config()
config.recording_interval = 5.0  # Less frequent = smaller files

# Embedding cache
embedder = OllamaEmbedding(config)
# Cache embeddings to avoid recomputation
```

### Database Optimization

```python
# Use connection pooling
from memscreen.storage import SQLiteManager

db = SQLiteManager(db_path)
# Connection automatically managed
# Thread-safe by default
```

### Async Operations

```python
# Background recording
# Already threaded in recording_tab.py
def record_screen(self):
    thread = threading.Thread(target=self._record_in_background)
    thread.daemon = True
    thread.start()
```

---

## 🐛 Common Issues

### Issue 1: Ollama Connection Failed

**Solution**:
```bash
# Start Ollama
ollama serve

# Pull models
ollama pull qwen3:1.7b
ollama pull mxbai-embed-large
```

### Issue 2: Import Errors

**Solution**:
```python
# Use new import paths
# Old: from memscreen.memory import OllamaLLM
# New: from memscreen.llm import OllamaLLM
```

### Issue 3: Database Locked

**Solution**:
```python
# SQLiteManager is thread-safe
# Only one instance needed
db = SQLiteManager(db_path)
# Don't create multiple instances
```

---

## 📚 Further Reading

- **[REFACTORING_PLAN.md](REFACTORING_PLAN.md)** - Complete refactoring roadmap
- **[REFACTORING_COMPLETE.md](REFACTORING_COMPLETE.md)** - Progress report
- **[TESTING_RESULTS.md](TESTING_RESULTS.md)** - Test validation
- **[README.md](README.md)** - Project overview

---

## 🤝 Contributing

When contributing to MemScreen:

1. **Follow the modular structure**
   - New LLM providers → `llm/`
   - New embeddings → `embeddings/`
   - New UI components → `ui/components/`

2. **Add type hints**
   ```python
   def my_function(param: str) -> bool:
       """Docstring."""
       return True
   ```

3. **Write tests**
   ```bash
   pytest tests/unit/test_llm.py -v
   ```

4. **Update documentation**
   - Add docstrings (Google style)
   - Update this guide if adding major features

---

**Last Updated**: 2025-01-24
**Architecture Version**: 2.0
**Status**: Production Ready ✅
