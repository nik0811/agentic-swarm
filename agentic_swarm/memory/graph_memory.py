"""
Graph Memory - Entity-Relationship Storage

Stores entities and their relationships for knowledge graph-style reasoning.
Uses NetworkX for in-memory graph operations (no external dependencies required).

Features:
- Add entities with properties
- Create relationships between entities
- Traverse relationships (multi-hop)
- Find paths between entities
- Query by entity type or relationship type
- Persist to/from JSON for durability
"""

from __future__ import annotations

import json
import time
from typing import Any

from pydantic import BaseModel


class Entity(BaseModel):
    """An entity in the knowledge graph."""

    id: str
    type: str
    name: str
    properties: dict[str, Any] = {}
    created_at: float = 0.0
    updated_at: float = 0.0

    def __init__(self, **data):
        if "created_at" not in data or data["created_at"] == 0.0:
            data["created_at"] = time.time()
        if "updated_at" not in data or data["updated_at"] == 0.0:
            data["updated_at"] = data["created_at"]
        super().__init__(**data)


class Relationship(BaseModel):
    """A relationship between two entities."""

    source_id: str
    target_id: str
    type: str
    properties: dict[str, Any] = {}
    weight: float = 1.0
    created_at: float = 0.0

    def __init__(self, **data):
        if "created_at" not in data or data["created_at"] == 0.0:
            data["created_at"] = time.time()
        super().__init__(**data)


