### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                 ###

"""
Intelligent Model Router for Chat System

This module provides smart model selection based on query complexity,
ensuring fast yet high-quality responses by routing to appropriate models.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """Model size tiers for different complexity levels."""
    TINY = "tiny"        # 270M-1B - Ultra fast, simple queries
    SMALL = "small"      # 1B-3B - Fast, everyday queries
    MEDIUM = "medium"    # 3B-7B - Balanced, complex queries
    LARGE = "large"      # 7B-14B - High quality, reasoning tasks


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    tier: ModelTier
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40

    # Performance characteristics
    avg_latency_ms: int = 0  # Average response latency
    quality_score: float = 0.0  # Quality score (0-1)


@dataclass
class QueryAnalysis:
    """Analysis result of a user query."""
    complexity_score: float  # 0-1, higher is more complex
    tier: ModelTier
    reasoning_required: bool
    creative_required: bool
    factual_required: bool
    keywords: List[str]
    estimated_tokens: int

    # Detected patterns
    is_greeting: bool
    is_question: bool
    is_command: bool
    is_conversational: bool


class ComplexityAnalyzer:
    """
    Analyzes query complexity to determine appropriate model tier.

    Uses multiple heuristics:
    - Length and structure
    - Keyword analysis
    - Question type detection
    - Task complexity indicators
    """

    # Simple queries - use tiny/small models
    SIMPLE_PATTERNS = [
        r"^(||hello|hi|hey)[.!?]*$",
        r"^(||yes|no|ok|)[.!?]*$",
        r"^(||thank)[.!?]*$",
        r"^(||bye|goodbye)[.!?]*$",
    ]

    # Conversational patterns - use small models
    CONVERSATIONAL_PATTERNS = [
        r"(|||how|what)",
        r"(||think|believe)",
        r"(|could|would|might)",
    ]

    # Complex reasoning - use medium/large models
    COMPLEX_PATTERNS = [
        r"(||why|because).{0,5}(|||fail|error|issue)",
        r"(|||explain|analyze|summarize|compare)",
        r"(|||cause|effect|impact)",
        r"(|||step|process|how to)",
        r"(||advantage|disadvantage)",
        r"(||how to solve|what to do)",
        r"(||best|optimal)",
    ]

    # Creative tasks - use medium models
    CREATIVE_PATTERNS = [
        r"(|||write|create|generate).{0,10}(|||||content|story|poem|code)",
        r"(||imagine)",
        r"(||design|plan)",
    ]

    # Factual queries - use small/medium models
    FACTUAL_PATTERNS = [
        r"(||what is|define|)",
        r"(|||how many|how much)",
        r"(||when||time)",
        r"(||where||place)",
        r"(|whose|who||person)",
    ]

    def __init__(self):
        """Initialize the complexity analyzer."""
        self.simple_regex = [re.compile(p, re.IGNORECASE) for p in self.SIMPLE_PATTERNS]
        self.conversational_regex = [re.compile(p, re.IGNORECASE) for p in self.CONVERSATIONAL_PATTERNS]
        self.complex_regex = [re.compile(p, re.IGNORECASE) for p in self.COMPLEX_PATTERNS]
        self.creative_regex = [re.compile(p, re.IGNORECASE) for p in self.CREATIVE_PATTERNS]
        self.factual_regex = [re.compile(p, re.IGNORECASE) for p in self.FACTUAL_PATTERNS]

    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze query complexity and characteristics.

        Args:
            query: User's query string

        Returns:
            QueryAnalysis with detailed metrics
        """
        query_lower = query.lower().strip()
        query_len = len(query)

        # Initialize analysis
        analysis = QueryAnalysis(
            complexity_score=0.0,
            tier=ModelTier.SMALL,
            reasoning_required=False,
            creative_required=False,
            factual_required=False,
            keywords=[],
            estimated_tokens=len(query.split()) * 1.3,  # Rough estimate
            is_greeting=False,
            is_question=False,
            is_command=False,
            is_conversational=False,
        )

        # Detect greeting
        analysis.is_greeting = any(regex.match(query) for regex in self.simple_regex[:4])

        # Detect question
        analysis.is_question = ('?' in query) or any(
            word in query_lower for word in ['', '', '', '', '', 'what', 'where', 'who', 'how', 'why']
        )

        # Detect command
        analysis.is_command = any(prefix in query_lower for prefix in ['!', '', 'help', '', 'search'])

        # Detect conversational
        analysis.is_conversational = any(regex.search(query) for regex in self.conversational_regex)

        # Calculate complexity score
        complexity = 0.0

        # Length factor (0-0.3)
        if query_len < 20:
            complexity += 0.0
        elif query_len < 50:
            complexity += 0.1
        elif query_len < 100:
            complexity += 0.2
        else:
            complexity += 0.3

        # Question marks and structure (0-0.2)
        question_marks = query.count('?') + query.count('')
        complexity += min(question_marks * 0.05, 0.2)

        # Complex patterns (0-0.3)
        complex_matches = sum(1 for regex in self.complex_regex if regex.search(query))
        complexity += min(complex_matches * 0.1, 0.3)
        analysis.reasoning_required = complex_matches > 0

        # Creative patterns (0-0.15)
        creative_matches = sum(1 for regex in self.creative_regex if regex.search(query))
        complexity += min(creative_matches * 0.05, 0.15)
        analysis.creative_required = creative_matches > 0

        # Factual patterns (0-0.1)
        factual_matches = sum(1 for regex in self.factual_regex if regex.search(query))
        complexity += min(factual_matches * 0.03, 0.1)
        analysis.factual_required = factual_matches > 0

        # Sentence complexity (0-0.15)
        sentences = re.split(r'[.]', query)
        if len(sentences) > 2:
            complexity += 0.1
        if any('' in s or ',' in s for s in sentences):
            complexity += 0.05

        # Technical/specific terms (0-0.1)
        technical_keywords = ['api', '', 'code', '', 'algorithm', '', 'data']
        if any(kw in query_lower for kw in technical_keywords):
            complexity += 0.1

        analysis.complexity_score = min(complexity, 1.0)

        # Determine tier based on complexity (adjusted thresholds)
        if analysis.complexity_score < 0.15:
            analysis.tier = ModelTier.TINY
        elif analysis.complexity_score < 0.35:
            analysis.tier = ModelTier.SMALL
        elif analysis.complexity_score < 0.6:
            analysis.tier = ModelTier.MEDIUM
        else:
            analysis.tier = ModelTier.LARGE

        # Extract keywords
        words = re.findall(r'[\w]+', query_lower)
        stop_words = {'', '', '', '', '', 'the', 'is', 'a', 'an', 'of', 'to'}
        analysis.keywords = [w for w in words if len(w) > 1 and w not in stop_words][:5]

        logger.info(f"Query analysis: score={analysis.complexity_score:.2f}, tier={analysis.tier.value}")

        return analysis


