"""
MemScreen Memory System - Backward Compatibility Module

This module provides backward compatibility imports for the refactored MemScreen memory system.
All classes have been moved to specialized modules for better organization.

**New Module Structure:**
- memscreen.llm - Language Model classes (BaseLlmConfig, LLMBase, OllamaLLM, etc.)
- memscreen.embeddings - Embedding classes (BaseEmbedderConfig, EmbeddingBase, OllamaEmbedding, etc.)
- memscreen.vector_store - Vector Store classes (VectorStoreFactory)
- memscreen.storage - Storage classes (SQLiteManager)
- memscreen.memory - Memory system (MemoryBase, Memory, MemoryConfig, etc.)

**Migration Guide:**
Old imports continue to work for backward compatibility:
    from memscreen.memory import Memory, OllamaLLM, SQLiteManager

New recommended imports:
    from memscreen.memory import Memory
    from memscreen.llm import OllamaLLM
    from memscreen.storage import SQLiteManager
"""

# Version info
from .version import __version__
__author__ = "Jixiang Luo"

# Import all classes from new modules for backward compatibility
from .llm import (
    BaseLlmConfig,
    LLMBase,
    OllamaLLM,
    OllamaConfig,
    LlmFactory,
    load_class,
)

from .embeddings import (
    BaseEmbedderConfig,
    EmbeddingBase,
    OllamaEmbedding,
    MockEmbeddings,
    EmbedderFactory,
)

from .vector_store import (
    VectorStoreFactory,
)

from .storage import (
    SQLiteManager,
)

from .memory import (
    MemoryBase,
    Memory,
    MemoryConfig,
    MemoryItem,
    MemoryType,
)

# Re-export for backward compatibility
__all__ = [
    # LLM classes
    "BaseLlmConfig",
    "LLMBase",
    "OllamaLLM",
    "OllamaConfig",
    "LlmFactory",
    "load_class",

    # Embedding classes
    "BaseEmbedderConfig",
    "EmbeddingBase",
    "OllamaEmbedding",
    "MockEmbeddings",
    "EmbedderFactory",

    # Vector Store classes
    "VectorStoreFactory",

    # Storage classes
    "SQLiteManager",

    # Memory classes
    "MemoryBase",
    "Memory",
    "MemoryConfig",
    "MemoryItem",
    "MemoryType",
]

# Deprecated imports - will be removed in version 3.0
import warnings

_DEPRECATED_MSG = """
Direct imports from memscreen.memory are deprecated. Please update your imports:

Old: from memscreen.memory import OllamaLLM
New: from memscreen.llm import OllamaLLM

Old: from memscreen.memory import OllamaEmbedding
New: from memscreen.embeddings import OllamaEmbedding

Old: from memscreen.memory import SQLiteManager
New: from memscreen.storage import SQLiteManager

This compatibility wrapper will be removed in MemScreen 1.0.0.
"""

# Show deprecation warning only once
_warning_shown = False


def _show_deprecation_warning():
    """Show deprecation warning once per session."""
    global _warning_shown
    if not _warning_shown:
        warnings.warn(
            _DEPRECATED_MSG,
            DeprecationWarning,
            stacklevel=3
        )
        _warning_shown = True


# Override __getattr__ to show warning for attribute access
def __getattr__(name):
    """Intercept attribute access to show deprecation warning."""
    if name in __all__:
        _show_deprecation_warning()
        return globals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