class GraphMemory:
    """
    Entity-relationship memory for knowledge graph operations.

    Provides graph-based storage and querying without external dependencies.
    Optionally uses NetworkX for advanced graph algorithms if available.

    Usage:
        graph = GraphMemory(agent_id="agent-123")

        # Add entities
        graph.add_entity("user_1", "user", "John", {"age": 30})
        graph.add_entity("lang_1", "language", "Python")

        # Add relationships
        graph.add_relationship("user_1", "lang_1", "prefers")
        graph.add_relationship("user_1", "lang_1", "uses", {"years": 5})

        # Query
        related = graph.get_related("user_1", "prefers")  # ["lang_1"]
        entities = graph.get_entities_by_type("language")  # [Entity(...)]

        # Traverse (multi-hop)
        path = graph.find_path("user_1", "framework_1")  # ["user_1", "lang_1", "framework_1"]
    """

    def __init__(self, agent_id: str, use_networkx: bool = True):
        """
        Initialize graph memory.

        Args:
            agent_id: Owner agent ID for isolation
            use_networkx: Use NetworkX for advanced algorithms (if available)
        """
        self.agent_id = agent_id
        self._entities: dict[str, Entity] = {}
        self._relationships: list[Relationship] = []
        self._adjacency: dict[str, dict[str, list[Relationship]]] = {}

        self._nx_graph = None
        if use_networkx:
            try:
                import networkx as nx

                self._nx_graph = nx.DiGraph()
            except ImportError:
                pass

    def add_entity(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        properties: dict[str, Any] = None,
    ) -> Entity:
        """Add or update an entity in the graph."""
        if entity_id in self._entities:
            entity = self._entities[entity_id]
            entity.name = name
            entity.type = entity_type
            entity.properties = properties or {}
            entity.updated_at = time.time()
        else:
            entity = Entity(
                id=entity_id,
                type=entity_type,
                name=name,
                properties=properties or {},
            )
            self._entities[entity_id] = entity
            self._adjacency[entity_id] = {}

            if self._nx_graph is not None:
                self._nx_graph.add_node(entity_id, type=entity_type, name=name, **entity.properties)

        return entity

    def get_entity(self, entity_id: str) -> Entity | None:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def get_entities_by_type(self, entity_type: str) -> list[Entity]:
        """Get all entities of a specific type."""
        return [e for e in self._entities.values() if e.type == entity_type]

    def remove_entity(self, entity_id: str) -> bool:
        """Remove an entity and all its relationships."""
        if entity_id not in self._entities:
            return False

        del self._entities[entity_id]

        self._relationships = [
            r for r in self._relationships if r.source_id != entity_id and r.target_id != entity_id
        ]

        if entity_id in self._adjacency:
            del self._adjacency[entity_id]
        for adj in self._adjacency.values():
            if entity_id in adj:
                del adj[entity_id]

        if self._nx_graph is not None:
            self._nx_graph.remove_node(entity_id)

        return True

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: dict[str, Any] = None,
        weight: float = 1.0,
    ) -> Relationship | None:
        """Add a relationship between two entities."""
        if source_id not in self._entities or target_id not in self._entities:
            return None

        rel = Relationship(
            source_id=source_id,
            target_id=target_id,
            type=rel_type,
            properties=properties or {},
            weight=weight,
        )
        self._relationships.append(rel)

        if source_id not in self._adjacency:
            self._adjacency[source_id] = {}
        if target_id not in self._adjacency[source_id]:
            self._adjacency[source_id][target_id] = []
        self._adjacency[source_id][target_id].append(rel)

        if self._nx_graph is not None:
            self._nx_graph.add_edge(
                source_id, target_id, type=rel_type, weight=weight, **rel.properties
            )

        return rel

    def get_relationships(
        self, source_id: str = None, target_id: str = None, rel_type: str = None
    ) -> list[Relationship]:
        """Get relationships matching the criteria."""
        results = self._relationships

        if source_id:
            results = [r for r in results if r.source_id == source_id]
        if target_id:
            results = [r for r in results if r.target_id == target_id]
        if rel_type:
            results = [r for r in results if r.type == rel_type]

        return results

    def get_related(
        self, entity_id: str, rel_type: str = None, direction: str = "outgoing"
    ) -> list[str]:
        """
        Get IDs of entities related to the given entity.

        Args:
            entity_id: Source entity ID
            rel_type: Filter by relationship type (optional)
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of related entity IDs
        """
        related = set()

        if direction in ("outgoing", "both"):
            for rel in self._relationships:
                if rel.source_id == entity_id and (rel_type is None or rel.type == rel_type):
                    related.add(rel.target_id)

        if direction in ("incoming", "both"):
            for rel in self._relationships:
                if rel.target_id == entity_id and (rel_type is None or rel.type == rel_type):
                    related.add(rel.source_id)

        return list(related)

    def find_path(self, source_id: str, target_id: str, max_depth: int = 5) -> list[str] | None:
        """
        Find shortest path between two entities.

        Uses NetworkX if available, otherwise BFS.
        """
        if source_id not in self._entities or target_id not in self._entities:
            return None

        if self._nx_graph is not None:
            import networkx as nx

            try:
                return nx.shortest_path(self._nx_graph, source_id, target_id)
            except nx.NetworkXNoPath:
                return None

        visited = {source_id}
        queue = [(source_id, [source_id])]

        while queue:
            current, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            if current == target_id:
                return path

            for neighbor in self.get_related(current, direction="both"):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def traverse(
        self,
        start_id: str,
        rel_types: list[str] = None,
        max_depth: int = 3,
        direction: str = "outgoing",
    ) -> dict[str, list[Entity]]:
        """
        Traverse the graph from a starting entity.

        Returns entities grouped by depth level.
        """
        if start_id not in self._entities:
            return {}

        result: dict[str, list[Entity]] = {}
        visited = {start_id}
        current_level = [start_id]

        for depth in range(1, max_depth + 1):
            next_level = []
            level_entities = []

            for entity_id in current_level:
                for rel_type in rel_types or [None]:
                    related = self.get_related(entity_id, rel_type, direction)
                    for related_id in related:
                        if related_id not in visited:
                            visited.add(related_id)
                            next_level.append(related_id)
                            entity = self._entities.get(related_id)
                            if entity:
                                level_entities.append(entity)

            if level_entities:
                result[f"depth_{depth}"] = level_entities

            current_level = next_level
            if not current_level:
                break

        return result

    def query(
        self,
        entity_type: str = None,
        rel_type: str = None,
        properties: dict[str, Any] = None,
    ) -> list[Entity]:
        """
        Query entities by type, relationship, or properties.

        Args:
            entity_type: Filter by entity type
            rel_type: Filter entities that have this relationship type
            properties: Filter by property values (exact match)
        """
        results = list(self._entities.values())

        if entity_type:
            results = [e for e in results if e.type == entity_type]

        if rel_type:
            has_rel = set()
            for rel in self._relationships:
                if rel.type == rel_type:
                    has_rel.add(rel.source_id)
                    has_rel.add(rel.target_id)
            results = [e for e in results if e.id in has_rel]

        if properties:
            filtered = []
            for entity in results:
                match = all(entity.properties.get(k) == v for k, v in properties.items())
                if match:
                    filtered.append(entity)
            results = filtered

        return results

    def to_dict(self) -> dict:
        """Export graph to dictionary for persistence."""
        return {
            "agent_id": self.agent_id,
            "entities": {eid: e.model_dump() for eid, e in self._entities.items()},
            "relationships": [r.model_dump() for r in self._relationships],
        }

    def to_json(self) -> str:
        """Export graph to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict, use_networkx: bool = True) -> GraphMemory:
        """Load graph from dictionary."""
        graph = cls(agent_id=data.get("agent_id", "unknown"), use_networkx=use_networkx)

        for entity_data in data.get("entities", {}).values():
            graph.add_entity(
                entity_id=entity_data["id"],
                entity_type=entity_data["type"],
                name=entity_data["name"],
                properties=entity_data.get("properties", {}),
            )

        for rel_data in data.get("relationships", []):
            graph.add_relationship(
                source_id=rel_data["source_id"],
                target_id=rel_data["target_id"],
                rel_type=rel_data["type"],
                properties=rel_data.get("properties", {}),
                weight=rel_data.get("weight", 1.0),
            )

        return graph

    @classmethod
    def from_json(cls, json_str: str, use_networkx: bool = True) -> GraphMemory:
        """Load graph from JSON string."""
        return cls.from_dict(json.loads(json_str), use_networkx)

    def clear(self) -> None:
        """Clear all entities and relationships."""
        self._entities.clear()
        self._relationships.clear()
        self._adjacency.clear()

        if self._nx_graph is not None:
            self._nx_graph.clear()

    def get_stats(self) -> dict:
        """Get graph statistics."""
        entity_types = {}
        for entity in self._entities.values():
            entity_types[entity.type] = entity_types.get(entity.type, 0) + 1

        rel_types = {}
        for rel in self._relationships:
            rel_types[rel.type] = rel_types.get(rel.type, 0) + 1

        return {
            "total_entities": len(self._entities),
            "total_relationships": len(self._relationships),
            "entity_types": entity_types,
            "relationship_types": rel_types,
            "using_networkx": self._nx_graph is not None,
        }

    @property
    def entity_count(self) -> int:
        """Number of entities in the graph."""
        return len(self._entities)

    @property
    def relationship_count(self) -> int:
        """Number of relationships in the graph."""
        return len(self._relationships)
