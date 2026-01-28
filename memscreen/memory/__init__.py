### copyright 2025 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2025-11-09             ###
### license: MIT                 ###

"""
Memory module for storing, retrieving, and managing memories.

This module provides a comprehensive memory management system with support for:
- Semantic memory (facts and knowledge)
- Episodic memory (events and experiences)
- Procedural memory (skills and procedures)
- Vector-based similarity search
- History tracking
"""

# Import base classes
from .base import MemoryBase

# Import models and configurations
from .models import (
    MemoryItem,
    MemoryConfig,
    MemoryType,
    EmbedderConfig,
    LlmConfig,
    ChromaDbConfig,
    VectorStoreConfig,
)

# Import main Memory implementation
from .memory import Memory, _build_filters_and_metadata

# Import Memory Manager
from .manager import MemoryManager, get_memory_manager, reset_memory_manager

__all__ = [
    # Base classes
    "MemoryBase",
    # Models
    "MemoryItem",
    "MemoryConfig",
    "MemoryType",
    # Configuration models
    "EmbedderConfig",
    "LlmConfig",
    "ChromaDbConfig",
    "VectorStoreConfig",
    # Main implementation
    "Memory",
    # Memory Manager
    "MemoryManager",
    "get_memory_manager",
    "reset_memory_manager",
    # Helper functions
    "_build_filters_and_metadata",
]

# Backward compatibility: re-export classes that were previously in memory.py
# This allows existing imports like `from memscreen.memory import MemoryBase` to continue working
