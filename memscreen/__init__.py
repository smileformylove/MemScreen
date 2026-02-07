"""
MemScreen - Ask Screen Anything with AI-Powered Visual Memory

A local, privacy-focused screen recording and analysis system that uses
computer vision and language models to understand and remember your screen content.

Version: v0.6.0

Architecture:
- MVP Pattern: Presenters handle business logic
- Memory System: ChromaDB + SQLite for vector and structured storage
- LLM Integration: Ollama for local AI inference
- UI: Kivy-based cross-platform interface with floating ball control

Example:
    >>> from memscreen import Memory
    >>> memory = Memory(config=MemoryConfig(...))
    >>> memory.search("What did I just capture?")
"""

__version__ = "0.6.0"
__author__ = "Jixiang Luo"
__email__ = "jixiangluo85@gmail.com"

# Main Memory system
from .memory import Memory, MemoryConfig, MemoryItem, MemoryType

# LLM providers
from .llm import OllamaLLM, BaseLlmConfig

# Import configs from memory.models
from .memory.models import LlmConfig, EmbedderConfig, VectorStoreConfig

# Embedding providers
from .embeddings import OllamaEmbedding

# Vector store
from .vector_store import VectorStoreFactory

# Storage
from .storage import SQLiteManager

__all__ = [
    "Memory",
    "MemoryConfig",
    "MemoryItem",
    "MemoryType",
    "OllamaLLM",
    "BaseLlmConfig",
    "LlmConfig",
    "OllamaEmbedding",
    "EmbedderConfig",
    "VectorStoreConfig",
    "VectorStoreFactory",
    "SQLiteManager",
]
