### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                 ###

"""
Intelligent caching system for MemScreen.

This module provides advanced caching with LRU eviction, TTL support,
and intelligent cache key generation.
"""

import hashlib
import json
import logging
import time
from collections import OrderedDict
from typing import Any, Optional, Dict, List, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a single cache entry with metadata."""

    def __init__(self, key: str, value: Any, ttl: Optional[float] = None):
        """
        Initialize a cache entry.

        Args:
            key: Cache key
            value: Cached value
            ttl: Time to live in seconds (None for no expiration)
        """
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.hits = 0
        self.last_access = self.created_at

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl

    def touch(self):
        """Update last access time and increment hit counter."""
        self.last_access = time.time()
        self.hits += 1


class IntelligentCache:
    """
    Intelligent LRU cache with TTL support and smart eviction.

    Features:
    - LRU eviction when cache is full
    - Per-entry TTL support
    - Cache statistics
    - Automatic cleanup of expired entries
    """

    def __init__(self, max_size: int = 1000, default_ttl: Optional[float] = None):
        """
        Initialize the intelligent cache.

        Args:
            max_size: Maximum number of entries in cache
            default_ttl: Default time-to-live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
        }
        self._lock = None  # For thread safety (can use threading.Lock if needed)

    def _generate_key(self, *args, **kwargs) -> str:
        """
        Generate a cache key from function arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            str: Hash-based cache key
        """
        # Create a deterministic string representation
        key_parts = []

        # Add args
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # For complex objects, use hash of JSON representation
                try:
                    key_parts.append(json.dumps(arg, sort_keys=True, default=str))
                except:
                    key_parts.append(str(id(arg)))

        # Add kwargs (sorted for consistency)
        for k in sorted(kwargs.keys()):
            v = kwargs[k]
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}:{v}")
            else:
                try:
                    key_parts.append(f"{k}:{json.dumps(v, sort_keys=True, default=str)}")
                except:
                    key_parts.append(f"{k}:{str(id(v))}")

        # Generate hash of the combined key parts
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        # Move to end to mark as recently used (LRU)
        if key in self._cache:
            entry = self._cache[key]

            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                return None

            # Mark as recently used
            self._cache.move_to_end(key)
            entry.touch()
            self._stats["hits"] += 1
            return entry.value

        self._stats["misses"] += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default_ttl if None)
        """
        # Use default TTL if not specified
        if ttl is None and self.default_ttl is not None:
            ttl = self.default_ttl

        # Create new entry
        entry = CacheEntry(key, value, ttl)

        # Add or update entry
        self._cache[key] = entry
        self._cache.move_to_end(key)

        # Evict oldest entry if cache is full
        if len(self._cache) > self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats["evictions"] += 1

    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._cache.clear()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
        }

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of entries removed
        """
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]
            self._stats["expirations"] += 1

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self._stats,
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_rate": hit_rate,
        }

    def __len__(self) -> int:
        """Return the current cache size."""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the cache and is not expired."""
        if key in self._cache:
            entry = self._cache[key]
            return not entry.is_expired()
        return False


# Global cache instance for search results
_search_cache = IntelligentCache(max_size=1000, default_ttl=300)  # 5 minutes TTL


def cached_search(max_size: int = 1000, ttl: float = 300):
    """
    Decorator for caching search results.

    Args:
        max_size: Maximum cache size
        ttl: Time to live in seconds

    Returns:
        Decorated function with caching
    """
    cache = IntelligentCache(max_size=max_size, default_ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache._generate_key(*args, **kwargs)

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                logger.debug(f"Cache hit for key: {key[:16]}...")
                return result

            # Cache miss - call the function
            logger.debug(f"Cache miss for key: {key[:16]}...")
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(key, result)

            return result

        # Add cache management methods to wrapper
        wrapper.cache_clear = cache.clear
        wrapper.cache_cleanup = cache.cleanup_expired
        wrapper.cache_stats = cache.get_stats

        return wrapper

    return decorator


__all__ = [
    "IntelligentCache",
    "CacheEntry",
    "cached_search",
    "_search_cache",
]
