### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-02             ###
### license: MIT                 ###

"""
Smart Context Retriever.

This module provides intelligent context retrieval optimized for
generating responses with the most relevant memories.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .dynamic_models import MemoryCategory, QueryIntent
from .input_classifier import InputClassifier

logger = logging.getLogger(__name__)


class ContextRetriever:
    """
    Smart context retriever for optimized memory access.

    Features:
    - Multi-strategy context retrieval (semantic, temporal, categorical)
    - Conversation context management
    - Query optimization for faster inference
    - Relevance scoring and ranking
    """

    def __init__(
        self,
        dynamic_manager=None,
        vector_store=None,
        embedding_model=None,
        max_context_items: int = 15,
        context_window: int = 5,
    ):
        """
        Initialize the context retriever.

        Args:
            dynamic_manager: DynamicMemoryManager instance
            vector_store: Vector store for semantic search
            embedding_model: Embedding model for queries
            max_context_items: Maximum number of items to retrieve
            context_window: Number of recent conversation turns to consider
        """
        self.dynamic_manager = dynamic_manager
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.classifier = InputClassifier()

        self.max_context_items = max_context_items
        self.context_window = context_window

        # Conversation history cache
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history_size = 20

    def retrieve_context(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        strategies: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve context using multiple strategies.

        Args:
            query: The user's query
            filters: Additional filters to apply
            strategies: Retrieval strategies to use (default: all)

        Returns:
            Dict containing organized context by strategy and relevance
        """
        if strategies is None:
            strategies = ["semantic", "categorical", "temporal", "conversational"]

        context = {
            "query": query,
            "strategies_used": strategies,
            "context_items": [],
            "metadata": {},
        }

        # Classify query for intent
        classified_query = self.classifier.classify_query(query)
        context["intent"] = classified_query.intent.value

        # Apply different retrieval strategies
        if "semantic" in strategies:
            semantic_context = self._retrieve_semantic_context(query, filters)
            context["semantic_context"] = semantic_context
            context["context_items"].extend(semantic_context)

        if "categorical" in strategies:
            categorical_context = self._retrieve_categorical_context(
                classified_query, filters
            )
            context["categorical_context"] = categorical_context
            context["context_items"].extend(categorical_context)

        if "temporal" in strategies:
            temporal_context = self._retrieve_temporal_context(query, filters)
            context["temporal_context"] = temporal_context
            context["context_items"].extend(temporal_context)

        if "conversational" in strategies:
            conversational_context = self._retrieve_conversational_context(query)
            context["conversational_context"] = conversational_context
            context["context_items"].extend(conversational_context)

        # Remove duplicates and sort by relevance
        context["context_items"] = self._deduplicate_and_rank(context["context_items"])

        # Limit to max items
        context["context_items"] = context["context_items"][:self.max_context_items]
        context["total_items"] = len(context["context_items"])

        return context

    def _retrieve_semantic_context(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve context using semantic similarity."""
        if not self.vector_store or not self.embedding_model:
            return []

        try:
            query_embedding = self.embedding_model.embed(query, "search")
            results = self.vector_store.search(
                query=query,
                vectors=query_embedding,
                limit=self.max_context_items,
                filters=filters,
            )

            return [
                {
                    "id": item.id,
                    "content": item.payload.get("data", ""),
                    "score": item.score if hasattr(item, 'score') else 0.0,
                    "category": item.payload.get("category", "general"),
                    "strategy": "semantic",
                }
                for item in results
            ]
        except Exception as e:
            logger.error(f"Error in semantic retrieval: {e}")
            return []

    def _retrieve_categorical_context(
        self,
        classified_query,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve context based on query category intent."""
        if not self.dynamic_manager:
            return []

        try:
            # Use dynamic manager's intelligent search
            result = self.dynamic_manager.intelligent_search(
                query=classified_query.query,
                filters=filters,
                limit=self.max_context_items // 2,
            )

            return [
                {
                    "id": item.id,
                    "content": item.payload.get("data", ""),
                    "score": item.score if hasattr(item, 'score') else 0.0,
                    "category": item.payload.get("category", "general"),
                    "strategy": "categorical",
                }
                for item in result.get("results", [])
            ]
        except Exception as e:
            logger.error(f"Error in categorical retrieval: {e}")
            return []

    def _retrieve_temporal_context(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        days_back: int = 7,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent context from the last N days."""
        if not self.vector_store or not self.embedding_model:
            return []

        try:
            # Build time-based filter
            time_filter = deepcopy(filters) if filters else {}
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            time_filter["created_at"] = {"$gte": cutoff_date}

            query_embedding = self.embedding_model.embed(query, "search")
            results = self.vector_store.search(
                query=query,
                vectors=query_embedding,
                limit=self.max_context_items // 3,
                filters=time_filter,
            )

            return [
                {
                    "id": item.id,
                    "content": item.payload.get("data", ""),
                    "score": item.score if hasattr(item, 'score') else 0.0,
                    "category": item.payload.get("category", "general"),
                    "created_at": item.payload.get("created_at", ""),
                    "strategy": "temporal",
                }
                for item in results
            ]
        except Exception as e:
            logger.error(f"Error in temporal retrieval: {e}")
            return []

    def _retrieve_conversational_context(
        self,
        query: str,
    ) -> List[Dict[str, Any]]:
        """Retrieve context from recent conversation history."""
        context = []

        # Get recent conversation turns
        recent_history = self.conversation_history[-self.context_window:]

        for turn in recent_history:
            content = turn.get("content", "")
            if content:
                context.append({
                    "content": content,
                    "role": turn.get("role", "user"),
                    "strategy": "conversational",
                    "score": 0.5,  # Base score for conversation context
                })

        return context

    def _deduplicate_and_rank(
        self,
        items: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Remove duplicates and rank by relevance."""
        # Deduplicate by ID
        seen_ids = set()
        unique_items = []

        for item in items:
            item_id = item.get("id", id(item.get("content", "")))
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_items.append(item)

        # Sort by score (highest first)
        unique_items.sort(key=lambda x: x.get("score", 0.0), reverse=True)

        return unique_items

    def add_to_conversation_history(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Add a message to conversation history.

        Args:
            role: The role (user, assistant, system)
            content: The message content
            metadata: Optional metadata
        """
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        })

        # Trim history if needed
        if len(self.conversation_history) > self.max_history_size:
            self.conversation_history = self.conversation_history[-self.max_history_size:]

    def clear_conversation_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def format_context_for_llm(
        self,
        context: Dict[str, Any],
        format_type: str = "structured",
    ) -> str:
        """
        Format retrieved context for LLM input.

        Args:
            context: The context dictionary from retrieve_context
            format_type: Format type ("structured", "concise", "detailed")

        Returns:
            Formatted context string
        """
        if format_type == "structured":
            return self._format_structured(context)
        elif format_type == "concise":
            return self._format_concise(context)
        elif format_type == "detailed":
            return self._format_detailed(context)
        else:
            return self._format_structured(context)

    def _format_structured(self, context: Dict[str, Any]) -> str:
        """Format context in structured format by category."""
        items = context.get("context_items", [])

        # Group by category
        by_category = defaultdict(list)
        for item in items:
            category = item.get("category", "general")
            by_category[category].append(item)

        # Build formatted string
        sections = []
        for category, items in by_category.items():
            if items:
                section = f"## {category.title()}\n"
                for item in items[:3]:  # Top 3 per category
                    section += f"- {item.get('content', '')}\n"
                sections.append(section)

        return "\n".join(sections)

    def _format_concise(self, context: Dict[str, Any]) -> str:
        """Format context in concise format."""
        items = context.get("context_items", [])[:5]

        lines = ["Relevant context:"]
        for item in items:
            lines.append(f"- {item.get('content', '')}")

        return "\n".join(lines)

    def _format_detailed(self, context: Dict[str, Any]) -> str:
        """Format context in detailed format with scores."""
        items = context.get("context_items", [])

        lines = ["## Retrieved Context"]
        lines.append(f"Query: {context.get('query', '')}")
        lines.append(f"Intent: {context.get('intent', 'unknown')}")
        lines.append(f"Total items: {context.get('total_items', len(items))}")
        lines.append("")

        for i, item in enumerate(items, 1):
            lines.append(f"{i}. [{item.get('category', 'general')}] {item.get('content', '')}")
            lines.append(f"   Score: {item.get('score', 0.0):.2f} | Strategy: {item.get('strategy', 'unknown')}")
            lines.append("")

        return "\n".join(lines)

    def optimize_query_for_inference(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Optimize query with context for faster inference.

        This creates a condensed query prompt that includes only the most
        relevant context, reducing token count and improving speed.

        Args:
            query: The original query
            context: The retrieved context

        Returns:
            Optimized query string with context
        """
        # Get top context items
        top_items = context.get("context_items", [])[:5]

        # Extract key information
        key_info = []
        for item in top_items:
            if item.get("score", 0.0) > 0.7:  # Only high-relevance items
                key_info.append(item.get("content", ""))

        if not key_info:
            return query

        # Build optimized prompt
        optimized = f"""Query: {query}

Key context:
{chr(10).join(f'- {info}' for info in key_info)}

Response:"""

        return optimized


from copy import deepcopy


__all__ = ["ContextRetriever"]
