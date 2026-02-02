### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-02             ###
### license: MIT                 ###

"""
Dynamic Memory Manager.

This module provides a dynamic memory management system that categorizes
and optimizes memory storage and retrieval based on content type.
"""

import logging
import uuid
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .dynamic_models import (
    MemoryCategory,
    QueryIntent,
    ClassifiedInput,
    ClassifiedQuery,
    DynamicMemoryConfig,
)
from .input_classifier import InputClassifier

logger = logging.getLogger(__name__)


class DynamicMemoryManager:
    """
    Dynamic memory manager for categorized memory storage and retrieval.

    This manager provides:
    - Automatic input classification
    - Category-based memory organization
    - Intent-aware search optimization
    - Category-weighted retrieval
    """

    def __init__(
        self,
        vector_store=None,
        embedding_model=None,
        llm=None,
        config: Optional[DynamicMemoryConfig] = None,
    ):
        """
        Initialize the dynamic memory manager.

        Args:
            vector_store: Base vector store instance
            embedding_model: Embedding model for generating embeddings
            llm: Language model for LLM-based classification
            config: Configuration for the dynamic memory system
        """
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.llm = llm

        # Configuration
        self.config = config or DynamicMemoryConfig()

        # Initialize classifier
        self.classifier = InputClassifier(
            llm=llm,
            enable_llm_fallback=True,
        )

        # Category-specific collections (if enabled)
        self.category_collections: Dict[MemoryCategory, Any] = {}
        if self.config.use_category_collections:
            self._initialize_category_collections()

        # Statistics tracking
        self.stats = {
            "total_classifications": 0,
            "category_counts": defaultdict(int),
            "intent_counts": defaultdict(int),
        }

    def _initialize_category_collections(self):
        """Initialize separate collections for different categories."""
        # This would create separate collections in the vector store
        # For now, we'll use metadata filtering instead
        logger.info("Category-specific collections enabled (using metadata filtering)")

    def classify_and_add(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        use_llm: bool = False,
    ) -> Dict[str, Any]:
        """
        Classify input and add to memory with category tagging.

        Args:
            text: The input text to store
            metadata: Additional metadata to store
            use_llm: Whether to use LLM for classification

        Returns:
            Dict containing the classification result and memory ID
        """
        # Classify the input
        classified = self.classifier.classify_input(text, use_llm=use_llm)

        # Update statistics
        self.stats["total_classifications"] += 1
        self.stats["category_counts"][classified.category] += 1

        # Merge metadata
        final_metadata = deepcopy(metadata) if metadata else {}
        final_metadata.update({
            "category": classified.category.value,
            "confidence": classified.confidence,
            "subcategories": classified.subcategories,
        })
        final_metadata.update(classified.metadata)

        # Generate embedding and store
        if self.embedding_model and self.vector_store:
            embedding = self.embedding_model.embed(text, "add")
            memory_id = str(uuid.uuid4())

            # Add to vector store with category metadata
            payload = {
                "data": text,
                "category": classified.category.value,
                "confidence": classified.confidence,
                **final_metadata,
            }

            self.vector_store.insert(
                vectors=[embedding],
                ids=[memory_id],
                payloads=[payload],
            )

            logger.debug(
                f"Added memory {memory_id} with category {classified.category.value} "
                f"(confidence: {classified.confidence:.2f})"
            )

            return {
                "memory_id": memory_id,
                "classification": classified.model_dump(),
                "metadata": final_metadata,
            }

        return {
            "classification": classified.model_dump(),
            "metadata": final_metadata,
        }

    def intelligent_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Perform intelligent search based on query intent and category.

        Args:
            query: The search query
            filters: Additional filters to apply
            limit: Maximum number of results

        Returns:
            Dict containing search results and classification info
        """
        # Classify the query
        classified_query = self.classifier.classify_query(query)

        # Update statistics
        self.stats["intent_counts"][classified_query.intent] += 1

        # Get optimized search parameters
        search_params = classified_query.search_params
        search_limit = min(limit, search_params.get("limit", limit))

        # Build category filters
        category_filters = self._build_category_filters(
            classified_query.target_categories,
            filters,
        )

        # Perform search
        results = []
        if self.embedding_model and self.vector_store:
            query_embedding = self.embedding_model.embed(query, "search")

            # Search in target categories
            all_results = []
            for category_filter in category_filters:
                category_results = self.vector_store.search(
                    query=query,
                    vectors=query_embedding,
                    limit=search_limit,
                    filters=category_filter,
                )
                all_results.extend(category_results)

            # Apply category weights if enabled
            if self.config.enable_category_weights:
                all_results = self._apply_category_weights(all_results)

            # Sort by score and deduplicate
            seen_ids = set()
            unique_results = []
            for result in sorted(all_results, key=lambda x: x.score, reverse=True):
                if result.id not in seen_ids:
                    seen_ids.add(result.id)
                    unique_results.append(result)
                    if len(unique_results) >= limit:
                        break

            results = unique_results

        logger.debug(
            f"Search for '{query[:50]}...' found {len(results)} results "
            f"(intent: {classified_query.intent.value}, "
            f"categories: {[c.value for c in classified_query.target_categories]})"
        )

        return {
            "results": results,
            "query_classification": classified_query.model_dump(),
            "search_params": search_params,
        }

    def get_context_for_response(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        filters: Optional[Dict[str, Any]] = None,
        max_context_items: int = 10,
    ) -> Dict[str, Any]:
        """
        Get optimized context for generating a response.

        This method analyzes the query intent and retrieves the most relevant
        memories across different categories to provide comprehensive context.

        Args:
            query: The user's query
            conversation_history: Recent conversation history
            filters: Additional filters to apply
            max_context_items: Maximum number of context items

        Returns:
            Dict containing categorized context and metadata
        """
        # Classify query
        classified_query = self.classifier.classify_query(query)

        # Get context from different categories
        context_by_category = {}
        all_context = []

        if self.embedding_model and self.vector_store:
            query_embedding = self.embedding_model.embed(query, "search")

            # Search each target category
            for category in classified_query.target_categories:
                category_filter = self._build_category_filter(category, filters)

                category_results = self.vector_store.search(
                    query=query,
                    vectors=query_embedding,
                    limit=max_context_items // 2,  # Split limit across categories
                    filters=category_filter,
                )

                if category_results:
                    context_by_category[category.value] = category_results
                    all_context.extend(category_results)

        # Sort by relevance and limit
        all_context.sort(key=lambda x: x.score, reverse=True)
        top_context = all_context[:max_context_items]

        # Organize context by category for structured presentation
        organized_context = {
            "query": query,
            "intent": classified_query.intent.value,
            "context_by_category": {
                cat: [self._format_context_item(item) for item in items]
                for cat, items in context_by_category.items()
            },
            "top_context": [self._format_context_item(item) for item in top_context],
            "total_items": len(top_context),
        }

        # Add conversation context if available
        if conversation_history:
            organized_context["conversation_history"] = conversation_history[-3:]  # Last 3 messages

        return organized_context

    def get_memories_by_category(
        self,
        category: MemoryCategory,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> List[Any]:
        """
        Retrieve all memories of a specific category.

        Args:
            category: The category to retrieve
            filters: Additional filters
            limit: Maximum number of results

        Returns:
            List of memories in the category
        """
        if not self.vector_store:
            return []

        category_filter = self._build_category_filter(category, filters)

        try:
            results = self.vector_store.list(filters=category_filter, limit=limit)
            return results[0] if isinstance(results, tuple) else results
        except Exception as e:
            logger.error(f"Error retrieving memories by category: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about memory classifications and usage."""
        return {
            "total_classifications": self.stats["total_classifications"],
            "category_distribution": dict(self.stats["category_counts"]),
            "intent_distribution": dict(self.stats["intent_counts"]),
        }

    def _build_category_filters(
        self,
        categories: List[MemoryCategory],
        base_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Build filters for multiple categories."""
        filters_list = []

        for category in categories:
            category_filter = self._build_category_filter(category, base_filters)
            filters_list.append(category_filter)

        return filters_list

    def _build_category_filter(
        self,
        category: MemoryCategory,
        base_filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build a filter for a specific category."""
        filter_dict = deepcopy(base_filters) if base_filters else {}
        filter_dict["category"] = category.value
        return filter_dict

    def _apply_category_weights(self, results: List[Any]) -> List[Any]:
        """Apply category-specific weights to search results."""
        if not results:
            return results

        weighted_results = []
        for result in results:
            category = result.payload.get("category", MemoryCategory.GENERAL.value)
            try:
                category_enum = MemoryCategory(category)
                weight = self.config.default_category_weights.get(
                    category_enum,
                    1.0,
                )
                # Adjust score by weight
                if hasattr(result, 'score'):
                    result.score = result.score * weight
            except ValueError:
                pass  # Keep original score if category is invalid
            weighted_results.append(result)

        return weighted_results

    def _format_context_item(self, item: Any) -> Dict[str, Any]:
        """Format a context item for presentation."""
        return {
            "id": item.id,
            "content": item.payload.get("data", ""),
            "category": item.payload.get("category", "general"),
            "score": item.score if hasattr(item, 'score') else 0.0,
            "metadata": {
                k: v for k, v in item.payload.items()
                if k not in ["data", "category"]
            },
        }

    def reset_statistics(self):
        """Reset classification statistics."""
        self.stats = {
            "total_classifications": 0,
            "category_counts": defaultdict(int),
            "intent_counts": defaultdict(int),
        }


__all__ = ["DynamicMemoryManager"]
