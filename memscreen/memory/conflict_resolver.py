### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Intelligent conflict detection and resolution for memory management.

This module implements a three-level conflict detection system:
1. Fast hash-based duplicate detection
2. Semantic similarity detection
3. LLM-based semantic conflict analysis
"""

import hashlib
import logging
import json
from typing import Dict, List, Optional, Literal
from datetime import datetime
from collections import OrderedDict

logger = logging.getLogger(__name__)

__all__ = [
    "ConflictResolver",
    "ConflictResolverConfig",
]


class ConflictResolverConfig:
    """
    Configuration for conflict resolution.

    Args:
        similarity_threshold: Threshold for semantic similarity (0-1)
        enable_llm_check: Enable LLM-based conflict detection
        llm_cache_size: Size of LLM result cache
    """

    def __init__(
        self,
        similarity_threshold: float = 0.95,
        enable_llm_check: bool = True,
        llm_cache_size: int = 1000,
    ):
        self.similarity_threshold = similarity_threshold
        self.enable_llm_check = enable_llm_check
        self.llm_cache_size = llm_cache_size


class ConflictResolver:
    """
    Detect and resolve memory conflicts.

    Three-level detection:
    1. Hash-based: Exact/near-exact duplicates (MD5)
    2. Similarity-based: Semantically similar (cosine similarity > threshold)
    3. LLM-based: Semantic conflict analysis (contradictory, complementary, etc.)

    Resolution strategies:
    - skip: Don't add (duplicate)
    - merge: Merge with existing memory
    - keep_both: Keep both memories
    - mark_conflict: Mark as conflicting

    Example:
        ```python
        resolver = ConflictResolver(
            embedding_model=embedder,
            llm=llm
        )

        conflicts = resolver.detect_conflict(
            new_memory="The file size is 100MB",
            existing_memories=[...]
        )

        for conflict in conflicts:
            resolution = resolver.resolve_conflict(conflict, new_memory)
            execute_resolution(resolution)
        ```
    """

    def __init__(
        self,
        embedding_model,
        llm,
        config: Optional[ConflictResolverConfig] = None,
    ):
        """
        Initialize the conflict resolver.

        Args:
            embedding_model: Text embedding model
            llm: LLM for semantic analysis
            config: Resolver configuration
        """
        if config is None:
            config = ConflictResolverConfig()

        self.embedding_model = embedding_model
        self.llm = llm
        self.config = config

        # LRU cache for LLM conflict checks
        self._conflict_cache = OrderedDict()
        self._cache_max_size = config.llm_cache_size

        logger.info(
            f"ConflictResolver initialized "
            f"(similarity_threshold={config.similarity_threshold}, "
            f"llm_check={config.enable_llm_check})"
        )

    def detect_conflict(
        self,
        new_memory: str,
        existing_memories: List[Dict],
    ) -> List[Dict]:
        """
        Detect conflicts between new memory and existing memories.

        Args:
            new_memory: New memory content
            existing_memories: List of existing memories with keys:
                - id: str
                - data: str
                - embedding: List[float] (optional)
                - hash: str (optional)

        Returns:
            List of conflict details, each with:
            - memory_id: str
            - conflict_type: 'duplicate' | 'equivalent' | 'contradictory' |
                            'complementary' | 'unrelated'
            - confidence: float (0-1)
            - resolution: str (suggested action)
            - existing_memory: Dict
        """
        conflicts = []

        # Generate hash for new memory
        new_hash = hashlib.md5(new_memory.encode()).hexdigest()
        new_embedding = self.embedding_model.embed(new_memory, "add")

        for mem in existing_memories:
            # Level 1: Hash-based duplicate detection
            mem_hash = mem.get('hash')
            if mem_hash and mem_hash == new_hash:
                conflicts.append({
                    'memory_id': mem['id'],
                    'conflict_type': 'duplicate',
                    'confidence': 1.0,
                    'resolution': 'skip',
                    'existing_memory': mem,
                })
                logger.info(f"Exact duplicate detected: {mem['id'][:8]}")
                continue  # Exact duplicate, no need for further checks

            # Level 2: Semantic similarity
            mem_embedding = mem.get('embedding')
            if mem_embedding:
                similarity = self._cosine_similarity(new_embedding, mem_embedding)

                if similarity >= self.config.similarity_threshold:
                    # Level 3: LLM-based conflict detection
                    if self.config.enable_llm_check:
                        conflict_detail = self._llm_conflict_check(
                            new_memory, mem['data']
                        )
                    else:
                        # Fallback without LLM
                        conflict_detail = {
                            'type': 'equivalent',
                            'confidence': similarity,
                            'suggestion': 'skip',
                        }

                    conflicts.append({
                        'memory_id': mem['id'],
                        'conflict_type': conflict_detail['type'],
                        'confidence': conflict_detail['confidence'],
                        'resolution': conflict_detail['suggestion'],
                        'existing_memory': mem,
                    })

        return conflicts

    def resolve_conflict(
        self,
        conflict: Dict,
        new_memory: str,
    ) -> Dict:
        """
        Resolve a detected conflict.

        Args:
            conflict: Conflict details from detect_conflict()
            new_memory: New memory content

        Returns:
            Resolution action with keys:
            - action: 'skip' | 'update' | 'merge' | 'keep_both' | 'mark_conflict'
            - reason: str
            - memory_id: str
            - merged_content: str (if action='merge')
        """
        conflict_type = conflict['conflict_type']
        existing = conflict['existing_memory']
        memory_id = conflict['memory_id']

        if conflict_type == 'duplicate':
            return {
                'action': 'skip',
                'reason': 'Exact duplicate content detected',
                'memory_id': memory_id,
            }

        elif conflict_type == 'equivalent':
            return {
                'action': 'skip',
                'reason': 'Semantically equivalent memory exists',
                'memory_id': memory_id,
                'increment_access': True,  # Boost access count
            }

        elif conflict_type == 'contradictory':
            return {
                'action': 'mark_conflict',
                'reason': 'Contradictory information detected',
                'memory_id': memory_id,
                'conflict_metadata': {
                    'type': 'contradiction',
                    'detected_at': datetime.now().isoformat(),
                    'conflicting_memory': new_memory[:100],  # Preview
                },
            }

        elif conflict_type == 'complementary':
            # Merge memories
            merged = self._merge_memories(new_memory, existing['data'])
            return {
                'action': 'merge',
                'reason': 'Complementary information, merging',
                'memory_id': memory_id,
                'merged_content': merged,
            }

        else:  # unrelated or default
            return {
                'action': 'keep_both',
                'reason': 'Unrelated content',
                'memory_id': memory_id,
            }

    def _llm_conflict_check(
        self,
        new_memory: str,
        existing_memory: str,
    ) -> Dict:
        """
        Use LLM to detect conflict type.

        Returns conflict details:
        - type: DUPLICATE | EQUIVALENT | CONTRADICTORY | COMPLEMENTARY | UNRELATED
        - confidence: 0.0-1.0
        - reasoning: str
        - suggestion: skip | update | merge | keep_both

        Args:
            new_memory: New memory content
            existing_memory: Existing memory content

        Returns:
            Conflict details dict
        """
        # Check cache
        cache_key = f"{hash(new_memory)}:{hash(existing_memory)}"
        if cache_key in self._conflict_cache:
            return self._conflict_cache[cache_key]

        # Build prompt
        prompt = f"""Analyze the relationship between these two statements:

