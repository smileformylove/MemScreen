"""
Model Performance Optimization Configuration
Provides optimized settings for different use cases
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
import time


@dataclass
class ModelPerformanceConfig:
    """Configuration for optimized model performance"""

    # Model selection
    model_chat: str = "qwen2.5vl:3b"
    model_chat_fast: str = "qwen2.5vl:0.5b"  # Faster but less accurate
    model_vision: str = "qwen2.5vl:3b"
    model_embedding: str = "nomic-embed-text"

    # Performance parameters
    max_tokens_chat: int = 512  # Reduced from 2000
    max_tokens_vision: int = 256  # For image analysis
    max_tokens_summary: int = 128  # For quick summaries

    # Sampling parameters
    temperature_chat: float = 0.7  # Increased for faster convergence
    temperature_fast: float = 0.5  # Balanced
    top_p: float = 0.9  # Increased for diversity
    top_k: int = 20  # Increased from 1

    # Context optimization
    num_ctx: int = 2048  # Context window size
    num_batch: int = 512  # Batch size for processing
    num_gpu: int = 1  # Number of GPU layers (0 = CPU only)
    num_thread: int = 4  # Number of CPU threads

    # Caching
    enable_cache: bool = True
    cache_ttl: int = 3600  # Cache TTL in seconds (1 hour)
    cache_max_size: int = 100  # Maximum cached responses

    # Streaming
    enable_streaming: bool = False  # Enable for faster feedback

    # Quantization (if supported)
    quantization: Optional[str] = "q4_0"  # Options: q4_0, q4_1, q5_0, q5_1, q8_0

    # Performance monitoring
    enable_monitoring: bool = True
    log_slow_queries: bool = True
    slow_query_threshold: float = 5.0  # Log queries slower than 5 seconds


class PerformanceOptimizer:
    """Optimize model performance based on use case"""

    def __init__(self, config: Optional[ModelPerformanceConfig] = None):
        self.config = config or ModelPerformanceConfig()
        self.cache = {}
        self.performance_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "slow_queries": 0,
            "total_time": 0.0,
        }

    def get_optimized_params(self, use_case: str) -> Dict:
        """
        Get optimized parameters for specific use case

        Args:
            use_case: Type of query (chat, vision, summary, search)

        Returns:
            Dict with optimized parameters
        """
        configs = {
            "chat": {
                "model": self.config.model_chat,
                "num_predict": self.config.max_tokens_chat,
                "temperature": self.config.temperature_chat,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "num_ctx": self.config.num_ctx,
                "num_gpu": self.config.num_gpu,
                "num_thread": self.config.num_thread,
            },
            "chat_fast": {
                "model": self.config.model_chat_fast,
                "num_predict": self.config.max_tokens_summary,
                "temperature": self.config.temperature_fast,
                "top_p": 0.8,
                "top_k": 10,
                "num_ctx": 1024,
                "num_gpu": self.config.num_gpu,
                "num_thread": self.config.num_thread,
            },
            "vision": {
                "model": self.config.model_vision,
                "num_predict": self.config.max_tokens_vision,
                "temperature": 0.3,
                "top_p": 0.8,
                "num_ctx": 1024,
                "num_gpu": self.config.num_gpu,
            },
            "summary": {
                "model": self.config.model_chat_fast,
                "num_predict": self.config.max_tokens_summary,
                "temperature": 0.5,
                "top_p": 0.9,
                "num_ctx": 512,
                "num_gpu": 0,  # CPU is fine for summaries
            },
            "search": {
                "model": self.config.model_chat_fast,
                "num_predict": 64,  # Very short responses
                "temperature": 0.3,
                "top_p": 0.7,
                "num_ctx": 512,
                "num_gpu": 0,
            },
        }

        return configs.get(use_case, configs["chat"])

    def get_cache_key(self, messages: List[Dict], params: Dict) -> str:
        """Generate cache key from messages and parameters"""
        import hashlib
        import json

        # Create a deterministic string representation
        content = json.dumps({"messages": messages, "params": params}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def check_cache(self, cache_key: str) -> Optional[str]:
        """Check if response is cached"""
        if not self.config.enable_cache:
            return None

        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            # Check if cache is still valid
            if time.time() - cached_data["timestamp"] < self.config.cache_ttl:
                self.performance_stats["cache_hits"] += 1
                return cached_data["response"]
            else:
                # Remove expired cache
                del self.cache[cache_key]

        return None

    def add_to_cache(self, cache_key: str, response: str):
        """Add response to cache"""
        if not self.config.enable_cache:
            return

        # Implement LRU cache if size exceeds limit
        if len(self.cache) >= self.config.cache_max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]

        self.cache[cache_key] = {
            "response": response,
            "timestamp": time.time(),
        }

    def track_performance(self, duration: float):
        """Track performance metrics"""
        self.performance_stats["total_requests"] += 1
        self.performance_stats["total_time"] += duration

        if duration > self.config.slow_query_threshold:
            self.performance_stats["slow_queries"] += 1
            if self.config.log_slow_queries:
                print(f"[Performance] Slow query detected: {duration:.2f}s")

    def get_stats(self) -> Dict:
        """Get performance statistics"""
        stats = self.performance_stats.copy()

        if stats["total_requests"] > 0:
            stats["avg_time"] = stats["total_time"] / stats["total_requests"]
            stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_requests"]
        else:
            stats["avg_time"] = 0.0
            stats["cache_hit_rate"] = 0.0

        return stats

    def print_stats(self):
        """Print performance statistics"""
        stats = self.get_stats()
        print("\n" + "="*50)
        print("📊 Model Performance Statistics")
        print("="*50)
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Cache Hits: {stats['cache_hits']}")
        print(f"Cache Hit Rate: {stats['cache_hit_rate']:.1%}")
        print(f"Average Time: {stats['avg_time']:.2f}s")
        print(f"Slow Queries: {stats['slow_queries']}")
        print(f"Cache Size: {len(self.cache)}")
        print("="*50 + "\n")


# Global optimizer instance
_optimizer = None


def get_optimizer() -> PerformanceOptimizer:
    """Get global optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    return _optimizer


def reset_optimizer():
    """Reset optimizer (for testing)"""
    global _optimizer
    _optimizer = None
