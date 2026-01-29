### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-01-29             ###
### license: MIT                ###

"""
Base Graph Store Interface

Defines the interface for graph storage implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from .models import GraphNode, GraphEdge


class BaseGraphStore(ABC):
    """
    Abstract base class for graph store implementations.

    Provides methods for creating, querying, and managing
    knowledge graphs with entities and relationships.
    """

    @abstractmethod
    def add_node(self, node: GraphNode) -> str:
        """
        Add a node to the graph.

        Args:
            node: GraphNode to add

        Returns:
            Node ID
        """
        pass

    @abstractmethod
    def add_edge(self, edge: GraphEdge) -> str:
        """
        Add an edge to the graph.

        Args:
            edge: GraphEdge to add

        Returns:
            Edge ID
        """
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """
        Get a node by ID.

        Args:
            node_id: Node identifier

        Returns:
            GraphNode if found, None otherwise
        """
        pass

    @abstractmethod
    def get_neighbors(self, node_id: str, edge_type: Optional[str] = None) -> List[Tuple[GraphNode, GraphEdge]]:
        """
        Get neighbors of a node.

        Args:
            node_id: Starting node ID
            edge_type: Optional filter by edge type

        Returns:
            List of (neighbor_node, edge) tuples
        """
        pass

    @abstractmethod
    def search_nodes(self, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[GraphNode]:
        """
        Search for nodes matching a query.

        Args:
            query: Search query
            limit: Maximum results
            filters: Optional metadata filters

        Returns:
            List of matching nodes
        """
        pass

    @abstractmethod
    def find_path(self, source_id: str, target_id: str, max_depth: int = 3) -> List[GraphNode]:
        """
        Find shortest path between two nodes.

        Args:
            source_id: Starting node ID
            target_id: Ending node ID
            max_depth: Maximum path length

        Returns:
            List of nodes forming the path
        """
        pass

    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node and its edges.

        Args:
            node_id: Node to delete

        Returns:
            True if deleted
        """
        pass

    @abstractmethod
    def delete_all(self, filters: Optional[Dict[str, Any]] = None) -> bool:
        """
        Delete all nodes/edges matching filters.

        Args:
            filters: Optional filters

        Returns:
            True if deleted
        """
        pass


__all__ = ["BaseGraphStore"]
