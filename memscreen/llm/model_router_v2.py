### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-06             ###
### license: MIT                 ###

"""
Enhanced model router with 7b model optimization for visual QA.

This module extends the existing IntelligentModelRouter to provide:
- Specialized routing for visual QA tasks
- Context optimization for 7b models
- Parameter tuning for visual reasoning
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

__all__ = [
    "EnhancedModelRouter",
]


class EnhancedModelRouter:
    """
    Enhanced model router with 7b model optimization for visual QA.

    Extends routing decisions to consider:
    - Visual context size
    - Visual reasoning requirements
    - 7b model optimization

    Example:
        ```python
        router = EnhancedModelRouter()

        model, params = router.route_for_vision_qa(
            query="What's on the screen?",
            has_visual_context=True,
            context_size=5
        )
        ```
    """

    def __init__(self, base_router=None):
        """
        Initialize enhanced router.

        Args:
            base_router: Existing IntelligentModelRouter instance
        """
        self.base_router = base_router

        # 7b model configuration
        self.model_configs = {
            "qwen2.5:7b": {
                "quality": 0.92,
                "avg_latency_ms": 400,
                "max_tokens": 2048,
                "specialized_for": ["vision_reasoning", "context_heavy"],
            },
            "qwen2.5vl:3b": {
                "quality": 0.82,
                "avg_latency_ms": 200,
                "max_tokens": 1024,
                "specialized_for": ["quick_vision"],
            },
            "qwen3:1.7b": {
                "quality": 0.75,
                "avg_latency_ms": 120,
                "max_tokens": 512,
                "specialized_for": ["fast_response"],
            },
        }

        logger.info("EnhancedModelRouter initialized")

    def route_for_vision_qa(
        self,
        query: str,
        has_visual_context: bool,
        context_size: int,
    ) -> Tuple[str, Dict]:
        """
        Route query to optimal model for visual QA.

        Decision logic:
        1. Large visual context + reasoning → 7b
        2. Simple visual query → 3b
        3. No visual context → standard routing

        Args:
            query: User query
            has_visual_context: Whether visual context is available
            context_size: Number of visual memories

        Returns:
            Tuple of (model_name, parameters)
        """
        # Check if visual reasoning is needed
        vision_keywords = [
            'recognize', 'detect', 'analyze', 'compare',
            '识别', '检测', '分析', '比较'
        ]

        needs_vision_reasoning = any(
            kw in query.lower() for kw in vision_keywords
        )

        # Routing decision
        if has_visual_context and context_size > 3:
            # Rich visual context → use 7b
            model = "qwen2.5:7b"
            params = {
                "temperature": 0.5,
                "num_predict": 1024,
                "num_ctx": 8192,  # Large context window
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            }
            logger.info(
                f"Routing to 7b model: {model} "
                f"(rich visual context, n={context_size})"
            )

        elif needs_vision_reasoning or context_size > 0:
            # Some visual reasoning needed → use 3b vision model
            model = "qwen2.5vl:3b"
            params = {
                "temperature": 0.3,
                "num_predict": 512,
                "num_ctx": 4096,
                "top_p": 0.85,
            }
            logger.info(
                f"Routing to 3b vision model: {model} "
                f"(visual reasoning, n={context_size})"
            )

        else:
            # No visual context → use fast model
            model = "qwen3:1.7b"
            params = {
                "temperature": 0.3,
                "num_predict": 256,
                "num_ctx": 2048,
                "top_p": 0.8,
            }
            logger.info(f"Routing to fast model: {model} (no visual context)")

        return model, params

    def optimize_parameters_for_vision(
        self,
        model: str,
        query_type: str,
        context_size: int,
    ) -> Dict:
        """
        Optimize parameters for visual QA with specific model.

        Args:
            model: Model name
            query_type: Query type (find, content, action, general)
            context_size: Visual context size

        Returns:
            Optimized parameters dict
        """
        # Base parameters by model
        if "7b" in model:
            base_params = {
                "temperature": 0.5,
                "num_predict": 1024,
                "num_ctx": 8192,
                "top_p": 0.9,
            }
        elif "3b" in model:
            base_params = {
                "temperature": 0.3,
                "num_predict": 512,
                "num_ctx": 4096,
                "top_p": 0.85,
            }
        else:
            base_params = {
                "temperature": 0.3,
                "num_predict": 256,
                "num_ctx": 2048,
                "top_p": 0.8,
            }

        # Adjust based on query type
        if query_type == "content":
            # Content queries need longer output
            base_params["num_predict"] = int(base_params["num_predict"] * 1.2)
        elif query_type == "action":
            # Action queries need moderate output
            base_params["num_predict"] = int(base_params["num_predict"] * 1.0)

        # Adjust based on context size
        if context_size > 5:
            # Large context → reduce output to stay within token limit
            base_params["num_predict"] = int(base_params["num_predict"] * 0.8)

        return base_params

    def estimate_context_tokens(
        self,
        visual_context: List[Dict],
        query: str,
        conversation_history: Optional[List[Dict]] = None,
    ) -> int:
        """
        Estimate total tokens for the context.

        Rough estimation: 1 token ≈ 4 characters.

        Args:
            visual_context: Visual memories
            query: User query
            conversation_history: Chat history

        Returns:
            Estimated token count
        """
        total_chars = len(query)

        # Add visual context
        for mem in visual_context:
            total_chars += len(mem.get('description', ''))
            total_chars += len(mem.get('text_content', ''))

        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                if isinstance(msg, dict):
                    content = msg.get('content', '')
                    total_chars += len(content)

        # Rough token estimate
        estimated_tokens = total_chars / 4

        logger.debug(f"Estimated tokens: {estimated_tokens}")

        return int(estimated_tokens)
