### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-02             ###
### license: MIT                 ###

"""
Intelligent Agent with Automatic Input Classification and Dispatch

This agent uses the dynamic memory system to automatically classify inputs
and intelligently dispatch them to appropriate handlers.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentConfig
from .base_skill import BaseSkill, SkillResult
from ..memory import (
    MemoryCategory,
    QueryIntent,
    InputClassifier,
)

logger = logging.getLogger(__name__)


@dataclass
class DispatchRule:
    """Rule for dispatching inputs to handlers"""
    category: MemoryCategory
    intent: Optional[QueryIntent] = None
    handler: Optional[str] = None  # Skill name or handler function
    priority: int = 1
    description: str = ""


class IntelligentAgent(BaseAgent):
    """
    Enhanced Agent with automatic input classification and intelligent dispatch.

    Features:
    - Automatic input classification using dynamic memory
    - Intent-based query routing
    - Category-aware context retrieval
    - Smart skill selection
    """

    def __init__(
        self,
        memory_system=None,
        llm_client=None,
        config: AgentConfig = None,
        enable_classification: bool = True,
    ):
        """
        Initialize the intelligent agent.

        Args:
            memory_system: Memory system (should have dynamic features enabled)
            llm_client: LLM client for AI capabilities
            config: Agent configuration
            enable_classification: Enable automatic input classification
        """
        super().__init__(memory_system, llm_client, config)

        self.enable_classification = enable_classification

        # Initialize classifier if memory system has it
        self.classifier = None
        if (enable_classification and
            hasattr(memory_system, 'classifier')):
            self.classifier = memory_system.classifier
            logger.info("[Agent] Input classifier initialized")

        # Dispatch rules
        self.dispatch_rules: List[DispatchRule] = []
        self._setup_default_dispatch_rules()

        # Category handlers
        self.category_handlers: Dict[MemoryCategory, Callable] = {}

        # Statistics
        self.dispatch_stats = {
            "total_dispatches": 0,
            "category_counts": {},
            "intent_counts": {},
        }

        # OPTIMIZATION: Classification cache
        self._classification_cache = {}
        self._cache_max_size = 50

        logger.info(f"[Agent] Intelligent agent initialized (classification={enable_classification})")

    def _get_cached_classification(self, text: str):
        """Get cached classification if available"""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return self._classification_cache.get(text_hash)

    def _cache_classification(self, text: str, classification, intent_classification):
        """Cache classification results"""
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()

        # Simple cache eviction
        if len(self._classification_cache) >= self._cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self._classification_cache))
            del self._classification_cache[oldest_key]

        self._classification_cache[text_hash] = (classification, intent_classification)

    def _setup_default_dispatch_rules(self):
        """Setup default dispatch rules based on categories and intents"""
        self.dispatch_rules = [
            # Question -> Search/Answer
            DispatchRule(
                category=MemoryCategory.QUESTION,
                intent=QueryIntent.RETRIEVE_FACT,
                handler="search_memory",
                priority=1,
                description="Search memory for facts"
            ),
            DispatchRule(
                category=MemoryCategory.QUESTION,
                intent=QueryIntent.FIND_PROCEDURE,
                handler="find_procedure",
                priority=1,
                description="Find procedures"
            ),

            # Task -> Task management
            DispatchRule(
                category=MemoryCategory.TASK,
                handler="manage_task",
                priority=2,
                description="Manage tasks"
            ),

            # Code -> Code assistant
            DispatchRule(
                category=MemoryCategory.CODE,
                handler="code_assistant",
                priority=1,
                description="Code assistance"
            ),

            # Procedure -> Execute/Explain
            DispatchRule(
                category=MemoryCategory.PROCEDURE,
                handler="handle_procedure",
                priority=1,
                description="Handle procedures"
            ),

            # Greeting -> Greet back
            DispatchRule(
                category=MemoryCategory.GREETING,
                handler="greet",
                priority=3,
                description="Handle greetings"
            ),
        ]

    def register_category_handler(
        self,
        category: MemoryCategory,
        handler: Callable
    ):
        """
        Register a custom handler for a specific category.

        Args:
            category: Memory category to handle
            handler: Async function to handle inputs of this category
        """
        self.category_handlers[category] = handler
        logger.info(f"[Agent] Registered handler for category: {category.value}")

    async def process_input(
        self,
        input_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process an input with automatic classification and dispatch.

        Args:
            input_text: The input text to process
            context: Additional context

        Returns:
            Processing result
        """
        logger.info(f"[Agent] Processing input: {input_text[:50]}...")

        # OPTIMIZATION: Check cache first
        cached = self._get_cached_classification(input_text)
        if cached:
            classification, intent_classification = cached
            logger.info(f"[Agent] ⚡ Using cached classification")
        else:
            # 1. Classify input
            classification = None
            if self.enable_classification and self.classifier:
                classification = self.classifier.classify_input(input_text)
                logger.info(f"[Agent] Input classified as: {classification.category.value} "
                           f"(confidence: {classification.confidence:.2f})")
            else:
                logger.warning("[Agent] Classification not available, using default routing")

            # 2. Classify query intent
            intent_classification = None
            if self.enable_classification and self.classifier:
                intent_classification = self.classifier.classify_query(input_text)
                logger.info(f"[Agent] Query intent: {intent_classification.intent.value}")

            # Cache the results
            if classification:
                self._cache_classification(input_text, classification, intent_classification)

        # 3. Find matching dispatch rule
        dispatch_rule = self._find_dispatch_rule(
            classification.category if classification else None,
            intent_classification.intent if intent_classification else None
        )

        # 4. Dispatch to handler
        result = await self._dispatch(
            input_text=input_text,
            classification=classification,
            intent_classification=intent_classification,
            dispatch_rule=dispatch_rule,
            context=context or {}
        )

        # 5. Update statistics
        self._update_dispatch_stats(classification, intent_classification)

        # 6. OPTIMIZATION: Store to memory in background (don't wait)
        if self.memory_system and classification:
            # Create background task for storage (non-blocking)
            asyncio.create_task(
                self._store_with_classification(input_text, classification, result)
            )
            logger.info(f"[Agent] ⚡ Storage scheduled in background")

        return result

    def _find_dispatch_rule(
        self,
        category: Optional[MemoryCategory],
        intent: Optional[QueryIntent]
    ) -> Optional[DispatchRule]:
        """Find the best matching dispatch rule"""
        if not category:
            return None

        # Find rules matching category
        matching_rules = [
            rule for rule in self.dispatch_rules
            if rule.category == category
        ]

        # Filter by intent if specified
        if intent and matching_rules:
            intent_matching = [
                rule for rule in matching_rules
                if rule.intent == intent or rule.intent is None
            ]
            if intent_matching:
                matching_rules = intent_matching

        # Return highest priority rule
        if matching_rules:
            return max(matching_rules, key=lambda r: r.priority)

        return None

    async def _dispatch(
        self,
        input_text: str,
        classification,
        intent_classification,
        dispatch_rule: Optional[DispatchRule],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Dispatch input to appropriate handler"""

        # Check for custom category handler first
        if classification and classification.category in self.category_handlers:
            handler = self.category_handlers[classification.category]
            logger.info(f"[Agent] Using custom handler for {classification.category.value}")
            return await handler(input_text, context, classification)

        # Use dispatch rule
        if dispatch_rule and dispatch_rule.handler:
            return await self._execute_dispatch_handler(
                dispatch_rule.handler,
                input_text,
                context,
                classification,
                intent_classification
            )

        # Default handling based on category
        return await self._default_dispatch(
            input_text,
            context,
            classification,
            intent_classification
        )

    async def _execute_dispatch_handler(
        self,
        handler_name: str,
        input_text: str,
        context: Dict[str, Any],
        classification,
        intent_classification,
    ) -> Dict[str, Any]:
        """Execute a dispatch handler (skill or built-in handler)"""

        # Check if it's a registered skill
        skill = self.skill_registry.get(handler_name)
        if skill:
            logger.info(f"[Agent] Dispatching to skill: {handler_name}")
            result = await skill.execute(
                input_text=input_text,
                context=context,
                classification=classification.model_dump() if classification else None,
                intent=intent_classification.model_dump() if intent_classification else None
            )
            return {
                "success": result.success,
                "data": result.data,
                "handler": f"skill:{handler_name}",
                "metadata": result.metadata
            }

        # Check for built-in handler
        builtin_handler = getattr(self, f"_handle_{handler_name}", None)
        if builtin_handler:
            logger.info(f"[Agent] Dispatching to built-in handler: {handler_name}")
            return await builtin_handler(input_text, context, classification, intent_classification)

        logger.warning(f"[Agent] Handler not found: {handler_name}")
        return await self._default_dispatch(input_text, context, classification, intent_classification)

    async def _default_dispatch(
        self,
        input_text: str,
        context: Dict[str, Any],
        classification,
        intent_classification,
    ) -> Dict[str, Any]:
        """Default dispatch logic when no specific handler found"""

        category = classification.category if classification else None

        # Default behaviors
        if category == MemoryCategory.QUESTION:
            # Search memory for answer
            return await self._handle_search_memory(input_text, context, classification, intent_classification)

        elif category == MemoryCategory.TASK:
            # Add to memory as task
            return await self._handle_manage_task(input_text, context, classification, intent_classification)

        elif category == MemoryCategory.CODE:
            # Code assistance
            return await self._handle_code_assistant(input_text, context, classification, intent_classification)

        else:
            # General LLM response
            return await self._handle_general_query(input_text, context, classification, intent_classification)

    # Built-in handlers

    async def _handle_search_memory(
        self,
        input_text: str,
        context: Dict[str, Any],
        classification,
        intent_classification,
    ) -> Dict[str, Any]:
        """Handle memory search queries"""
        if not self.memory_system:
            return {
                "success": False,
                "error": "Memory system not available",
                "handler": "search_memory"
            }

        # Use smart search if available
        if hasattr(self.memory_system, 'smart_search'):
            results = self.memory_system.smart_search(
                query=input_text,
                **context.get('filters', {})
            )
            return {
                "success": True,
                "data": results,
                "handler": "smart_search",
                "query": input_text
            }

        # Fallback to regular search
        elif hasattr(self.memory_system, 'search'):
            results = self.memory_system.search(
                query=input_text,
                **context.get('filters', {})
            )
            return {
                "success": True,
                "data": results,
                "handler": "search",
                "query": input_text
            }

        return {"success": False, "error": "Search not available"}

    async def _handle_manage_task(
        self,
        input_text: str,
        context: Dict[str, Any],
        classification,
        intent_classification,
    ) -> Dict[str, Any]:
        """Handle task management"""
        if not self.memory_system:
            return {
                "success": False,
                "error": "Memory system not available",
                "handler": "manage_task"
            }

        # Add task to memory with classification
        if hasattr(self.memory_system, 'add_with_classification'):
            result = self.memory_system.add_with_classification(
                input_text,
                **context.get('filters', {})
            )
            return {
                "success": True,
                "data": result,
                "handler": "add_task",
                "message": "Task added to memory"
            }

        return {"success": False, "error": "Task management not available"}

    async def _handle_code_assistant(
        self,
        input_text: str,
        context: Dict[str, Any],
        classification,
        intent_classification,
    ) -> Dict[str, Any]:
        """Handle code-related queries"""
        # Use LLM to analyze/generate code
        if self.llm_client:
            prompt = f"""Analyze or help with this code:
{input_text}

Provide helpful assistance."""
            response = self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}]
            )
            return {
                "success": True,
                "data": {"response": response},
                "handler": "code_assistant"
            }

        return {"success": False, "error": "LLM not available"}

    async def _handle_find_procedure(
        self,
        input_text: str,
        context: Dict[str, Any],
        classification,
        intent_classification,
    ) -> Dict[str, Any]:
        """Handle procedure finding"""
        if self.memory_system and hasattr(self.memory_system, 'get_memories_by_category'):
            procedures = self.memory_system.get_memories_by_category(
                "procedure",
                **context.get('filters', {})
            )
            return {
                "success": True,
                "data": procedures,
                "handler": "find_procedure"
            }

        return await self._handle_search_memory(input_text, context, classification, intent_classification)

    async def _handle_greet(
        self,
        input_text: str,
        context: Dict[str, Any],
        classification,
        intent_classification,
    ) -> Dict[str, Any]:
        """Handle greetings"""
        greetings = [
            "你好！我是 MemScreen AI 助手，很高兴为您服务！",
            "Hello! I'm MemScreen AI assistant, ready to help!",
        ]
        return {
            "success": True,
            "data": {"response": greetings[0]},
            "handler": "greet"
        }

    async def _handle_general_query(
        self,
        input_text: str,
        context: Dict[str, Any],
        classification,
        intent_classification,
    ) -> Dict[str, Any]:
        """Handle general queries with LLM"""
        if self.llm_client:
            # Get context if available
            context_data = None
            if self.memory_system and hasattr(self.memory_system, 'get_context_for_response'):
                context_data = self.memory_system.get_context_for_response(
                    input_text,
                    **context.get('filters', {})
                )

            # Build prompt with context
            prompt = f"User query: {input_text}"
            if context_data:
                prompt += f"\n\nRelevant context:\n{context_data}"

            response = self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}]
            )

            return {
                "success": True,
                "data": {"response": response},
                "handler": "general_query",
                "context_used": context_data is not None
            }

        return {"success": False, "error": "LLM not available"}

    def _metadata_value_for_store(self, value: Any) -> Any:
        """Convert metadata value to Chroma-safe type (str, int, float, bool, None)."""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    async def _store_with_classification(
        self,
        input_text: str,
        classification,
        result: Dict[str, Any]
    ):
        """Store the interaction in memory with classification metadata"""
        try:
            if hasattr(self.memory_system, 'add'):
                raw = {
                    "category": classification.category.value,
                    "confidence": classification.confidence,
                    "subcategories": classification.subcategories,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
                raw.update(classification.metadata)
                metadata = {k: self._metadata_value_for_store(v) for k, v in raw.items()}

                # Add to memory (user_id required by memory API)
                self.memory_system.add(
                    input_text,
                    user_id="api_chat",
                    metadata=metadata,
                )
                logger.debug("[Agent] Interaction stored in memory")
        except Exception as e:
            logger.error(f"[Agent] Error storing to memory: {e}")

    def _update_dispatch_stats(self, classification, intent_classification):
        """Update dispatch statistics"""
        self.dispatch_stats["total_dispatches"] += 1

        if classification:
            cat = classification.category.value
            self.dispatch_stats["category_counts"][cat] = \
                self.dispatch_stats["category_counts"].get(cat, 0) + 1

        if intent_classification:
            intent = intent_classification.intent.value
            self.dispatch_stats["intent_counts"][intent] = \
                self.dispatch_stats["intent_counts"].get(intent, 0) + 1

    def get_dispatch_stats(self) -> Dict[str, Any]:
        """Get dispatch statistics"""
        return self.dispatch_stats.copy()


__all__ = [
    "IntelligentAgent",
    "DispatchRule",
]