class IntelligentModelRouter:
    """
    Intelligent router that selects optimal model based on query analysis.

    Routing strategy:
    1. Analyze query complexity
    2. Select appropriate model tier
    3. Choose best model in tier
    4. Optimize parameters for the model
    """

    def __init__(self, available_models: Optional[List[str]] = None):
        """
        Initialize the model router.

        Args:
            available_models: List of available model names
        """
        self.analyzer = ComplexityAnalyzer()
        self.available_models = available_models or []

        # Default model configurations (can be overridden by available models)
        self.model_configs: Dict[str, ModelConfig] = {}
        self._initialize_default_configs()

        # Map tier to list of models
        self.tier_models: Dict[ModelTier, List[str]] = {
            ModelTier.TINY: [],
            ModelTier.SMALL: [],
            ModelTier.MEDIUM: [],
            ModelTier.LARGE: [],
        }

        if available_models:
            self._categorize_models()

    def _initialize_default_configs(self):
        """Initialize default model configurations."""
        # Tiny models (270M-1B)
        self.model_configs.update({
            "phi3:mini": ModelConfig("phi3:mini", ModelTier.TINY, avg_latency_ms=50, quality_score=0.7),
            "gemma2:2b": ModelConfig("gemma2:2b", ModelTier.TINY, avg_latency_ms=80, quality_score=0.75),
            "qwen2:1.5b": ModelConfig("qwen2:1.5b", ModelTier.TINY, avg_latency_ms=60, quality_score=0.72),
        })

        # Small models (1B-3B) - Default for everyday queries
        self.model_configs.update({
            "qwen2.5vl:3b": ModelConfig("qwen2.5vl:3b", ModelTier.SMALL, avg_latency_ms=150, quality_score=0.85),
            "llama3.2:3b": ModelConfig("llama3.2:3b", ModelTier.SMALL, avg_latency_ms=180, quality_score=0.82),
            "qwen3:1.7b": ModelConfig("qwen3:1.7b", ModelTier.SMALL, avg_latency_ms=120, quality_score=0.80),
            "phi3:3.8b": ModelConfig("phi3:3.8b", ModelTier.SMALL, avg_latency_ms=200, quality_score=0.87),
        })

        # Medium models (3B-7B) - For complex queries
        self.model_configs.update({
            "qwen2.5:7b": ModelConfig("qwen2.5:7b", ModelTier.MEDIUM, avg_latency_ms=400, quality_score=0.92),
            "llama3.1:8b": ModelConfig("llama3.1:8b", ModelTier.MEDIUM, avg_latency_ms=450, quality_score=0.90),
            "gemma2:9b": ModelConfig("gemma2:9b", ModelTier.MEDIUM, avg_latency_ms=500, quality_score=0.91),
            "qwen2:7b": ModelConfig("qwen2:7b", ModelTier.MEDIUM, avg_latency_ms=380, quality_score=0.93),
        })

        # Large models (7B-14B) - For reasoning tasks
        self.model_configs.update({
            "qwen2.5:14b": ModelConfig("qwen2.5:14b", ModelTier.LARGE, avg_latency_ms=800, quality_score=0.96),
            "llama3:70b": ModelConfig("llama3:70b", ModelTier.LARGE, avg_latency_ms=2000, quality_score=0.98),
        })

    def _categorize_models(self):
        """Categorize available models by tier."""
        for model_name in self.available_models:
            # Try to find exact match
            if model_name in self.model_configs:
                config = self.model_configs[model_name]
                self.tier_models[config.tier].append(model_name)
                continue

            # Fuzzy match by size in model name
            model_lower = model_name.lower()
            if any(x in model_lower for x in ['270m', '0.5b', '1b', 'tiny', 'mini']):
                self.tier_models[ModelTier.TINY].append(model_name)
                self.model_configs[model_name] = ModelConfig(
                    model_name, ModelTier.TINY,
                    avg_latency_ms=100, quality_score=0.7
                )
            elif any(x in model_lower for x in ['3b', '1.7b', '1.5b', '2b', 'small']):
                self.tier_models[ModelTier.SMALL].append(model_name)
                self.model_configs[model_name] = ModelConfig(
                    model_name, ModelTier.SMALL,
                    avg_latency_ms=200, quality_score=0.85
                )
            elif any(x in model_lower for x in ['7b', '8b', '9b', 'medium']):
                self.tier_models[ModelTier.MEDIUM].append(model_name)
                self.model_configs[model_name] = ModelConfig(
                    model_name, ModelTier.MEDIUM,
                    avg_latency_ms=500, quality_score=0.92
                )
            else:
                self.tier_models[ModelTier.LARGE].append(model_name)
                self.model_configs[model_name] = ModelConfig(
                    model_name, ModelTier.LARGE,
                    avg_latency_ms=1000, quality_score=0.95
                )

        logger.info(f"Model categorization:")
        for tier, models in self.tier_models.items():
            logger.info(f"  {tier.value}: {len(models)} models - {models[:3]}")

    def route(self, query: str) -> Tuple[str, ModelConfig]:
        """
        Route query to optimal model.

        Args:
            query: User's query

        Returns:
            Tuple of (model_name, model_config)
        """
        # Analyze query
        analysis = self.analyzer.analyze(query)

        # Get models for determined tier
        tier_models = self.tier_models.get(analysis.tier, [])

        # Fallback: if no models in tier, try adjacent tiers
        if not tier_models:
            logger.warning(f"No models in {analysis.tier.value} tier, trying fallback")
            if analysis.tier == ModelTier.TINY:
                tier_models = self.tier_models.get(ModelTier.SMALL, [])
            elif analysis.tier == ModelTier.LARGE:
                tier_models = self.tier_models.get(ModelTier.MEDIUM, [])

            # Still no models? Use all available
            if not tier_models:
                tier_models = self.available_models

        # Select best model in tier
        # Prefer models with better quality/latency balance
        if tier_models:
            # Sort by quality score (higher is better)
            sorted_models = sorted(
                tier_models,
                key=lambda m: self.model_configs.get(m, ModelConfig(m, analysis.tier)).quality_score,
                reverse=True
            )
            selected_model = sorted_models[0]
        else:
            # Ultimate fallback
            selected_model = "qwen2.5vl:3b"

        config = self.model_configs.get(selected_model, ModelConfig(selected_model, analysis.tier))

        logger.info(f"Routed query to {selected_model} ({config.tier.value} tier)")

        return selected_model, config

    def get_optimized_parameters(self, query: str, model_config: ModelConfig) -> Dict:
        """
        Get optimized parameters for the query and model.

        Args:
            query: User's query
            model_config: Selected model configuration

        Returns:
            Dictionary of optimized parameters
        """
        analysis = self.analyzer.analyze(query)

        params = {
            "temperature": model_config.temperature,
            "top_p": model_config.top_p,
            "top_k": model_config.top_k,
            "num_predict": model_config.max_tokens,
            "num_ctx": 4096,  # Context window
            "repeat_penalty": 1.15,
        }

        # Adjust parameters based on query type
        if analysis.is_greeting:
            # Greetings: deterministic, quick
            params["temperature"] = 0.3
            params["num_predict"] = 50
        elif analysis.is_command:
            # Commands: precise, concise
            params["temperature"] = 0.2
            params["num_predict"] = 100
        elif analysis.creative_required:
            # Creative: higher temperature for diversity
            params["temperature"] = 0.9
            params["num_predict"] = 512
        elif analysis.reasoning_required:
            # Reasoning: lower temperature, more tokens
            params["temperature"] = 0.5
            params["num_predict"] = 1024
        elif analysis.factual_required:
            # Factual: very low temperature
            params["temperature"] = 0.2
            params["num_predict"] = 256

        # Adjust based on model tier
        if model_config.tier == ModelTier.TINY:
            # Tiny models: be conservative with output
            params["num_predict"] = min(params["num_predict"], 256)
            params["temperature"] = min(params["temperature"], 0.7)
        elif model_config.tier == ModelTier.LARGE:
            # Large models: can handle more complex outputs
            params["num_predict"] = max(params["num_predict"], 512)

        return params


# Singleton instance
_router_instance: Optional[IntelligentModelRouter] = None


def get_router(available_models: Optional[List[str]] = None) -> IntelligentModelRouter:
    """
    Get the singleton router instance.

    Args:
        available_models: Optional list of available models

    Returns:
        IntelligentModelRouter instance
    """
    global _router_instance

    if _router_instance is None or available_models is not None:
        _router_instance = IntelligentModelRouter(available_models)

    return _router_instance


__all__ = [
    "ModelTier",
    "ModelConfig",
    "QueryAnalysis",
    "ComplexityAnalyzer",
    "IntelligentModelRouter",
    "get_router",
]
