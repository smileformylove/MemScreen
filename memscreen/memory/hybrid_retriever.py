### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Hybrid Vision-Text Retriever for multimodal memory search.

This module implements a hybrid retrieval system that combines text and visual
embeddings for cross-modal search using Reciprocal Rank Fusion (RRF).
"""

import logging
from typing import Dict, List, Optional, Union, Literal
from pathlib import Path

from ..embeddings.base import EmbeddingBase
from ..embeddings.vision_encoder import VisionEncoder, VisionEncoderConfig
from ..vector_store.multimodal_chroma import MultimodalChromaDB
from ..vector_store.chroma import OutputData

logger = logging.getLogger(__name__)

__all__ = [
    "HybridVisionRetriever",
    "HybridRetrieverConfig",
]


class HybridRetrieverConfig:
    """
    Configuration for HybridVisionRetriever.

    Args:
        fusion_weight: Weight for text results (0-1), vision weight = 1 - fusion_weight
        text_limit: Number of text results to retrieve for fusion
        vision_limit: Number of vision results to retrieve for fusion
        rrf_k: RRF constant (higher = more lenient fusion)
        enable_query_rewriting: Whether to rewrite queries for better retrieval
        enable_caching: Whether to cache retrieval results
    """

    def __init__(
        self,
        fusion_weight: float = 0.6,
        text_limit: int = 20,
        vision_limit: int = 20,
        rrf_k: int = 60,
        enable_query_rewriting: bool = True,
        enable_caching: bool = True,
    ):
        self.fusion_weight = fusion_weight
        self.text_limit = text_limit
        self.vision_limit = vision_limit
        self.rrf_k = rrf_k
        self.enable_query_rewriting = enable_query_rewriting
        self.enable_caching = enable_caching


class HybridVisionRetriever:
    """
    Hybrid retriever combining text and visual search.

    This retriever supports three types of queries:
    1. Text-only: Searches using text embeddings
    2. Vision-only: Searches using visual embeddings (from image)
    3. Hybrid: Combines both text and visual queries with RRF fusion

    Example:
        ```python
        retriever = HybridVisionRetriever(
            text_embedder=ollama_embedder,
            vision_encoder=vision_encoder,
            vector_store=multimodal_store
        )

        # Text query
        results = retriever.retrieve("red button on screen")

        # Vision query
        results = retriever.retrieve(image_path="query.jpg")

        # Hybrid query
        results = retriever.retrieve(
            query="find similar",
            image_path="query.jpg"
        )
        ```
    """

    def __init__(
        self,
        text_embedder: EmbeddingBase,
        vision_encoder: VisionEncoder,
        vector_store: MultimodalChromaDB,
        config: Optional[HybridRetrieverConfig] = None,
    ):
        """
        Initialize the hybrid retriever.

        Args:
            text_embedder: Text embedding model
            vision_encoder: Vision encoder for images
            vector_store: Multimodal vector store
            config: Retriever configuration
        """
        self.text_embedder = text_embedder
        self.vision_encoder = vision_encoder
        self.vector_store = vector_store

        if config is None:
            config = HybridRetrieverConfig()

        self.config = config

        # Simple LRU cache for retrieval results
        self._cache = {} if config.enable_caching else None
        self._cache_order = [] if config.enable_caching else None

        logger.info(
            f"HybridVisionRetriever initialized "
            f"(fusion_weight={config.fusion_weight}, "
            f"text_limit={config.text_limit}, "
            f"vision_limit={config.vision_limit})"
        )

    def retrieve(
        self,
        query: Optional[str] = None,
        image_path: Optional[str] = None,
        filters: Optional[Dict] = None,
        limit: int = 10,
    ) -> List[OutputData]:
        """
        Retrieve memories using hybrid text-vision search.

        Args:
            query: Text query
            image_path: Path to query image
            filters: Metadata filters to apply
            limit: Maximum number of results to return

        Returns:
            List of retrieved memories ranked by relevance

        Raises:
            ValueError: If neither query nor image_path is provided

        Note:
            At least one of query or image_path must be provided.
            If both are provided, hybrid search is performed.
        """
        if query is None and image_path is None:
            raise ValueError("At least one of query or image_path must be provided")

        # Check cache
        cache_key = self._get_cache_key(query, image_path, filters, limit)
        if self._cache is not None and cache_key in self._cache:
            logger.debug("Cache hit for retrieval")
            self._update_cache_order(cache_key)
            return self._cache[cache_key]

        # Query rewriting for better retrieval
        rewritten_query = query
        if self.config.enable_query_rewriting and query:
            rewritten_query = self._rewrite_query_for_vision(query)

        # Generate embeddings
        text_embedding = None
        vision_embedding = None

        if query:
            try:
                text_embedding = self.text_embedder.embed(rewritten_query, "search")
            except Exception as e:
                logger.error(f"Failed to generate text embedding: {e}")

        if image_path:
            try:
                vision_embedding = self.vision_encoder.encode_image(image_path)
            except Exception as e:
                logger.error(f"Failed to generate vision embedding: {e}")

        # Perform hybrid search
        results = self.vector_store.search_hybrid(
            query_text_embedding=text_embedding,
            query_vision_embedding=vision_embedding,
            limit=limit,
            filters=filters,
            fusion_weight=self.config.fusion_weight,
        )

        # Cache results
        if self._cache is not None:
            self._add_to_cache(cache_key, results)

        logger.info(
            f"Retrieved {len(results)} memories "
            f"(query: {bool(query)}, image: {bool(image_path)})"
        )

        return results

    def retrieve_text_only(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 10,
    ) -> List[OutputData]:
        """
        Retrieve using text query only.

        Args:
            query: Text query
            filters: Metadata filters
            limit: Maximum results

        Returns:
            List of retrieved memories
        """
        # Query rewriting
        if self.config.enable_query_rewriting:
            query = self._rewrite_query_for_vision(query)

        # Generate embedding
        text_embedding = self.text_embedder.embed(query, "search")

        # Search
        results = self.vector_store.search_text(
            query_embedding=text_embedding,
            limit=limit,
            filters=filters,
        )

        logger.info(f"Text-only retrieval returned {len(results)} results")
        return results

    def retrieve_vision_only(
        self,
        image_path: str,
        filters: Optional[Dict] = None,
        limit: int = 10,
    ) -> List[OutputData]:
        """
        Retrieve using vision query only.

        Args:
            image_path: Path to query image
            filters: Metadata filters
            limit: Maximum results

        Returns:
            List of retrieved memories
        """
        # Generate embedding
        vision_embedding = self.vision_encoder.encode_image(image_path)

        # Search
        results = self.vector_store.search_vision(
            query_embedding=vision_embedding,
            limit=limit,
            filters=filters,
        )

        logger.info(f"Vision-only retrieval returned {len(results)} results")
        return results

    def _rewrite_query_for_vision(self, query: str) -> str:
        """
        Rewrite query to add visual terminology for better retrieval.

        Example:
            "red button" → "red button UI element clickable interface"

        Args:
            query: Original query

        Returns:
            Rewritten query with visual terms
        """
        # Visual term expansions
        expansions = {
            "button": ["UI element", "clickable", "interface"],
            "text": ["content", "words", "characters", "document"],
            "image": ["picture", "visual", "graphic", "screenshot"],
            "window": ["pane", "panel", "interface", "dialog"],
            "file": ["document", "item", "resource"],
            "screen": ["display", "interface", "view"],
            "error": ["message", "dialog", "alert", "popup"],
            "menu": ["list", "options", "dropdown"],
            "code": ["programming", "script", "function", "class"],
        }

        words = query.split()
        expanded_words = []

        for word in words:
            expanded_words.append(word)

            # Add expansions for matching terms
            word_lower = word.lower()
            if word_lower in expansions:
                expanded_words.extend(expansions[word_lower])

        rewritten = " ".join(expanded_words)

        if rewritten != query:
            logger.debug(f"Query rewritten: '{query}' → '{rewritten}'")

        return rewritten

    def _get_cache_key(
        self,
        query: Optional[str],
        image_path: Optional[str],
        filters: Optional[Dict],
        limit: int,
    ) -> str:
        """
        Generate cache key for retrieval.

        Args:
            query: Text query
            image_path: Path to image
            filters: Metadata filters
            limit: Result limit

        Returns:
            Cache key string
        """
        import hashlib

        key_parts = [query or "", image_path or "", str(limit)]

        if filters:
            # Sort filters for consistent key
            sorted_filters = sorted(filters.items())
            key_parts.append(str(sorted_filters))

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _add_to_cache(self, key: str, value: List[OutputData]):
        """Add item to LRU cache."""
        if self._cache is None:
            return

        # Remove if exists
        if key in self._cache:
            self._cache_order.remove(key)

        # Add to cache
        self._cache[key] = value
        self._cache_order.append(key)

        # Enforce cache size limit (100 items)
        max_cache_size = 100
        while len(self._cache_order) > max_cache_size:
            oldest_key = self._cache_order.pop(0)
            del self._cache[oldest_key]

    def _update_cache_order(self, key: str):
        """Update cache order when item is accessed."""
        if self._cache is None or key not in self._cache:
            return

        self._cache_order.remove(key)
        self._cache_order.append(key)

    def clear_cache(self):
        """Clear the retrieval cache."""
        if self._cache is not None:
            self._cache.clear()
            self._cache_order.clear()
            logger.info("Hybrid retriever cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dict with 'size' and 'max_size' keys
        """
        if self._cache is None:
            return {"size": 0, "max_size": 0, "enabled": False}

        return {
            "size": len(self._cache),
            "max_size": 100,
            "enabled": True,
        }


