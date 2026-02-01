### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""
Graph Store Factory

Factory for creating graph store instances.
"""

from typing import Dict, Any
from .memory_graph import MemoryGraphStore
from .models import GraphConfig


class GraphStoreFactory:
    """Factory for creating graph store instances."""

    _providers = {
        "memory": MemoryGraphStore,
    }

    @classmethod
    def create(cls, provider: str, config: Dict[str, Any] = None):
        """
        Create a graph store instance.

        Args:
            provider: Provider name (e.g., 'memory', 'neo4j')
            config: Provider-specific configuration

        Returns:
            Graph store instance

        Raises:
            ValueError: If provider is not supported
        """
        provider_class = cls._providers.get(provider)

        if provider_class is None:
            raise ValueError(
                f"Unsupported graph store provider: {provider}. "
                f"Supported providers: {list(cls._providers.keys())}"
            )

        return provider_class(config)

    @classmethod
    def register_provider(cls, name: str, provider_class):
        """
        Register a new graph store provider.

        Args:
            name: Provider name
            provider_class: Provider class
        """
        cls._providers[name] = provider_class


__all__ = ["GraphStoreFactory"]
