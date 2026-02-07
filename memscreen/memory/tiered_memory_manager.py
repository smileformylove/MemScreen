### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Tiered memory management system implementing a time-pyramid architecture.

This module provides a three-tier memory system:
- Working Memory: Recent, frequently accessed items (~1 hour, ~100 items)
- Short-term Memory: Recent items (~1-7 days, ~1000 items)
- Long-term Memory: Older, compressed items (~7+ days, unlimited)
"""

import logging
import uuid
from typing import Dict, List, Optional, Literal
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

__all__ = [
    "MemoryTier",
    "TieredMemoryManager",
    "TieredMemoryConfig",
]


class MemoryTier(str, Enum):
    """Memory tier levels."""
    WORKING = "working"       # 1 hour, ~100 items
    SHORT_TERM = "short_term"  # 1-7 days, ~1000 items
    LONG_TERM = "long_term"    # 7+ days, unlimited


class TieredMemoryConfig:
    """
    Configuration for tiered memory management.

    Args:
        working_memory_hours: Maximum age for working memory
        short_term_days: Maximum age for short-term memory
        working_capacity: Max items in working memory
        short_term_capacity: Max items in short-term memory
        enable_working_memory: Enable working memory tier
        auto_decay: Enable automatic memory decay
        auto_compress: Enable automatic memory compression
    """

    def __init__(
        self,
        working_memory_hours: int = 1,
        short_term_days: int = 7,
        working_capacity: int = 100,
        short_term_capacity: int = 1000,
        enable_working_memory: bool = False,  # Disabled in phase 1
        auto_decay: bool = True,
        auto_compress: bool = True,
    ):
        self.working_memory_hours = working_memory_hours
        self.short_term_days = short_term_days
        self.working_capacity = working_capacity
        self.short_term_capacity = short_term_capacity
        self.enable_working_memory = enable_working_memory
        self.auto_decay = auto_decay
        self.auto_compress = auto_compress


class TieredMemoryManager:
    """
    Tiered memory manager implementing time-pyramid architecture.

    This manager automatically:
    - Assigns memories to appropriate tiers
    - Promotes frequently accessed memories
    - Demotes old/unused memories
    - Compresses long-term memories

    Example:
        ```python
        manager = TieredMemoryManager(
            vector_store=store,
            embedding_model=embedder,
            llm=llm,
            config=TieredMemoryConfig(enable_working_memory=False)
        )

        # Add memory
        memory_id = manager.add_memory(
            content="User's screen showed code editor",
            metadata={"category": "fact"},
            importance_score=0.6
        )

        # Retrieve (automatically promotes accessed memories)
        results = manager.retrieve("code editor", limit=10)
        ```
    """

    def __init__(
        self,
        vector_store,
        embedding_model,
        llm,
        config: Optional[TieredMemoryConfig] = None,
    ):
        """
        Initialize the tiered memory manager.

        Args:
            vector_store: Multimodal vector store
            embedding_model: Text embedding model
            llm: LLM for generating summaries
            config: Manager configuration
        """
        from .importance_scorer import ImportanceScorer

        if config is None:
            config = TieredMemoryConfig()

        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.llm = llm
        self.config = config

        # Importance scorer
        self.scorer = ImportanceScorer()

        # In-memory tracking (TODO: persist to database)
        self._memory_tiers = {}  # memory_id -> tier
        self._access_counts = {}  # memory_id -> count
        self._last_accessed = {}  # memory_id -> timestamp

        logger.info(
            f"TieredMemoryManager initialized "
            f"(working={config.enable_working_memory}, "
            f"short_term={config.short_term_days}d, "
            f"capacity={config.working_capacity}/{config.short_term_capacity})"
        )

    def add_memory(
        self,
        content: str,
        metadata: Dict,
        importance_score: Optional[float] = None,
        text_embedding: Optional[List[float]] = None,
        vision_embedding: Optional[List[float]] = None,
    ) -> str:
        """
        Add a memory to the appropriate tier.

        Args:
            content: Memory content
            metadata: Memory metadata
            importance_score: Pre-computed importance (optional)
            text_embedding: Text embedding vector (optional)
            vision_embedding: Vision embedding vector (optional)

        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())

        # Compute importance score if not provided
        if importance_score is None:
            importance_score = self.scorer.score_memory(
                content=content,
                metadata=metadata,
                access_count=0,
                created_at=datetime.now(),
            )

        # Determine initial tier
        tier = self._determine_initial_tier(importance_score, metadata)

        # Generate embeddings if not provided
        if text_embedding is None:
            text_embedding = self.embedding_model.embed(content, "add")

        # Prepare payload
        payload = metadata.copy()
        payload.update({
            "data": content,
            "tier": tier.value,
            "importance_score": importance_score,
            "created_at": datetime.now().isoformat(),
            "access_count": 0,
        })

        # Insert into vector store
        self.vector_store.insert_multimodal(
            ids=[memory_id],
            text_embeddings=[text_embedding],
            vision_embeddings=[vision_embedding] if vision_embedding else None,
            payloads=[payload],
        )

        # Track tier and access
        self._memory_tiers[memory_id] = tier
        self._access_counts[memory_id] = 0
        self._last_accessed[memory_id] = datetime.now()

        logger.info(
            f"Added memory {memory_id[:8]} to {tier.value} "
            f"(importance={importance_score:.2f})"
        )

        return memory_id

    def retrieve(
        self,
        query: str,
        tier: Optional[MemoryTier] = None,
        limit: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Retrieve memories, promoting accessed items.

        Strategy:
        1. Search from highest tier to lowest
        2. Stop when enough results found
        3. Promote accessed memories

        Args:
            query: Search query
            tier: Specific tier to search (None = all tiers)
            limit: Max results
            filters: Metadata filters

        Returns:
            List of memories with metadata
        """
        query_embedding = self.embedding_model.embed(query, "search")

        results = []
        searched_tiers = []

        # Determine search order
        if tier:
            tiers_to_search = [tier]
        else:
            tiers_to_search = [
                MemoryTier.WORKING,
                MemoryTier.SHORT_TERM,
                MemoryTier.LONG_TERM,
            ]

        # Filter out disabled tiers
        if not self.config.enable_working_memory:
            tiers_to_search = [t for t in tiers_to_search if t != MemoryTier.WORKING]

        # Search each tier
        for current_tier in tiers_to_search:
            tier_filter = {"tier": current_tier.value}
            if filters:
                tier_filter.update(filters)

            tier_results = self.vector_store.search_text(
                query_embedding=query_embedding,
                filters=tier_filter,
                limit=limit,
            )

            results.extend(tier_results)
            searched_tiers.append(current_tier)

            if len(results) >= limit:
                break

        # Take only top results
        results = results[:limit]

        # Promote accessed memories
        for result in results:
            if result.id:
                self._promote_memory(result.id, searched_tiers)

        logger.info(
            f"Retrieved {len(results)} memories "
            f"(tiers={[t.value for t in searched_tiers]})"
        )

        return results

    def _determine_initial_tier(
        self,
        importance_score: float,
        metadata: Dict
    ) -> MemoryTier:
        """
        Determine initial tier for a memory.

        Args:
            importance_score: Importance score (0-1)
            metadata: Memory metadata

        Returns:
            Initial memory tier
        """
        # High importance → Working (if enabled)
        if importance_score >= 0.7 and self.config.enable_working_memory:
            return MemoryTier.WORKING

        # Medium importance → Short-term
        elif importance_score >= 0.4:
            return MemoryTier.SHORT_TERM

        # Low importance → Long-term
        else:
            return MemoryTier.LONG_TERM

    def _promote_memory(self, memory_id: str, from_tiers: List[MemoryTier]):
        """
        Promote memory to higher tier if frequently accessed.

        Promotion rules:
        - Working Memory: No promotion (already highest)
        - Short-term → Working: If accessed 3+ times in 1 hour
        - Long-term → Short-term: If accessed at all

        Args:
            memory_id: Memory to promote
            from_tiers: Tiers it was found in
        """
        current_tier = self._memory_tiers.get(memory_id)

        if current_tier is None:
            return  # Unknown memory

        if current_tier == MemoryTier.WORKING:
            return  # Already highest

        # Update access count
        self._access_counts[memory_id] = self._access_counts.get(memory_id, 0) + 1
        self._last_accessed[memory_id] = datetime.now()

        # Short-term → Working
        if current_tier == MemoryTier.SHORT_TERM:
            if self.config.enable_working_memory:
                # Check access frequency
                access_count = self._access_counts[memory_id]
                if access_count >= 3:
                    self._move_to_tier(memory_id, MemoryTier.WORKING)
                    logger.info(f"Promoted {memory_id[:8]} to Working Memory")

        # Long-term → Short-term
        elif current_tier == MemoryTier.LONG_TERM:
            self._move_to_tier(memory_id, MemoryTier.SHORT_TERM)
            logger.info(f"Promoted {memory_id[:8]} to Short-term Memory")

    def _move_to_tier(self, memory_id: str, new_tier: MemoryTier):
        """
        Move memory to a different tier.

        Args:
            memory_id: Memory to move
            new_tier: Target tier
        """
        # Update metadata
        self.vector_store.update(
            memory_id=memory_id,
            payload={"tier": new_tier.value},
        )

        # Update tracking
        self._memory_tiers[memory_id] = new_tier

    def decay_and_compress(self):
        """
        Perform memory decay and compression.

        Tasks:
        1. Demote old Working Memory → Short-term
        2. Demote old Short-term → Long-term
        3. Compress Long-term memories

        Should be called periodically (e.g., daily).
        """
        if not self.config.auto_decay:
            return

        logger.info("Starting memory decay and compression...")

        now = datetime.now()
        demoted_count = 0
        compressed_count = 0

        # Process all memories
        for memory_id, tier in list(self._memory_tiers.items()):
            # Get creation time
            try:
                memory_data = self.vector_store.get(memory_id)
                if not memory_data.get("text_data"):
                    continue

                created_at_str = memory_data["text_data"].payload.get("created_at")
                if not created_at_str:
                    continue

                created_at = datetime.fromisoformat(created_at_str)
                age = now - created_at

            except Exception as e:
                logger.warning(f"Failed to process {memory_id[:8]}: {e}")
                continue

            # Working Memory → Short-term
            if tier == MemoryTier.WORKING:
                if age.total_seconds() > self.config.working_memory_hours * 3600:
                    self._move_to_tier(memory_id, MemoryTier.SHORT_TERM)
                    demoted_count += 1

            # Short-term → Long-term
            elif tier == MemoryTier.SHORT_TERM:
                if age.days > self.config.short_term_days:
                    # Check access frequency
                    access_count = self._access_counts.get(memory_id, 0)
                    if access_count < 2:  # Rarely accessed
                        if self.config.auto_compress:
                            self._compress_and_archive(memory_id)
                        else:
                            self._move_to_tier(memory_id, MemoryTier.LONG_TERM)
                        demoted_count += 1
                        compressed_count += 1

        logger.info(
            f"Decay complete: demoted={demoted_count}, compressed={compressed_count}"
        )

    def _compress_and_archive(self, memory_id: str):
        """
        Compress memory using LLM summarization.

        Args:
            memory_id: Memory to compress
        """
        try:
            # Get memory data
            memory_data = self.vector_store.get(memory_id)
            if not memory_data.get("text_data"):
                return

            payload = memory_data["text_data"].payload
            content = payload.get("data", "")

            if not content:
                return

            # Generate summary using LLM
            summary_prompt = f"""Summarize this memory, preserving key information:

{content}

Provide:
1. One-sentence summary
2. Key facts (bullet points)
3. Keywords (comma-separated)

Be concise but complete."""

            summary = self.llm.generate_response(
                messages=[{"role": "user", "content": summary_prompt}],
                options={"num_predict": 256},
            )

            # Generate new embedding for summary
            summary_embedding = self.embedding_model.embed(summary, "add")

            # Update with compressed version
            updated_payload = payload.copy()
            updated_payload.update({
                "data": summary,
                "compressed": True,
                "original_length": len(content),
                "compressed_at": datetime.now().isoformat(),
                "tier": MemoryTier.LONG_TERM.value,
            })

            # Update in vector store
            self.vector_store.update(
                memory_id=memory_id,
                payload=updated_payload,
                text_embedding=summary_embedding,
            )

            # Update tier tracking
            self._memory_tiers[memory_id] = MemoryTier.LONG_TERM

            logger.info(f"Compressed and archived {memory_id[:8]}")

        except Exception as e:
            logger.error(f"Failed to compress {memory_id[:8]}: {e}")

    def get_stats(self) -> Dict:
        """
        Get statistics about memory distribution.

        Returns:
            Dict with tier counts and capacities
        """
        tier_counts = {
            MemoryTier.WORKING: 0,
            MemoryTier.SHORT_TERM: 0,
            MemoryTier.LONG_TERM: 0,
        }

        for tier in self._memory_tiers.values():
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        return {
            "tier_counts": {
                "working": tier_counts[MemoryTier.WORKING],
                "short_term": tier_counts[MemoryTier.SHORT_TERM],
                "long_term": tier_counts[MemoryTier.LONG_TERM],
            },
            "capacities": {
                "working": self.config.working_capacity,
                "short_term": self.config.short_term_capacity,
                "long_term": None,  # Unlimited
            },
            "total_memories": len(self._memory_tiers),
        }
