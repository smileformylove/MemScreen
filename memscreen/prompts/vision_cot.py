### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Vision Chain-of-Thought for step-by-step visual reasoning.

This module implements CoT (Chain-of-Thought) prompting for visual QA,
guiding 7b models to reason through visual evidence systematically.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

__all__ = [
    "VisionChainOfThought",
]


class VisionChainOfThought:
    """
    Implement Chain-of-Thought reasoning for visual QA.

    Guides models to:
    1. Analyze the query
    2. Recall visual evidence
    3. Analyze the evidence
    4. Formulate an answer

    Example:
        ```python
        cot = VisionChainOfThought()

        messages = cot.build_cot_prompt(
            query="What was on the user's screen?",
            visual_context=[...]
        )
        ```
    """

    def __init__(self):
        """Initialize the CoT builder."""
        logger.info("VisionChainOfThought initialized")

    def build_cot_prompt(
        self,
        query: str,
        visual_context: List[Dict],
    ) -> List[Dict]:
        """
        Build Chain-of-Thought prompt for visual QA.

        Args:
            query: User query
            visual_context: Retrieved visual memories

        Returns:
            List of message dicts
        """
        # Format visual evidence
        evidence = self._format_visual_evidence(visual_context)

        # Build CoT prompt
        cot_prompt = f"""Let's think step by step to answer: "{query}"

**Step 1: Understand the Query**
The user is asking about: {self._analyze_query(query)}

**Step 2: Recall Visual Evidence**
Based on my visual memory, I saw:

{evidence}

**Step 3: Analyze the Evidence**
{self._generate_analysis_questions()}

**Step 4: Formulate Answer**
Based on the visual evidence above, let me combine the information to answer the question.

Answer:"""

        return [
            {
                "role": "system",
                "content": "You are a careful visual analyst. Think step by step."
            },
            {
                "role": "user",
                "content": cot_prompt
            }
        ]

    def _analyze_query(self, query: str) -> str:
        """
        Analyze what the user is asking.

        Args:
            query: User query

        Returns:
            Query analysis string
        """
        query_lower = query.lower()

        if 'where' in query_lower or 'find' in query_lower:
            return "finding the location of something"
        elif 'what' in query_lower or 'content' in query_lower:
            return "understanding what content was displayed"
        elif 'how' in query_lower or 'do' in query_lower:
            return "understanding an action or process"
        else:
            return "general information about the visual content"

    def _format_visual_evidence(self, context: List[Dict]) -> str:
        """
        Format visual evidence for CoT reasoning.

        Args:
            context: Visual context items

        Returns:
            Formatted evidence string
        """
        if not context:
            return "No visual evidence available."

        evidence_parts = []

        for i, item in enumerate(context[:5], 1):  # Max 5 evidence items
            evidence_part = f"**Evidence {i}:**\n"

            # Add timestamp
            if 'timestamp' in item:
                evidence_part += f"  - Time: {item['timestamp']}\n"

            # Add description
            if 'description' in item:
                evidence_part += f"  - Scene: {item['description']}\n"

            # Add text content
            if 'text_content' in item:
                text_preview = item['text_content'][:100]
                if len(item['text_content']) > 100:
                    text_preview += "..."
                evidence_part += f"  - Text: \"{text_preview}\"\n"

            # Add objects if available
            if 'objects' in item and item['objects']:
                objects = ", ".join([
                    obj.get('class', 'object')
                    for obj in item['objects'][:3]
                ])
                evidence_part += f"  - Objects: {objects}\n"

            evidence_parts.append(evidence_part)

        return "\n".join(evidence_parts)

    def _generate_analysis_questions(self) -> str:
        """
        Generate guiding questions for evidence analysis.

        Returns:
            Questions string
        """
        questions = [
            "- What are the key visual elements present?",
            "- Do the screenshots show a consistent scene or changes over time?",
            "- Is there text that directly answers the question?",
            "- Are there any notable patterns or sequences?",
        ]

        return "\n".join(questions)

    def compress_context_for_7b(
        self,
        visual_context: List[Dict],
        max_tokens: int = 3000,
    ) -> List[Dict]:
        """
        Compress visual context to fit 7b model's context window.

        Args:
            visual_context: All visual context
            max_tokens: Target token count

        Returns:
            Compressed context
        """
        # Estimate tokens (rough approximation: 1 token ≈ 4 chars)
        total_chars = sum(
            len(str(item.get('description', ''))) +
            len(str(item.get('text_content', '')))
            for item in visual_context
        )
        estimated_tokens = total_chars / 4

        if estimated_tokens <= max_tokens:
            return visual_context

        # Need to compress: keep only top items by score
        compression_ratio = max_tokens / estimated_tokens
        keep_count = max(1, int(len(visual_context) * compression_ratio))

        logger.info(
            f"Compressing context: {len(visual_context)} → {keep_count} items"
        )

        # Sort by score and keep top items
        sorted_context = sorted(
            visual_context,
            key=lambda x: x.get('score', 0),
            reverse=True
        )

        return sorted_context[:keep_count]


# Convenience function
def build_vision_cot_prompt(
    query: str,
    visual_context: List[Dict],
) -> List[Dict]:
    """
    Convenience function to build vision CoT prompt.

    Args:
        query: User query
        visual_context: Retrieved visual memories

    Returns:
        List of message dicts
    """
    cot = VisionChainOfThought()
    return cot.build_cot_prompt(
        query=query,
        visual_context=visual_context,
    )
