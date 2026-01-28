"""
Optimized Ollama LLM Implementation with Performance Enhancements
"""

from typing import Dict, List, Optional, Union
import time
from .ollama import OllamaConfig, OllamaLLM
from .performance_config import PerformanceOptimizer, get_optimizer


class OptimizedOllamaConfig(OllamaConfig):
    """Extended Ollama config with performance options"""

    def __init__(
        self,
        # Performance options
        use_case: str = "chat",  # chat, vision, summary, search, chat_fast
        enable_cache: bool = True,
        enable_gpu: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.use_case = use_case
        self.enable_cache = enable_cache
        self.enable_gpu = enable_gpu


class OptimizedOllamaLLM(OllamaLLM):
    """Optimized version of OllamaLLM with caching and performance tracking"""

    def __init__(self, config: Optional[Union[OptimizedOllamaConfig, Dict]] = None):
        # Initialize with optimized config
        if config is None:
            config = OptimizedOllamaConfig()
        elif isinstance(config, dict):
            config = OptimizedOllamaConfig(**config)

        # Initialize parent class
        super().__init__(config)

        # Get performance optimizer
        self.optimizer = get_optimizer()

        # Store use case
        self.use_case = getattr(config, 'use_case', 'chat')

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        response_format=None,
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
        use_cache: Optional[bool] = None,
        **kwargs,
    ):
        """
        Generate response with performance optimizations

        Args:
            messages: List of message dicts
            response_format: Response format
            tools: List of tools
            tool_choice: Tool choice method
            use_cache: Override cache setting
            **kwargs: Additional parameters

        Returns:
            str: Generated response
        """
        # Check cache first
        cache_enabled = use_cache if use_cache is not None else self.optimizer.config.enable_cache

        if cache_enabled:
            # Get optimized params for cache key
            optimized_params = self.optimizer.get_optimized_params(self.use_case)
            cache_key = self.optimizer.get_cache_key(messages, optimized_params)

            # Check cache
            cached_response = self.optimizer.check_cache(cache_key)
            if cached_response is not None:
                print("[Cache] Using cached response")
                return cached_response

        # Start timing
        start_time = time.time()

        # Get optimized parameters
        optimized_params = self.optimizer.get_optimized_params(self.use_case)

        # Merge with any additional kwargs
        options = optimized_params.copy()
        options.update(kwargs.get('options', {}))

        # Build parameters for Ollama
        params = {
            "model": optimized_params["model"],
            "messages": messages,
            "options": options,
        }

        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in ['options']:
                params[key] = value

        # Generate response
        try:
            response = self.client.chat(**params)
            result = self._parse_response(response, tools)
        except Exception as e:
            print(f"[Error] Model inference failed: {e}")
            # Fallback to default model if optimized model fails
            if optimized_params["model"] != self.config.model:
                print(f"[Fallback] Trying default model: {self.config.model}")
                params["model"] = self.config.model
                response = self.client.chat(**params)
                result = self._parse_response(response, tools)
            else:
                raise

        # Track performance
        duration = time.time() - start_time
        self.optimizer.track_performance(duration)

        if self.optimizer.config.enable_monitoring:
            print(f"[Performance] Query completed in {duration:.2f}s using {optimized_params['model']}")

        # Cache the response
        if cache_enabled:
            self.optimizer.add_to_cache(cache_key, result)

        return result

    def generate_response_fast(self, messages: List[Dict[str, str]], **kwargs):
        """
        Generate fast response using smaller model

        Use this for quick previews or less critical queries
        """
        original_use_case = self.use_case
        self.use_case = "chat_fast"

        try:
            result = self.generate_response(messages, **kwargs)
        finally:
            self.use_case = original_use_case

        return result

    def generate_summary(self, text: str, max_length: int = 100) -> str:
        """
        Generate quick summary using optimized settings

        Args:
            text: Text to summarize
            max_length: Maximum summary length

        Returns:
            str: Summary
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Summarize briefly."},
            {"role": "user", "content": f"Summarize in {max_length} chars or less: {text}"}
        ]

        original_use_case = self.use_case
        self.use_case = "summary"

        try:
            result = self.generate_response(messages)
        finally:
            self.use_case = original_use_case

        return result

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        return self.optimizer.get_stats()

    def print_performance_stats(self):
        """Print performance statistics"""
        self.optimizer.print_stats()

    def clear_cache(self):
        """Clear response cache"""
        self.optimizer.cache.clear()
        print("[Cache] Cleared all cached responses")


__all__ = ["OptimizedOllamaConfig", "OptimizedOllamaLLM"]
