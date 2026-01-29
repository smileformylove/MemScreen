### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-01-29             ###
### license: MIT                ###

"""
Graph Memory Models

Defines data structures for graph-based memory storage.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Types of nodes in the knowledge graph."""
    ENTITY = "entity"  # Person, place, thing
    CONCEPT = "concept"  # Abstract idea
    EVENT = "event"  # Occurrence
    RELATIONSHIP = "relationship"  # Connection between entities


class EdgeType(str, Enum):
    """Types of relationships between nodes."""
    RELATED_TO = "related_to"
    PART_OF = "part_of"
    CAUSED_BY = "caused_by"
    SIMILAR_TO = "similar_to"
    LOCATED_AT = "located_at"
    HAPPENED_DURING = "happened_during"
    MENTIONED_WITH = "mentioned_with"


class GraphNode(BaseModel):
    """Represents a node in the knowledge graph."""
    id: str = Field(..., description="Unique identifier for the node")
    label: str = Field(..., description="Display label for the node")
    node_type: NodeType = Field(..., description="Type of the node")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    embeddings: Optional[List[float]] = Field(None, description="Vector embeddings")
    created_at: str = Field(..., description="Timestamp of creation")

    class Config:
        use_enum_values = True


class GraphEdge(BaseModel):
    """Represents an edge (relationship) between two nodes."""
    id: str = Field(..., description="Unique identifier for the edge")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    edge_type: EdgeType = Field(..., description="Type of relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    weight: float = Field(default=1.0, description="Strength of relationship")
    created_at: str = Field(..., description="Timestamp of creation")

    class Config:
        use_enum_values = True


class GraphConfig(BaseModel):
    """Configuration for graph store."""
    provider: str = Field(default="memory", description="Graph store provider")
    config: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific config")


__all__ = ["NodeType", "EdgeType", "GraphNode", "GraphEdge", "GraphConfig"]
