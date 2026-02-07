### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Vision QA prompt builder for optimized visual question-answering.

This module provides specialized prompt building for visual QA tasks,
optimized for 7b models with structured context formatting.
"""

import logging
from typing import Dict, List, Optional, Literal

logger = logging.getLogger(__name__)

__all__ = [
    "VisionQAPromptBuilder",
]


class VisionQAPromptBuilder:
    """
    Build optimized prompts for visual question-answering.

    Features:
    - Query type classification (find, content, action, general)
    - Structured visual context formatting
    - Context optimization for 7b models (3000-4000 tokens)
    - Scene-based grouping

    Example:
        ```python
        builder = VisionQAPromptBuilder()

        messages = builder.build_prompt_for_7b(
            query="Where is the red button?",
            visual_context=[...],
            conversation_history=[...]
        )
        ```
    """

    def __init__(self):
        """Initialize the prompt builder."""
        logger.info("VisionQAPromptBuilder initialized")

    def build_prompt_for_7b(
        self,
        query: str,
        visual_context: List[Dict],
        conversation_history: List[Dict],
    ) -> List[Dict]:
        """
        Build optimized prompt for 7b model.

        Args:
            query: User query
            visual_context: Retrieved visual memories
            conversation_history: Recent conversation history

        Returns:
            List of message dicts for LLM
        """
        # Classify query type
        query_type = self._classify_query_type(query)

        # Select relevant visual context
        relevant_context = self._select_relevant_visual_context(
            visual_context, query, query_type
        )

        # Build system prompt
        system_prompt = self._build_system_prompt(query_type)

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]

        # Add visual context if available
        if relevant_context:
            formatted_visual = self._format_visual_context(
                relevant_context, query_type
            )
            messages.append({
                "role": "user",
                "content": f"[Visual Context]\n\n{formatted_visual}"
            })

        # Add conversation history (recent 3 rounds = 6 messages)
        for msg in conversation_history[-6:]:
            messages.append(msg)

        # Add current query
        messages.append({"role": "user", "content": query})

        return messages

    def _classify_query_type(self, query: str) -> str:
        """
        Classify query type for specialized handling.

        Args:
            query: User query

        Returns:
            Query type: 'find', 'content', 'action', 'general'
        """
        query_lower = query.lower()

        # Find/locate queries
        if any(kw in query_lower for kw in ['find', 'where', 'locate', '位置', '在哪']):
            return 'find'

        # Content/what queries
        elif any(kw in query_lower for kw in ['what', 'content', 'text', '什么', '内容']):
            return 'content'

        # Action/how queries
        elif any(kw in query_lower for kw in ['how', 'do', 'did', '操作', '怎么', '如何']):
            return 'action'

        # General
        else:
            return 'general'

    def _select_relevant_visual_context(
        self,
        visual_context: List[Dict],
        query: str,
        query_type: str,
    ) -> List[Dict]:
        """
        Select most relevant visual context for query.

        Args:
            visual_context: All retrieved visual memories
            query: User query
            query_type: Classified query type

        Returns:
            Filtered and ranked visual context
        """
        if not visual_context:
            return []

        # Sort by score (relevance)
        sorted_context = sorted(
            visual_context,
            key=lambda x: x.get('score', 0),
            reverse=True
        )

        # Select top results based on query type
        if query_type == 'find':
            # For finding objects, prioritize recent items
            limit = 5
        elif query_type == 'content':
            # For content queries, need more context
            limit = 8
        else:
            limit = 5

        return sorted_context[:limit]

    def _build_system_prompt(self, query_type: str) -> str:
        """
        Build system prompt optimized for query type.

        Args:
            query_type: Query type

        Returns:
            System prompt string
        """
        base_prompt = """You are MemScreen, an AI assistant with visual memory capabilities.

You can see and remember what was on the user's screen through screenshots and recordings.

When answering questions about visual content:
- Be specific about what you saw
- Include timestamps when relevant
- Reference multiple screenshots if needed
- If uncertain, say what you recall and your confidence level
- Always base your answers on the provided visual context"""

        # Add type-specific instructions
        type_instructions = {
            'find': """

For "find" queries:
- Look for the object's location on screen
- Describe surrounding context
- Mention when you last saw it
- Use spatial terms (left, right, top, bottom)""",

            'content': """

For "content" queries:
- Quote text you saw on screen
- Preserve important details
- Summarize longer content accurately""",

            'action': """

For "action" queries:
- Describe the steps you observed
- Mention the application being used
- Include any relevant UI elements""",

            'general': """

Answer naturally based on what you observed in the visual context.""",
        }

        specific = type_instructions.get(query_type, type_instructions['general'])

        return base_prompt + specific

    def _format_visual_context(
        self,
        context: List[Dict],
        query_type: str,
    ) -> str:
        """
        Format visual context for LLM.

        Uses structured format with XML-like tags for clarity.

        Args:
            context: Visual context items
            query_type: Query type

        Returns:
            Formatted context string
        """
        sections = []

        # Group by granularity
        by_granularity = self._group_by_granularity(context)

        # Scene-level information
        if 'scene' in by_granularity:
            sections.append("## Scene-Level Context")
            for item in by_granularity['scene'][:2]:  # Max 2 scenes
                desc = item.get('description', 'No description')
                timestamp = item.get('timestamp', 'Unknown time')
                sections.append(f"• [{timestamp}] {desc}")
            sections.append("")  # Empty line

        # Text-level information (for content queries)
        if query_type in ['content', 'general'] and 'text' in by_granularity:
            sections.append("## Text Content")
            for text_item in by_granularity['text'][:3]:  # Max 3 text items
                text = text_item.get('text_content', '')
                if text:
                    # Truncate long text
                    if len(text) > 200:
                        text = text[:200] + "..."
                    sections.append(f"• \"{text}\"")
            sections.append("")

        return "\n".join(sections)

    def _group_by_granularity(self, context: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group context items by granularity level.

        Args:
            context: All context items

        Returns:
            Dict with keys 'scene', 'text', etc.
        """
        grouped = {}

        for item in context:
            granularity = item.get('granularity', 'unknown')
            if granularity not in grouped:
                grouped[granularity] = []
            grouped[granularity].append(item)

        return grouped


# Convenience function
def build_vision_qa_prompt(
    query: str,
    visual_context: List[Dict],
    conversation_history: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    Convenience function to build vision QA prompt.

    Args:
        query: User query
        visual_context: Retrieved visual memories
        conversation_history: Conversation history (optional)

    Returns:
        List of message dicts
    """
    if conversation_history is None:
        conversation_history = []

    builder = VisionQAPromptBuilder()
    return builder.build_prompt_for_7b(
        query=query,
        visual_context=visual_context,
        conversation_history=conversation_history,
    )
