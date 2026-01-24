"""
LLM (Large Language Model) module for MemScreen.

This module provides abstractions and implementations for various LLM providers.
Currently supports Ollama for local model inference.
"""

from .base import BaseLlmConfig, LLMBase
from .ollama import OllamaLLM, OllamaConfig
from .factory import LlmFactory, load_class

__all__ = [
    "BaseLlmConfig",
    "LLMBase",
    "OllamaLLM",
    "OllamaConfig",
    "LlmFactory",
    "load_class",
]