# Convenience function for quick usage
def retrieve_hybrid(
    query: Optional[str] = None,
    image_path: Optional[str] = None,
    text_embedder: Optional[EmbeddingBase] = None,
    vision_encoder: Optional[VisionEncoder] = None,
    vector_store: Optional[MultimodalChromaDB] = None,
    filters: Optional[Dict] = None,
    limit: int = 10,
) -> List[OutputData]:
    """
    Convenience function for hybrid retrieval.

    Args:
        query: Text query
        image_path: Path to query image
        text_embedder: Text embedding model
        vision_encoder: Vision encoder
        vector_store: Multimodal vector store
        filters: Metadata filters
        limit: Maximum results

    Returns:
        List of retrieved memories

    Note:
        All components (text_embedder, vision_encoder, vector_store) must be provided.
    """
    if text_embedder is None:
        raise ValueError("text_embedder must be provided")
    if vision_encoder is None:
        raise ValueError("vision_encoder must be provided")
    if vector_store is None:
        raise ValueError("vector_store must be provided")

    retriever = HybridVisionRetriever(
        text_embedder=text_embedder,
        vision_encoder=vision_encoder,
        vector_store=vector_store,
    )

    return retriever.retrieve(
        query=query,
        image_path=image_path,
        filters=filters,
        limit=limit,
    )
