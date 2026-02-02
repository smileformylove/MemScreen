### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-02             ###
### license: MIT                 ###

"""
Dynamic Memory Classification Models.

This module provides models for categorizing memories and managing dynamic memory storage.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryCategory(str, Enum):
    """Categories for classifying memory inputs."""

    # Question-based memories
    QUESTION = "question"  # User questions, queries

    # Task-based memories
    TASK = "task"  # Action items, to-do lists, commands

    # Knowledge-based memories
    FACT = "fact"  # Factual information, knowledge
    CONCEPT = "concept"  # Concepts, explanations

    # Conversation-based memories
    CONVERSATION = "conversation"  # General conversations
    GREETING = "greeting"  # Greetings and small talk

    # Technical content
    CODE = "code"  # Code snippets, programming
    DOCUMENT = "document"  # Documents, notes, files

    # Media content
    IMAGE = "image"  # Images, screenshots
    VIDEO = "video"  # Video content

    # Procedures and workflows
    PROCEDURE = "procedure"  # Step-by-step procedures
    WORKFLOW = "workflow"  # Multi-step workflows

    # Personal information
    PERSONAL = "personal"  # Personal preferences, settings
    REFERENCE = "reference"  # Reference information, links

    # Uncategorized
    GENERAL = "general"  # General/unclassified content


class QueryIntent(str, Enum):
    """Intents for classifying search queries."""

    RETRIEVE_FACT = "retrieve_fact"  # Looking for specific facts
    FIND_PROCEDURE = "find_procedure"  # Looking for how-to instructions
    SEARCH_CONVERSATION = "search_conversation"  # Looking for past conversations
    LOCATE_CODE = "locate_code"  # Looking for code snippets
    FIND_DOCUMENT = "find_document"  # Looking for documents
    GET_TASKS = "get_tasks"  # Looking for action items
    GENERAL_SEARCH = "general_search"  # General semantic search


class MemoryCategoryWeights(BaseModel):
    """Weights for different memory categories in search."""

    category: MemoryCategory
    weight: float = Field(default=1.0, ge=0.0, le=5.0)
    description: Optional[str] = Field(default=None)


class ClassifiedInput(BaseModel):
    """Result of input classification."""

    text: str = Field(..., description="The original input text")
    category: MemoryCategory = Field(..., description="The classified category")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Classification confidence")
    subcategories: List[str] = Field(default_factory=list, description="Additional subcategories")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extracted metadata")


class ClassifiedQuery(BaseModel):
    """Result of query classification."""

    query: str = Field(..., description="The original query")
    intent: QueryIntent = Field(..., description="The classified intent")
    target_categories: List[MemoryCategory] = Field(
        default_factory=list,
        description="Target memory categories to search"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Classification confidence")
    search_params: Dict[str, Any] = Field(default_factory=dict, description="Optimized search parameters")


class DynamicMemoryConfig(BaseModel):
    """Configuration for dynamic memory system."""

    # Classification settings
    enable_auto_classification: bool = Field(
        default=True,
        description="Enable automatic input classification"
    )
    enable_intent_classification: bool = Field(
        default=True,
        description="Enable query intent classification"
    )

    # Category-specific storage
    use_category_collections: bool = Field(
        default=True,
        description="Use separate collections for different categories"
    )

    # Search optimization
    enable_category_weights: bool = Field(
        default=True,
        description="Apply category-specific weights in search"
    )
    default_category_weights: Dict[MemoryCategory, float] = Field(
        default_factory=lambda: {
            MemoryCategory.FACT: 1.2,
            MemoryCategory.CONCEPT: 1.1,
            MemoryCategory.PROCEDURE: 1.2,
            MemoryCategory.CODE: 1.0,
            MemoryCategory.DOCUMENT: 1.0,
            MemoryCategory.CONVERSATION: 0.9,
            MemoryCategory.QUESTION: 0.8,
            MemoryCategory.TASK: 1.1,
        },
        description="Default weights for each category in search"
    )

    # Caching
    cache_classification_results: bool = Field(
        default=True,
        description="Cache classification results for faster repeated queries"
    )
    classification_cache_size: int = Field(
        default=500,
        description="Number of classification results to cache"
    )

    # Performance tuning
    batch_classification_threshold: int = Field(
        default=5,
        description="Minimum items to trigger batch classification"
    )
    max_search_categories: int = Field(
        default=3,
        description="Maximum number of categories to search in parallel"
    )


__all__ = [
    "MemoryCategory",
    "QueryIntent",
    "MemoryCategoryWeights",
    "ClassifiedInput",
    "ClassifiedQuery",
    "DynamicMemoryConfig",
]