Statement A: {new_memory}
Statement B: {existing_memory}

Determine if they are:
1. DUPLICATE: Identical or nearly identical
2. EQUIVALENT: Same meaning, different wording
3. CONTRADICTORY: Directly conflict (A says X, B says not-X)
4. COMPLEMENTARY: Can be combined (add more detail)
5. UNRELATED: No relationship

Respond in JSON format:
{{
  "type": "DUPLICATE|EQUIVALENT|CONTRADICTORY|COMPLEMENTARY|UNRELATED",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation",
  "suggestion": "skip|update|merge|keep_both"
}}"""

        try:
            response = self.llm.generate_response(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                options={"num_predict": 128, "temperature": 0.1},
            )

            result = json.loads(response)

            # Normalize to lowercase
            result['type'] = result['type'].lower()

            # Map to our types
            type_mapping = {
                'duplicate': 'duplicate',
                'equivalent': 'equivalent',
                'contradictory': 'contradictory',
                'complementary': 'complementary',
                'unrelated': 'unrelated',
            }
            result['type'] = type_mapping.get(result['type'], 'unrelated')

            # Cache result
            self._add_to_cache(cache_key, result)

            return result

        except Exception as e:
            logger.warning(f"LLM conflict check failed: {e}")
            # Return default
            return {
                "type": "unrelated",
                "confidence": 0.0,
                "reasoning": "LLM check failed",
                "suggestion": "keep_both"
            }

    def _merge_memories(self, mem1: str, mem2: str) -> str:
        """
        Merge two complementary memories.

        Args:
            mem1: First memory
            mem2: Second memory

        Returns:
            Merged memory content
        """
        prompt = f"""Merge these two related statements into one comprehensive statement:

Statement 1: {mem1}
Statement 2: {mem2}

Provide a merged statement that combines all key information from both.
Keep it concise but complete."""

        try:
            merged = self.llm.generate_response(
                messages=[{"role": "user", "content": prompt}],
                options={"num_predict": 256, "temperature": 0.3},
            )
            return merged.strip()

        except Exception as e:
            logger.error(f"Failed to merge memories: {e}")
            # Fallback: simple concatenation
            return f"{mem1} {mem2}"

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score between 0 and 1
        """
        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _add_to_cache(self, key: str, value: Dict):
        """Add item to LRU cache."""
        # Remove if exists
        if key in self._conflict_cache:
            del self._conflict_cache[key]

        # Add to cache
        self._conflict_cache[key] = value

        # Enforce size limit
        while len(self._conflict_cache) > self._cache_max_size:
            # Remove oldest (first item)
            self._conflict_cache.popitem(last=False)

    def clear_cache(self):
        """Clear the conflict cache."""
        self._conflict_cache.clear()
        logger.info("Conflict resolver cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dict with 'size' and 'max_size' keys
        """
        return {
            "size": len(self._conflict_cache),
            "max_size": self._cache_max_size,
        }
