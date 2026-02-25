"""
MemScreen - Ask Screen Anything with AI-Powered Visual Memory

A local, privacy-focused screen recording and analysis system that uses
computer vision and language models to understand and remember your screen content.

Version: v0.6.3

Architecture:
- MVP Pattern: Presenters handle business logic
- Memory System: ChromaDB + SQLite for vector and structured storage
- LLM Integration: Ollama for local AI inference
- UI: Flutter desktop frontend over FastAPI backend

Example:
    >>> from memscreen import Memory
    >>> memory = Memory(config=MemoryConfig(...))
    >>> memory.search("What did I just capture?")
"""

from .version import __version__
__author__ = "Jixiang Luo"
__email__ = "jixiangluo85@gmail.com"

__all__ = [
    "__version__",
    "__author__",
    "__email__",
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


def __getattr__(name):
    """
    Lazy exports to avoid importing heavy optional dependencies at package import time.
    This keeps lightweight runtime profiles (recording/process only) usable.
    """
    if name in {"Memory", "MemoryConfig", "MemoryItem", "MemoryType"}:
        from .memory import Memory, MemoryConfig, MemoryItem, MemoryType

        return {
            "Memory": Memory,
            "MemoryConfig": MemoryConfig,
            "MemoryItem": MemoryItem,
            "MemoryType": MemoryType,
        }[name]

    if name in {"LlmConfig", "EmbedderConfig", "VectorStoreConfig"}:
        from .memory.models import LlmConfig, EmbedderConfig, VectorStoreConfig

        return {
            "LlmConfig": LlmConfig,
            "EmbedderConfig": EmbedderConfig,
            "VectorStoreConfig": VectorStoreConfig,
        }[name]

    if name in {"OllamaLLM", "BaseLlmConfig"}:
        from .llm import OllamaLLM, BaseLlmConfig

        return {"OllamaLLM": OllamaLLM, "BaseLlmConfig": BaseLlmConfig}[name]

    if name == "OllamaEmbedding":
        from .embeddings import OllamaEmbedding

        return OllamaEmbedding

    if name == "VectorStoreFactory":
        from .vector_store import VectorStoreFactory

        return VectorStoreFactory

    if name == "SQLiteManager":
        from .storage import SQLiteManager

        return SQLiteManager

    raise AttributeError(f"module 'memscreen' has no attribute '{name}'")
