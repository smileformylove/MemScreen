### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Multimodal ChromaDB vector store with support for both text and vision embeddings.

This module extends ChromaDB to support dual-vector storage and retrieval:
- Text embeddings for semantic search
- Vision embeddings for visual similarity search
"""

import logging
from typing import Dict, List, Optional, Literal, Tuple, Any
from pathlib import Path

from .chroma import ChromaDB, OutputData

logger = logging.getLogger(__name__)

__all__ = [
    "MultimodalChromaDB",
]


class MultimodalChromaDB:
    """
    Multimodal vector store supporting both text and vision embeddings.

    This class manages two separate ChromaDB collections:
    - Text collection: Stores text embeddings (512-768 dim)
    - Vision collection: Stores vision embeddings (512-768 dim)

    Both collections are linked via the same memory ID in metadata, enabling
    cross-modal retrieval and fusion.

    Example:
        ```python
        store = MultimodalChromaDB(
            collection_name="memories",
            text_embedding_dims=512,
            vision_embedding_dims=768
        )

        # Insert with both text and vision vectors
        store.insert_multimodal(
            ids=["mem1"],
            text_embeddings=[[0.1, 0.2, ...]],
            vision_embeddings=[[0.3, 0.4, ...]],
            payloads=[{"content": "...", "image_path": "..."}]
        )

        # Hybrid search
        results = store.search_hybrid(
            query_text="search query",
            query_image="query.jpg",
            limit=10
        )
        ```
    """

    def __init__(
        self,
        collection_name: str,
        text_embedding_dims: int = 512,
        vision_embedding_dims: int = 768,
        host: Optional[str] = None,
        port: Optional[int] = None,
        path: Optional[str] = None,
    ):
        """
        Initialize the multimodal vector store.

        Args:
            collection_name: Base name for collections (will append "_text" and "_vision")
            text_embedding_dims: Dimension of text embeddings
            vision_embedding_dims: Dimension of vision embeddings
            host: ChromaDB server host
            port: ChromaDB server port
            path: Local path for ChromaDB persistence
        """
        self.collection_name = collection_name
        self.text_embedding_dims = text_embedding_dims
        self.vision_embedding_dims = vision_embedding_dims

        # Create two collections: one for text, one for vision
        text_collection_name = f"{collection_name}_text"
        vision_collection_name = f"{collection_name}_vision"

        logger.info(
            f"Initializing multimodal store: "
            f"text={text_collection_name} (dim={text_embedding_dims}), "
            f"vision={vision_collection_name} (dim={vision_embedding_dims})"
        )

        # Initialize ChromaDB instances
        self.text_store = ChromaDB(
            collection_name=text_collection_name,
            host=host,
            port=port,
            path=path,
        )

        self.vision_store = ChromaDB(
            collection_name=vision_collection_name,
            host=host,
            port=port,
            path=path,
        )

    def insert_multimodal(
        self,
        ids: List[str],
        text_embeddings: Optional[List[List[float]]] = None,
        vision_embeddings: Optional[List[List[float]]] = None,
        payloads: Optional[List[Dict]] = None,
    ):
        """
        Insert memories with text and/or vision embeddings.

        Args:
            ids: List of memory IDs
            text_embeddings: List of text embedding vectors
            vision_embeddings: List of vision embedding vectors
            payloads: List of metadata payloads (same for both collections)

        Note:
            At least one of text_embeddings or vision_embeddings must be provided.
            If both are provided, they are stored in separate collections.
        """
        if not ids:
            return

        if text_embeddings is None and vision_embeddings is None:
            raise ValueError(
                "At least one of text_embeddings or vision_embeddings must be provided"
            )

        # Prepare payloads for both collections
        text_payloads = payloads or [{}] * len(ids)
        vision_payloads = payloads or [{}] * len(ids)

        # Mark which collection has the embedding
        for i in range(len(ids)):
            if text_embeddings is not None:
                text_payloads[i] = text_payloads[i] or {}
                text_payloads[i]["has_text_embedding"] = True

            if vision_embeddings is not None:
                vision_payloads[i] = vision_payloads[i] or {}
                vision_payloads[i]["has_vision_embedding"] = True

        # Insert text embeddings if provided
        if text_embeddings is not None:
            if len(text_embeddings) != len(ids):
                raise ValueError("Length of text_embeddings must match length of ids")

            # Validate dimensions
            for i, emb in enumerate(text_embeddings):
                if len(emb) != self.text_embedding_dims:
                    raise ValueError(
                        f"Text embedding {i} has dimension {len(emb)}, "
                        f"expected {self.text_embedding_dims}"
                    )

            self.text_store.insert(
                vectors=text_embeddings,
                payloads=text_payloads,
                ids=ids,
            )
            logger.info(f"Inserted {len(text_embeddings)} text embeddings")

        # Insert vision embeddings if provided
        if vision_embeddings is not None:
            if len(vision_embeddings) != len(ids):
                raise ValueError("Length of vision_embeddings must match length of ids")

            # Validate dimensions
            for i, emb in enumerate(vision_embeddings):
                if len(emb) != self.vision_embedding_dims:
                    raise ValueError(
                        f"Vision embedding {i} has dimension {len(emb)}, "
                        f"expected {self.vision_embedding_dims}"
                    )

            self.vision_store.insert(
                vectors=vision_embeddings,
                payloads=vision_payloads,
                ids=ids,
            )
            logger.info(f"Inserted {len(vision_embeddings)} vision embeddings")

    def search_hybrid(
        self,
        query_text_embedding: Optional[List[float]] = None,
        query_vision_embedding: Optional[List[float]] = None,
        limit: int = 10,
        filters: Optional[Dict] = None,
        fusion_weight: float = 0.6,
    ) -> List[OutputData]:
        """
        Hybrid search combining text and vision queries using RRF fusion.

        Args:
            query_text_embedding: Text query embedding
            query_vision_embedding: Vision query embedding (image or extracted features)
            limit: Maximum number of results to return
            filters: Metadata filters to apply
            fusion_weight: Weight for text results (0-1), vision weight = 1 - fusion_weight

        Returns:
            Fused and ranked list of results

        Note:
            At least one of query_text_embedding or query_vision_embedding must be provided.
        """
        if query_text_embedding is None and query_vision_embedding is None:
            raise ValueError(
                "At least one of query_text_embedding or query_vision_embedding must be provided"
            )

        # Search text collection
        text_results = []
        text_scores = {}
        if query_text_embedding is not None:
            text_results = self.text_store.search(
                query="",
                vectors=[query_text_embedding],
                limit=limit * 2,  # Retrieve more for fusion
                filters=filters,
            )
            # Score by rank (RRF)
            k = 60  # RRF constant
            for i, result in enumerate(text_results):
                score = 1 / (k + i + 1)
                text_scores[result.id] = score

        # Search vision collection
        vision_results = []
        vision_scores = {}
        if query_vision_embedding is not None:
            vision_results = self.vision_store.search(
                query="",
                vectors=[query_vision_embedding],
                limit=limit * 2,  # Retrieve more for fusion
                filters=filters,
            )
            # Score by rank (RRF)
            k = 60  # RRF constant
            for i, result in enumerate(vision_results):
                score = 1 / (k + i + 1)
                vision_scores[result.id] = score

        # Fuse scores
        fused_scores = {}
        all_ids = set(text_scores.keys()) | set(vision_scores.keys())

        for memory_id in all_ids:
            text_score = text_scores.get(memory_id, 0)
            vision_score = vision_scores.get(memory_id, 0)

            # Weighted fusion
            final_score = (
                fusion_weight * text_score +
                (1 - fusion_weight) * vision_score
            )
            fused_scores[memory_id] = final_score

        # Get full results from text collection (has full payloads)
        all_results = text_results if text_results else vision_results
        result_map = {r.id: r for r in all_results}

        # Sort by fused score
        sorted_ids = sorted(
            fused_scores.keys(),
            key=lambda mid: fused_scores[mid],
            reverse=True
        )[:limit]

        # Build final results with fused scores
        final_results = []
        for memory_id in sorted_ids:
            if memory_id in result_map:
                result = result_map[memory_id]
                result.score = fused_scores[memory_id]
                final_results.append(result)

        logger.info(
            f"Hybrid search returned {len(final_results)} results "
            f"(text: {len(text_results)}, vision: {len(vision_results)})"
        )

        return final_results

    def search_text(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[OutputData]:
        """
        Search using text embedding only.

        Args:
            query_embedding: Text query embedding
            limit: Maximum number of results
            filters: Metadata filters

        Returns:
            List of search results
        """
        return self.text_store.search(
            query="",
            vectors=[query_embedding],
            limit=limit,
            filters=filters,
        )

    def search_vision(
        self,
        query_embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[OutputData]:
        """
        Search using vision embedding only.

        Args:
            query_embedding: Vision query embedding
            limit: Maximum number of results
            filters: Metadata filters

        Returns:
            List of search results
        """
        return self.vision_store.search(
            query="",
            vectors=[query_embedding],
            limit=limit,
            filters=filters,
        )

    def update(
        self,
        memory_id: str,
        text_embedding: Optional[List[float]] = None,
        vision_embedding: Optional[List[float]] = None,
        payload: Optional[Dict] = None,
    ):
        """
        Update embeddings and/or metadata for a memory.

        Args:
            memory_id: ID of the memory to update
            text_embedding: New text embedding (if updating)
            vision_embedding: New vision embedding (if updating)
            payload: New metadata (if updating)

        Note:
            At least one of text_embedding, vision_embedding, or payload must be provided.
        """
        if text_embedding is None and vision_embedding is None and payload is None:
            raise ValueError(
                "At least one of text_embedding, vision_embedding, or payload must be provided"
            )

        # Update text collection
        if text_embedding is not None or payload is not None:
            self.text_store.update(
                vector_id=memory_id,
                vector=text_embedding,
                payload=payload,
            )

        # Update vision collection
        if vision_embedding is not None or payload is not None:
            self.vision_store.update(
                vector_id=memory_id,
                vector=vision_embedding,
                payload=payload,
            )

        logger.info(f"Updated memory {memory_id}")

    def delete(self, memory_id: str):
        """
        Delete a memory from both collections.

        Args:
            memory_id: ID of the memory to delete
        """
        self.text_store.delete(memory_id)
        self.vision_store.delete(memory_id)
        logger.info(f"Deleted memory {memory_id}")

    def get(self, memory_id: str) -> Dict[str, Any]:
        """
        Get a memory with both text and vision data.

        Args:
            memory_id: ID of the memory

        Returns:
            Dict with keys:
            - text_data: OutputData from text collection (or None)
            - vision_data: OutputData from vision collection (or None)
        """
        result = {
            "text_data": None,
            "vision_data": None,
        }

        try:
            result["text_data"] = self.text_store.get(memory_id)
        except Exception as e:
            logger.debug(f"No text data for {memory_id}: {e}")

        try:
            result["vision_data"] = self.vision_store.get(memory_id)
        except Exception as e:
            logger.debug(f"No vision data for {memory_id}: {e}")

        return result

    def list(self, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """
        List all memories (from text collection).

        Args:
            filters: Metadata filters
            limit: Maximum number of results

        Returns:
            List of memory metadata
        """
        return self.text_store.list(filters=filters, limit=limit)

    def reset(self):
        """Reset both collections."""
        logger.warning("Resetting multimodal vector store...")
        self.text_store.reset()
        self.vision_store.reset()

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the vector store.

        Returns:
            Dict with keys:
            - text_count: Number of items in text collection
            - vision_count: Number of items in vision collection
            - total_count: Total unique memories
        """
        text_list = self.text_store.list(limit=1000000)
        vision_list = self.vision_store.list(limit=1000000)

        # list() returns [List[OutputData]], so we need to extract the inner list
        text_items = text_list[0] if text_list else []
        vision_items = vision_list[0] if vision_list else []

        text_ids = set(item.id for item in text_items if item)
        vision_ids = set(item.id for item in vision_items if item)

        return {
            "text_count": len(text_ids),
            "vision_count": len(vision_ids),
            "total_count": len(text_ids | vision_ids),
        }
