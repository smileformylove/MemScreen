### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Vision context optimizer for 7b model performance.

This module optimizes visual context for efficient 7b model inference:
- Re-ranking by relevance and recency
- Description compression
- Scene-based grouping
"""

import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

__all__ = [
    "VisionContextOptimizer",
]


class VisionContextOptimizer:
    """
    Optimize visual context for 7b models.

    Strategies:
    1. Re-rank by relevance + recency
    2. Compress redundant descriptions
    3. Group by scene for coherent context
    4. Limit to optimal token count (3000-4000)

    Example:
        ```python
        optimizer = VisionContextOptimizer()

        optimized_context = optimizer.optimize_context_for_7b(
            visual_memories=[...],
            query="red button",
            max_tokens=3500
        )
        ```
    """

    def __init__(self):
        """Initialize the optimizer."""
        logger.info("VisionContextOptimizer initialized")

    def optimize_context_for_7b(
        self,
        visual_memories: List[Dict],
        query: str,
        max_tokens: int = 3500,
    ) -> List[Dict]:
        """
        Optimize visual context for 7b model.

        Args:
            visual_memories: Retrieved visual memories
            query: User query
            max_tokens: Target token count

        Returns:
            Optimized (compressed) visual memories
        """
        if not visual_memories:
            return []

        # Step 1: Re-rank by relevance and recency
        ranked_memories = self._rank_by_relevance_and_recency(
            visual_memories, query
        )

        # Step 2: Select top memories
        selected = self._select_top_memories(
            ranked_memories, max_tokens
        )

        # Step 3: Compress descriptions
        compressed = []
        for mem in selected:
            compressed_mem = mem.copy()
            compressed_mem['description'] = self._compress_description(
                mem.get('description', '')
            )
            compressed.append(compressed_mem)

        logger.info(
            f"Optimized context: {len(visual_memories)} → {len(compressed)} memories"
        )

        return compressed

    def _rank_by_relevance_and_recency(
        self,
        memories: List[Dict],
        query: str,
    ) -> List[Dict]:
        """
        Re-rank memories by combined relevance + recency score.

        Formula: score = 0.6 * relevance + 0.4 * recency

        Args:
            memories: Visual memories
            query: User query

        Returns:
            Re-ranked memories (sorted)
        """
        now = datetime.now()

        for mem in memories:
            # Get relevance score
            relevance = mem.get('score', 0.5)

            # Calculate recency score
            created_at_str = mem.get('created_at', mem.get('timestamp', ''))
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                    days_ago = (now - created_at).days
                    recency = 1.0 / (1.0 + days_ago * 0.1)
                except:
                    recency = 0.5
            else:
                recency = 0.5

            # Combined score
            mem['combined_score'] = 0.6 * relevance + 0.4 * recency

        # Sort by combined score
        return sorted(
            memories,
            key=lambda x: x.get('combined_score', 0),
            reverse=True
        )

    def _select_top_memories(
        self,
        memories: List[Dict],
        max_tokens: int,
    ) -> List[Dict]:
        """
        Select top memories within token budget.

        Args:
            memories: Ranked memories
            max_tokens: Token budget

        Returns:
            Selected memories
        """
        selected = []
        total_tokens = 0

        # Rough token estimation: 1 token ≈ 4 characters
        for mem in memories:
            # Estimate tokens for this memory
            desc = mem.get('description', '')
            text = mem.get('text_content', '')
            chars = len(desc) + len(text)
            est_tokens = chars / 4

            if total_tokens + est_tokens > max_tokens:
                break

            selected.append(mem)
            total_tokens += est_tokens

        return selected

    def _compress_description(self, description: str) -> str:
        """
        Compress description while preserving key information.

        Args:
            description: Original description

        Returns:
            Compressed description
        """
        if not description:
            return ""

        # If already short, return as-is
        if len(description) <= 150:
            return description

        # Truncate with ellipsis
        return description[:147] + "..."

    def format_for_7b(self, memories: List[Dict]) -> str:
        """
        Format optimized memories for 7b model.

        Groups by scene and uses structured format.

        Args:
            memories: Optimized visual memories

        Returns:
            Formatted context string
        """
        if not memories:
            return "No visual context available."

        # Group by scene type
        by_scene = self._group_by_scene(memories)

        sections = []

        for scene, scene_memories in by_scene.items():
            sections.append(f"## {scene.title()}")

            for mem in scene_memories[:3]:  # Max 3 per scene
                desc = mem.get('description', 'No description')
                timestamp = mem.get('timestamp', mem.get('created_at', ''))

                if timestamp:
                    sections.append(f"• [{timestamp}] {desc}")
                else:
                    sections.append(f"• {desc}")

            sections.append("")  # Empty line between scenes

        return "\n".join(sections)

    def _group_by_scene(self, memories: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group memories by scene type.

        Args:
            memories: Visual memories

        Returns:
            Dict mapping scene_type → memories
        """
        grouped = {}

        for mem in memories:
            scene_type = mem.get('scene_type', 'general')
            if scene_type not in grouped:
                grouped[scene_type] = []
            grouped[scene_type].append(mem)

        return grouped
