### copyright 2026 jixiangluo    ###
### email:jixiangluo85@gmail.com ###
### rights reserved by author    ###
### time: 2026-02-01             ###
### license: MIT                ###

"""
Entity and Relationship Extractor

Extracts entities and relationships from text to build knowledge graphs.
"""

import json
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

from .models import GraphNode, GraphEdge, NodeType, EdgeType

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Extract entities and relationships from text using LLM.

    Identifies people, places, concepts, and their relationships
    to build a knowledge graph.
    """

    def __init__(self, llm):
        """
        Initialize entity extractor.

        Args:
            llm: Language model instance
        """
        self.llm = llm

    def extract_entities_and_relations(
        self,
        text: str,
        user_id: str = None
    ) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """
        Extract entities and relationships from text.

        Args:
            text: Input text
            user_id: Optional user ID for filtering

        Returns:
            Tuple of (nodes, edges)
        """
        prompt = self._build_extraction_prompt(text)

        try:
            response = self.llm.generate_response(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            # Clean and parse response
            if isinstance(response, str):
                response = response.strip()
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()

            result = json.loads(response)

            # Parse entities
            entities = result.get("entities", [])
            nodes = []
            for entity in entities:
                node = GraphNode(
                    id=entity.get("id", f"{user_id}_{entity.get('name', '').replace(' ', '_')}_{datetime.now().timestamp()}"),
                    label=entity.get("name", "Unknown"),
                    node_type=NodeType(entity.get("type", "entity")),
                    properties={
                        "user_id": user_id,
                        "description": entity.get("description", ""),
                        **entity.get("properties", {})
                    },
                    created_at=datetime.now().isoformat()
                )
                nodes.append(node)

            # Parse relationships
            relationships = result.get("relationships", [])
            edges = []
            for rel in relationships:
                edge = GraphEdge(
                    id=f"{rel['source']}_{rel['target']}_{datetime.now().timestamp()}",
                    source=rel.get("source", ""),
                    target=rel.get("target", ""),
                    edge_type=EdgeType(rel.get("type", "related_to")),
                    properties={
                        "user_id": user_id,
                        "context": rel.get("context", "")
                    },
                    weight=rel.get("weight", 1.0),
                    created_at=datetime.now().isoformat()
                )
                edges.append(edge)

            logger.info(f"Extracted {len(nodes)} entities and {len(edges)} relationships")
            return nodes, edges

        except Exception as e:
            logger.error(f"Failed to extract entities: {e}")
            return [], []

    def _build_extraction_prompt(self, text: str) -> str:
        """Build prompt for entity extraction."""
        return f"""Extract entities and relationships from the following text.

Text: {text}

Please identify:
1. **Entities**: People, places, organizations, concepts, or events mentioned
2. **Relationships**: How these entities relate to each other

Respond in JSON format:
{{
    "entities": [
        {{
            "name": "Entity Name",
            "type": "entity|concept|event",
            "description": "Brief description",
            "properties": {{"key": "value"}}
        }}
    ],
    "relationships": [
        {{
            "source": "Entity Name 1",
            "target": "Entity Name 2",
            "type": "related_to|part_of|caused_by|similar_to",
            "context": "How they are related",
            "weight": 1.0
        }}
    ]
}}

Focus on the most important entities and clear relationships.
Keep descriptions concise but informative."""


__all__ = ["EntityExtractor"]
