### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Memory importance scoring for tiered memory management.

This module provides functionality to score memories based on multiple factors:
category, access frequency, recency, user marks, and semantic richness.
"""

import logging
import math
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

__all__ = [
    "ImportanceScorer",
    "ImportanceScorerConfig",
]


class ImportanceScorerConfig:
    """
    Configuration for importance scoring.

    Args:
        category_weights: Weights for different memory categories
        recency_half_life: Half-life for recency decay in days
        access_log_base: Base for access frequency logarithm
        enable_user_marks: Whether to consider user importance marks
    """

    def __init__(
        self,
        category_weights: Optional[Dict[str, float]] = None,
        recency_half_life: int = 30,
        access_log_base: float = 5.0,
        enable_user_marks: bool = True,
    ):
        self.category_weights = category_weights or self._default_category_weights()
        self.recency_half_life = recency_half_life
        self.access_log_base = access_log_base
        self.enable_user_marks = enable_user_marks

    @staticmethod
    def _default_category_weights() -> Dict[str, float]:
        """
        Default category weights.

        Higher weight = more important.
        """
        return {
            'fact': 0.9,
            'procedure': 0.85,
            'code': 0.8,
            'task': 0.75,
            'concept': 0.7,
            'document': 0.65,
            'question': 0.6,
            'conversation': 0.4,
            'greeting': 0.2,
            'general': 0.5,
            'image': 0.6,
            'video': 0.6,
        }


class ImportanceScorer:
    """
    Score memory importance for tiered management.

    Uses multiple factors:
    1. Category weight (30%): Some categories are more important
    2. Access frequency (30%): How often accessed (log scale)
    3. Recency (20%): Exponential decay from creation time
    4. User marks (10%): Explicit user importance flags
    5. Semantic richness (10%): Content length and structure

    Example:
        ```python
        scorer = ImportanceScorer()
        score = scorer.score_memory(
            content="Python is a programming language",
            metadata={"category": "fact", "user_id": "user1"},
            access_count=5,
            created_at=datetime.now()
        )
        # score: 0.75 (high importance)
        ```
    """

    def __init__(self, config: Optional[ImportanceScorerConfig] = None):
        """
        Initialize the importance scorer.

        Args:
            config: Scorer configuration
        """
        if config is None:
            config = ImportanceScorerConfig()

        self.config = config
        logger.info("ImportanceScorer initialized")

    def score_memory(
        self,
        content: str,
        metadata: Dict,
        access_count: int = 0,
        created_at: Optional[datetime] = None,
    ) -> float:
        """
        Calculate importance score for a memory.

        Score is between 0.0 and 1.0, where:
        - 0.0-0.3: Low importance (long-term memory)
        - 0.3-0.7: Medium importance (short-term memory)
        - 0.7-1.0: High importance (working memory)

        Args:
            content: Memory content
            metadata: Memory metadata (should include 'category')
            access_count: Number of times accessed
            created_at: Creation timestamp

        Returns:
            Importance score between 0.0 and 1.0
        """
        # 1. Category weight (30%)
        category_weight = self._get_category_weight(metadata.get('category', 'general'))
        category_score = 0.3 * category_weight

        # 2. Access frequency (30%)
        access_score = 0.3 * self._compute_access_score(access_count)

        # 3. Recency (20%)
        recency_score = 0.2 * self._compute_recency_score(created_at)

        # 4. User marks (10%)
        user_mark_score = 0.1 * self._compute_user_mark_score(metadata)

        # 5. Semantic richness (10%)
        richness_score = 0.1 * self._compute_semantic_richness(content, metadata)

        # Combine scores
        final_score = (
            category_score +
            access_score +
            recency_score +
            user_mark_score +
            richness_score
        )

        # Clamp to [0, 1]
        final_score = max(0.0, min(1.0, final_score))

        logger.debug(
            f"Memory score: {final_score:.3f} "
            f"(cat={category_score:.2f}, acc={access_score:.2f}, "
            f"rec={recency_score:.2f}, user={user_mark_score:.2f}, "
            f"rich={richness_score:.2f})"
        )

        return final_score

    def score_batch(
        self,
        memories: list,
    ) -> list:
        """
        Score multiple memories in batch.

        Args:
            memories: List of dicts with keys:
                - content: str
                - metadata: dict
                - access_count: int (optional)
                - created_at: datetime (optional)

        Returns:
            List of importance scores (same order as input)
        """
        scores = []
        for mem in memories:
            score = self.score_memory(
                content=mem.get('content', ''),
                metadata=mem.get('metadata', {}),
                access_count=mem.get('access_count', 0),
                created_at=mem.get('created_at'),
            )
            scores.append(score)
        return scores

    def _get_category_weight(self, category: str) -> float:
        """
        Get weight for a memory category.

        Args:
            category: Memory category

        Returns:
            Weight between 0.0 and 1.0
        """
        return self.config.category_weights.get(
            category.lower(),
            self.config.category_weights.get('general', 0.5)
        )

    def _compute_access_score(self, access_count: int) -> float:
        """
        Compute access frequency score using logarithmic scaling.

        Prevents very high access counts from dominating.

        Formula: log(access_count + 1) / log(base)

        Args:
            access_count: Number of accesses

        Returns:
            Score between 0.0 and 1.0
        """
        if access_count <= 0:
            return 0.0

        score = math.log(access_count + 1) / math.log(self.config.access_log_base)
        return min(1.0, score)

    def _compute_recency_score(self, created_at: Optional[datetime]) -> float:
        """
        Compute recency score using exponential decay.

        Formula: exp(-days_ago / half_life)

        Args:
            created_at: Creation timestamp

        Returns:
            Score between 0.0 and 1.0
        """
        if created_at is None:
            return 0.5  # Neutral score if unknown

        now = datetime.now()
        days_ago = (now - created_at).days

        if days_ago < 0:
            days_ago = 0  # Future dates treated as now

        # Exponential decay
        score = math.exp(-days_ago / self.config.recency_half_life)
        return score

    def _compute_user_mark_score(self, metadata: Dict) -> float:
        """
        Compute user mark score.

        Checks for explicit importance flags in metadata.

        Args:
            metadata: Memory metadata

        Returns:
            Score of 0.0 or 1.0
        """
        if not self.config.enable_user_marks:
            return 0.0

        # Check for importance flag
        if metadata.get('important') or metadata.get('starred') or metadata.get('pinned'):
            return 1.0

        return 0.0

    def _compute_semantic_richness(self, content: str, metadata: Dict) -> float:
        """
        Compute semantic richness score.

        Measures content quality based on:
        - Length (optimal range: 100-500 chars)
        - Structure (has structured data)
        - Entities (has entities extracted)

        Args:
            content: Memory content
            metadata: Memory metadata

        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0

        # Length score
        length = len(content)
        if 100 <= length <= 500:
            score += 0.5
        elif length > 500:
            score += 0.3
        elif length > 50:
            score += 0.2

        # Structure score
        structured_fields = ['entities', 'frame_details', 'ocr_text',
                           'code', 'data', 'json', 'structured']
        if any(field in str(metadata).lower() for field in structured_fields):
            score += 0.3

        # Entity count
        entities = metadata.get('entities')
        if entities and isinstance(entities, list):
            if len(entities) > 3:
                score += 0.2
            elif len(entities) > 0:
                score += 0.1

        return min(1.0, score)

    def get_tier_for_score(self, score: float) -> str:
        """
        Determine memory tier based on importance score.

        Args:
            score: Importance score (0-1)

        Returns:
            Tier name: 'working', 'short_term', or 'long_term'
        """
        if score >= 0.7:
            return 'working'
        elif score >= 0.4:
            return 'short_term'
        else:
            return 'long_term'
