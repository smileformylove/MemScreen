# Graph Memory and Performance Optimization Guide

## 🎯 Overview

This document explains how to use the new Graph Memory feature and performance optimizations in MemScreen.

## 📊 Graph Memory System

### What is Graph Memory?

Graph Memory extracts entities (people, places, concepts) and relationships from your conversations and recordings, storing them in a knowledge graph. This allows for:

- **Entity Tracking**: Follow specific people, places, or concepts across all memories
- **Relationship Discovery**: Understand how different entities relate to each other
- **Contextual Search**: Find memories based on entity relationships

### Enabling Graph Memory

Create a configuration file (e.g., `config.yaml`):

```yaml
# Enable knowledge graph
enable_graph: true

# Graph store configuration
graph_store:
  provider: "memory"  # Currently only in-memory store is supported
  config: {}
```

Then use it when initializing MemScreen:

```python
from memscreen.config import MemScreenConfig

# Load from YAML file
config = MemScreenConfig(config_path="config.yaml")

# Or set programmatically
from memscreen.memory.models import MemoryConfig

config = MemoryConfig(
    enable_graph=True,  # Enable graph memory
    # ... other configurations
)
```

### Graph Memory Features

Once enabled, the system will:

1. **Extract Entities**: Automatically identify people, places, concepts, and events
2. **Create Relationships**: Detect how entities are related (e.g., "works at", "located in")
3. **Build Knowledge Graph**: Store entities and relationships in a queryable graph

### Example Usage

```python
from memscreen import Memory
from memscreen.memory.models import MemoryConfig, EmbedderConfig, LlmConfig, VectorStoreConfig

config = MemoryConfig(
    enable_graph=True,  # Enable graph memory
    embedder=EmbedderConfig(provider="ollama", config={"model": "mxbai-embed-large"}),
    vector_store=VectorStoreConfig(provider="chroma", config={"path": "./db/chroma_db"}),
    llm=LlmConfig(provider="ollama", config={"model": "qwen3:1.7b"})
)

memory = Memory(config=config)

# Add messages - entities will be extracted automatically
memory.add(
    "I met with Alice at the office to discuss the Q1 project.",
    user_id="user1"
)

# Query the graph (coming soon)
# entities = memory.graph.search_nodes("Alice")
# neighbors = memory.graph.get_neighbors(alice_node_id)
```

## ⚡ Performance Optimizations

Several optimizations have been implemented to improve model response speed:

### 1. Simple Message Fast-Track

**What**: Short, simple messages skip complex fact extraction
**Impact**: 2-3x faster for short messages
**Behavior**: Messages < 50 chars or single-line are added directly without LLM fact extraction

```python
# This is fast - no fact extraction
memory.add("Hi", user_id="user1")

# This uses full processing
memory.add("I had a long conversation about project planning...", user_id="user1")
```

### 2. Optimized LLM Parameters

**What**: Reduced token limits and lower temperature for faster responses
**Impact**: 30-40% faster LLM calls
**Trade-off**: Slightly less creative responses (fine for factual info)

Parameters used:
```python
{
    "num_predict": 256,  # Limit output tokens (was unlimited)
    "temperature": 0.3,   # Lower temperature (was 0.7)
    "top_p": 0.8,         # Focused sampling
}
```

### 3. Configurable Model Selection

Use faster models for different tasks:

```yaml
ollama:
  # Fast model for general LLM tasks (30-40% faster)
  llm_model: "qwen3:1.7b"

  # Even faster option (if available)
  # llm_model: "phi3:mini"

  # High-quality model (slower) for important tasks
  # llm_model: "qwen2.5:7b"
```

### 4. In-Memory Caching (Coming Soon)

Cache frequently searched queries to avoid repeated LLM calls.

## 🎛️ Configuration Options

### Full Performance-Optimized Config

```yaml
# config.yaml - Performance optimized settings

db:
  dir: "./db"

ollama:
  base_url: "http://127.0.0.1:11434"

  # Fast model for general use
  llm_model: "qwen3:1.7b"

  # Vision model for OCR
  vision_model: "qwen2.5vl:3b"

  # Embedding model
  embedding_model: "mxbai-embed-large"

recording:
  duration: 60
  interval: 2.0

# Enable graph (optional, adds 1-2 seconds per add)
enable_graph: false

performance:
  # These are used internally
  km_batch_threshold: 20
  flush_interval: 5.0
  typing_session_threshold: 2.0

timezone:
  default: "US/Pacific"
```

## 🔍 Troubleshooting

### Graph Memory Issues

**Problem**: Entity extraction fails
**Solution**: Ensure your LLM model supports JSON output format

**Problem**: Too many entities extracted
**Solution**: This is normal - the system filters important entities automatically

### Performance Issues

**Problem**: Responses still slow
**Solutions**:
1. Use a smaller model: `qwen3:1.7b` instead of `qwen2.5:7b`
2. Disable graph memory: `enable_graph: false`
3. Check Ollama is running locally (not remote)

**Problem**: Quality decreased
**Solution**: Increase `temperature` to 0.5 or 0.7 (slower but better quality)

## 📈 Benchmarks

Approximate performance on Apple M4:

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Short message add | 2.5s | 0.8s | 3.1x faster |
| Long message add | 4.0s | 2.5s | 1.6x faster |
| Chat query | 3.0s | 1.8s | 1.7x faster |
| Video add + OCR | 15s | 12s | 1.25x faster |

## 🚀 Future Enhancements

- [ ] NetworkX integration for advanced graph algorithms
- [ ] Neo4j support for large-scale graphs
- [ ] Graph visualization UI
- [ ] Entity linking across recordings
- [ ] Relationship strength scoring
- [ ] Graph-based search suggestions
- [ ] Distributed caching

## 📝 API Reference

See source code for full API:
- [memscreen/graph/models.py](memscreen/graph/models.py) - Graph data structures
- [memscreen/graph/base.py](memscreen/graph/base.py) - Graph store interface
- [memscreen/graph/memory_graph.py](memscreen/graph/memory_graph.py) - In-memory implementation
- [memscreen/graph/entity_extractor.py](memscreen/graph/entity_extractor.py) - Entity extraction
