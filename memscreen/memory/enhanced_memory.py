### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-07             ###
### license: MIT                 ###

"""
Enhanced Memory adapter with all new optimization features.

This module provides an adapter that extends the existing Memory class
with new optimization features from Phase 1-6.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = [
    "EnhancedMemory",
]


class EnhancedMemory:
    """
    Enhanced Memory adapter with optimization features.

    This adapter wraps the existing Memory class and adds:
    - Visual encoding with SigLIP/CLIP
    - Multimodal vector storage
    - Tiered memory management
    - Conflict detection and resolution
    - Visual QA optimization

    Example:
        ```python
        from memscreen.memory.enhanced_memory import EnhancedMemory
        from memscreen.config import get_config

        # Load config
        config = get_config()

        # Create enhanced memory
        memory = EnhancedMemory(config)

        # Add memory with visual encoding
        memory.add_with_vision(
            messages=[{"role": "user", "content": "..."}],
            image_path="screenshot.png"
        )

        # Visual-aware search
        results = memory.search_visual(
            query="red button",
            image_path="query.png"
        )
        ```
    """

    def __init__(self, base_memory, config=None):
        """
        Initialize enhanced memory adapter.

        Args:
            base_memory: Existing Memory instance
            config: MemScreenConfig instance
        """
        from ..config import get_config

        self.base_memory = base_memory
        self.config = config or get_config()

        # Initialize new features based on config
        self._init_vision_encoder()
        self._init_multimodal_store()
        self._init_tiered_memory()
        self._init_conflict_resolver()

        logger.info("EnhancedMemory adapter initialized")

    def _init_vision_encoder(self):
        """Initialize vision encoder if enabled."""
        self.vision_encoder = None

        if not self.config.vision_encoder_enabled:
            logger.info("Vision encoder disabled in config")
            return

        try:
            from ..embeddings.vision_encoder import VisionEncoder, VisionEncoderConfig

            encoder_config = VisionEncoderConfig(
                model_type=self.config.vision_encoder_model_type,
                device=self.config.vision_encoder_device,
                cache_size=self.config.vision_encoder_cache_size,
            )

            self.vision_encoder = VisionEncoder(encoder_config)
            logger.info(f"Vision encoder initialized: {encoder_config.model_type}")

        except ImportError as e:
            logger.warning(f"Cannot initialize vision encoder: {e}")
            logger.info("Vision encoding will be disabled")

    def _init_multimodal_store(self):
        """Initialize multimodal vector store if enabled."""
        self.multimodal_store = None

        if not self.config.vision_encoder_enabled:
            logger.info("Multimodal store disabled (vision encoder required)")
            return

        try:
            from ..vector_store.multimodal_chroma import MultimodalChromaDB

            # Get text embedding dimensions from embedder
            text_dims = 512  # Default for most embedding models

            # Vision embedding dimensions depend on model
            vision_dims = 768 if self.config.vision_encoder_model_type == "siglip" else 512

            self.multimodal_store = MultimodalChromaDB(
                collection_name=self.base_memory.collection_name,
                text_embedding_dims=text_dims,
                vision_embedding_dims=vision_dims,
                path=str(self.base_memory.vector_store.client.settings.persist_directory),
            )

            logger.info("Multimodal vector store initialized")

        except Exception as e:
            logger.warning(f"Cannot initialize multimodal store: {e}")
            self.multimodal_store = None

    def _init_tiered_memory(self):
        """Initialize tiered memory manager if enabled."""
        self.tiered_manager = None

        if not self.config.tiered_memory_enabled:
            logger.info("Tiered memory disabled in config")
            return

        try:
            from .tiered_memory_manager import TieredMemoryManager, TieredMemoryConfig

            tiered_config = TieredMemoryConfig(
                enable_working_memory=self.config.working_memory_enabled,
                short_term_days=self.config.short_term_days,
                working_capacity=self.config.tiered_memory.get("working_capacity", 100),
                short_term_capacity=self.config.tiered_memory.get("short_term_capacity", 1000),
            )

            self.tiered_manager = TieredMemoryManager(
                vector_store=self.multimodal_store or self.base_memory.vector_store,
                embedding_model=self.base_memory.embedding_model,
                llm=self.base_memory.llm,
                config=tiered_config,
            )

            logger.info("Tiered memory manager initialized")

        except Exception as e:
            logger.warning(f"Cannot initialize tiered memory: {e}")

    def _init_conflict_resolver(self):
        """Initialize conflict resolver if enabled."""
        self.conflict_resolver = None

        if not self.config.conflict_resolution_enabled:
            logger.info("Conflict resolution disabled in config")
            return

        try:
            from .conflict_resolver import ConflictResolver, ConflictResolverConfig

            resolver_config = ConflictResolverConfig(
                similarity_threshold=self.config.similarity_threshold,
                enable_llm_check=self.config.conflict_resolution.get("enable_llm_check", True),
            )

            self.conflict_resolver = ConflictResolver(
                embedding_model=self.base_memory.embedding_model,
                llm=self.base_memory.llm,
                config=resolver_config,
            )

            logger.info("Conflict resolver initialized")

        except Exception as e:
            logger.warning(f"Cannot initialize conflict resolver: {e}")

    # ============================================
    # ENHANCED METHODS
    # ============================================

    def add_with_vision(
        self,
        messages: List[Dict],
        image_path: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """
        Add memory with visual encoding.

        Args:
            messages: Message list
            image_path: Path to screenshot/image
            user_id: User identifier
            agent_id: Agent identifier
            run_id: Run identifier
            metadata: Additional metadata

        Returns:
            Memory ID
        """
        if not self.vision_encoder or not self.multimodal_store:
            logger.warning("Vision encoding not available, using default add()")
            return self.base_memory.add(
                messages=messages,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                metadata=metadata,
            )

        # Extract content from messages
        content = self._extract_content_from_messages(messages)

        # Generate vision embedding if image provided
        vision_embedding = None
        if image_path and Path(image_path).exists():
            try:
                vision_embedding = self.vision_encoder.encode_image(image_path)
                logger.info(f"Generated vision embedding for {image_path}")
            except Exception as e:
                logger.error(f"Failed to encode image: {e}")

        # Generate text embedding
        text_embedding = self.base_memory.embedding_model.embed(content, "add")

        # Build metadata
        base_metadata, _ = _build_filters_and_metadata(
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            input_metadata=metadata or {},
        )

        # Add image path to metadata
        if image_path:
            base_metadata["image_path"] = image_path
            base_metadata["has_vision"] = True

        # Generate memory ID
        import uuid
        memory_id = str(uuid.uuid4())

        # Insert into multimodal store
        try:
            self.multimodal_store.insert_multimodal(
                ids=[memory_id],
                text_embeddings=[text_embedding],
                vision_embeddings=[vision_embedding] if vision_embedding else None,
                payloads=[base_metadata],
            )

            logger.info(f"Added multimodal memory {memory_id[:8]} with vision={bool(vision_embedding)}")

            return memory_id

        except Exception as e:
            logger.error(f"Failed to add multimodal memory: {e}")
            # Fallback to default add
            return self.base_memory.add(
                messages=messages,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                metadata=metadata,
            )

    def search_visual(
        self,
        query: str,
        image_path: Optional[str] = None,
        limit: int = 10,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ):
        """
        Visual-aware search using hybrid retrieval.

        Args:
            query: Text query
            image_path: Optional query image
            limit: Max results
            user_id: User identifier
            agent_id: Agent identifier
            run_id: Run identifier

        Returns:
            Search results
        """
        if not self.multimodal_store:
            logger.warning("Multimodal store not available, using default search")
            return self.base_memory.search(
                query=query,
                limit=limit,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
            )

        try:
            from .hybrid_retriever import HybridVisionRetriever

            # Create hybrid retriever
            retriever = HybridVisionRetriever(
                text_embedder=self.base_memory.embedding_model,
                vision_encoder=self.vision_encoder,
                vector_store=self.multimodal_store,
                config=None,  # Use defaults
            )

            # Build filters
            _, filters = _build_filters_and_metadata(
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
            )

            # Perform hybrid search
            results = retriever.retrieve(
                query=query,
                image_path=image_path,
                filters=filters,
                limit=limit,
            )

            logger.info(f"Hybrid search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            # Fallback to default search
            return self.base_memory.search(
                query=query,
                limit=limit,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
            )

    def get_memory_tier(self, memory_id: str) -> Optional[str]:
        """
        Get the tier of a memory.

        Args:
            memory_id: Memory ID

        Returns:
            Tier name or None
        """
        if not self.tiered_manager:
            return None

        return self.tiered_manager._memory_tiers.get(memory_id)

    def promote_memory(self, memory_id: str) -> bool:
        """
        Manually promote a memory to higher tier.

        Args:
            memory_id: Memory ID

        Returns:
            True if successful
        """
        if not self.tiered_manager:
            logger.warning("Tiered memory not available")
            return False

        try:
            current_tier = self.tiered_manager._memory_tiers.get(memory_id)
            if current_tier:
                if current_tier.value == "long_term":
                    self.tiered_manager._move_to_tier(
                        memory_id,
                        self.tiered_manager.MemoryTier.SHORT_TERM
                    )
                elif current_tier.value == "short_term" and self.config.working_memory_enabled:
                    self.tiered_manager._move_to_tier(
                        memory_id,
                        self.tiered_manager.MemoryTier.WORKING
                    )
                return True
        except Exception as e:
            logger.error(f"Failed to promote memory: {e}")
            return False

    def detect_conflicts(self, new_memory: str) -> List[Dict]:
        """
        Detect conflicts for a new memory.

        Args:
            new_memory: New memory content

        Returns:
            List of conflicts
        """
        if not self.conflict_resolver:
            return []

        try:
            # Get existing memories
            search_results = self.base_memory.search(
                query=new_memory,
                limit=20,
            )

            existing_memories = []
            for r in search_results:
                if r.payload:
                    existing_memories.append({
                        "id": r.id,
                        "data": r.payload.get("data", ""),
                        "embedding": None,  # Will be computed by resolver
                    })

            conflicts = self.conflict_resolver.detect_conflict(
                new_memory=new_memory,
                existing_memories=existing_memories,
            )

            logger.info(f"Detected {len(conflicts)} conflicts")
            return conflicts

        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return []

    # ============================================
    # DELEGATE METHODS TO BASE MEMORY
    # ============================================

    def add(self, *args, **kwargs):
        """Delegate add to base memory."""
        return self.base_memory.add(*args, **kwargs)

    def search(self, *args, **kwargs):
        """Delegate search to base memory."""
        return self.base_memory.search(*args, **kwargs)

    def update(self, *args, **kwargs):
        """Delegate update to base memory."""
        return self.base_memory.update(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Delegate delete to base memory."""
        return self.base_memory.delete(*args, **kwargs)

    def get(self, *args, **kwargs):
        """Delegate get to base memory."""
        return self.base_memory.get(*args, **kwargs)

    # ============================================
    # UTILITY METHODS
    # ============================================

    @staticmethod
    def _extract_content_from_messages(messages: List[Dict]) -> str:
        """Extract text content from messages."""
        content_parts = []
        for msg in messages:
            if isinstance(msg, dict):
                content = msg.get("content", "")
                if isinstance(content, str):
                    content_parts.append(content)
                elif isinstance(content, list):
                    # Handle vision content with images
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                content_parts.append(item.get("text", ""))
                            elif item.get("type") == "image_url":
                                # Skip actual image data, just note it exists
                                pass
                        elif isinstance(item, str):
                            content_parts.append(item)
        return " ".join(content_parts)


def create_enhanced_memory(base_memory) -> EnhancedMemory:
    """
    Convenience function to create enhanced memory from base memory.

    Args:
        base_memory: Existing Memory instance

    Returns:
        EnhancedMemory adapter instance
    """
    return EnhancedMemory(base_memory)
