### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-01-29             ###
### license: MIT                ###

"""
In-Memory Graph Store Implementation

Simple graph store implementation using NetworkX or in-memory data structures.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict, deque

from .base import BaseGraphStore
from .models import GraphNode, GraphEdge, NodeType, EdgeType

logger = logging.getLogger(__name__)


class MemoryGraphStore(BaseGraphStore):
    """
    In-memory graph store implementation.

    Stores nodes and edges in memory with fast lookup.
    Suitable for development and small to medium datasets.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize in-memory graph store.

        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.adjacency: Dict[str, List[Tuple[str, str]]] = defaultdict(list)  # node_id -> [(neighbor_id, edge_id)]

    def add_node(self, node: GraphNode) -> str:
        """Add a node to the graph."""
        if not node.id:
            node.id = str(uuid.uuid4())

        if not node.created_at:
            node.created_at = datetime.now().isoformat()

        self.nodes[node.id] = node
        logger.debug(f"Added node: {node.id} - {node.label}")
        return node.id

    def add_edge(self, edge: GraphEdge) -> str:
        """Add an edge to the graph."""
        if not edge.id:
            edge.id = str(uuid.uuid4())

        if not edge.created_at:
            edge.created_at = datetime.now().isoformat()

        # Validate nodes exist
        if edge.source not in self.nodes:
            logger.warning(f"Source node {edge.source} not found, skipping edge")
            return None

        if edge.target not in self.nodes:
            logger.warning(f"Target node {edge.target} not found, skipping edge")
            return None

        self.edges[edge.id] = edge
        self.adjacency[edge.source].append((edge.target, edge.id))

        # For undirected graphs, also add reverse edge
        # Uncomment if you want bidirectional relationships:
        # self.adjacency[edge.target].append((edge.source, edge.id))

        logger.debug(f"Added edge: {edge.source} -> {edge.target} ({edge.edge_type})")
        return edge.id

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str, edge_type: Optional[str] = None) -> List[Tuple[GraphNode, GraphEdge]]:
        """Get neighbors of a node."""
        if node_id not in self.adjacency:
            return []

        neighbors = []
        for neighbor_id, edge_id in self.adjacency[node_id]:
            edge = self.edges.get(edge_id)
            if edge and (edge_type is None or edge.edge_type == edge_type):
                neighbor = self.nodes.get(neighbor_id)
                if neighbor:
                    neighbors.append((neighbor, edge))

        return neighbors

    def search_nodes(self, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[GraphNode]:
        """
        Search for nodes matching a query.

        Simple text-based search on node labels and properties.
        """
        query_lower = query.lower()
        results = []

        for node in self.nodes.values():
            # Search in label
            if query_lower in node.label.lower():
                if filters is None or all(
                    node.properties.get(k) == v for k, v in filters.items()
                ):
                    results.append(node)
                    continue

            # Search in properties
            for key, value in node.properties.items():
                if isinstance(value, str) and query_lower in value.lower():
                    if filters is None or all(
                        node.properties.get(k) == v for k, v in filters.items()
                    ):
                        results.append(node)
                        break

        return results[:limit]

    def find_path(self, source_id: str, target_id: str, max_depth: int = 3) -> List[GraphNode]:
        """
        Find shortest path between two nodes using BFS.

        Args:
            source_id: Starting node ID
            target_id: Target node ID
            max_depth: Maximum search depth

        Returns:
            List of nodes forming the path, empty if no path found
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return []

        # BFS to find shortest path
        queue = deque([(source_id, [source_id])])
        visited = {source_id}

        while queue:
            current_id, path = queue.popleft()

            if current_id == target_id:
                return [self.nodes[node_id] for node_id in path]

            if len(path) >= max_depth + 1:
                continue

            for neighbor_id, _ in self.adjacency[current_id]:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return []  # No path found

    def delete_node(self, node_id: str) -> bool:
        """Delete a node and its edges."""
        if node_id not in self.nodes:
            return False

        # Delete all edges connected to this node
        edges_to_delete = []
        for edge_id, edge in self.edges.items():
            if edge.source == node_id or edge.target == node_id:
                edges_to_delete.append(edge_id)

        for edge_id in edges_to_delete:
            del self.edges[edge_id]

        # Remove from adjacency lists
        if node_id in self.adjacency:
            del self.adjacency[node_id]

        for node_id_key in self.adjacency:
            self.adjacency[node_id_key] = [
                (nid, eid) for nid, eid in self.adjacency[node_id_key]
                if nid != node_id
            ]

        # Delete node
        del self.nodes[node_id]

        logger.debug(f"Deleted node: {node_id}")
        return True

    def delete_all(self, filters: Optional[Dict[str, Any]] = None) -> bool:
        """Delete all nodes/edges matching filters."""
        if filters is None:
            # Delete everything
            self.nodes.clear()
            self.edges.clear()
            self.adjacency.clear()
            logger.info("Cleared all nodes and edges")
            return True

        # Delete nodes matching filters
        nodes_to_delete = []
        for node_id, node in self.nodes.items():
            if all(node.properties.get(k) == v for k, v in filters.items()):
                nodes_to_delete.append(node_id)

        for node_id in nodes_to_delete:
            self.delete_node(node_id)

        logger.info(f"Deleted {len(nodes_to_delete)} nodes matching filters")
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "nodes_by_type": self._count_nodes_by_type(),
            "edges_by_type": self._count_edges_by_type(),
        }

    def _count_nodes_by_type(self) -> Dict[str, int]:
        """Count nodes by type."""
        counts = defaultdict(int)
        for node in self.nodes.values():
            counts[node.node_type] += 1
        return dict(counts)

    def _count_edges_by_type(self) -> Dict[str, int]:
        """Count edges by type."""
        counts = defaultdict(int)
        for edge in self.edges.values():
            counts[edge.edge_type] += 1
        return dict(counts)


__all__ = ["MemoryGraphStore"]
