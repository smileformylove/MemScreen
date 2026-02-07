### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                 ###

"""
Embeddings module for MemScreen.

This module provides embedding functionality for various providers including:
- Base embedding configuration and abstract classes
- Ollama embeddings
- Vision embeddings (SigLIP/CLIP)
- Mock embeddings for testing
- Factory for creating embedder instances
"""

from .base import BaseEmbedderConfig, EmbeddingBase
from .ollama import OllamaEmbedding
from .vision_encoder import VisionEncoder, VisionEncoderConfig
from .mock import MockEmbeddings
from .factory import EmbedderFactory

__all__ = [
    "BaseEmbedderConfig",
    "EmbeddingBase",
    "OllamaEmbedding",
    "VisionEncoder",
    "VisionEncoderConfig",
    "MockEmbeddings",
    "EmbedderFactory",
]
