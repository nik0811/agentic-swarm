"""Tests for GraphMemory - Entity-Relationship Storage."""

import pytest

from agentic_swarm.memory.graph_memory import Entity, GraphMemory, Relationship


class TestGraphMemory:
    """Test GraphMemory functionality."""

    def test_create_graph_memory(self):
        """Test creating a graph memory instance."""
        graph = GraphMemory(agent_id="test-agent")
        assert graph.agent_id == "test-agent"
        assert graph.entity_count == 0
        assert graph.relationship_count == 0

    def test_add_entity(self):
        """Test adding entities."""
        graph = GraphMemory(agent_id="test")
        
        entity = graph.add_entity(
            entity_id="user_1",
            entity_type="user",
            name="John Doe",
            properties={"age": 30, "role": "developer"},
        )
        
        assert entity.id == "user_1"
        assert entity.type == "user"
        assert entity.name == "John Doe"
        assert entity.properties["age"] == 30
        assert graph.entity_count == 1

    def test_get_entity(self):
        """Test retrieving entities."""
        graph = GraphMemory(agent_id="test")
        graph.add_entity("e1", "type1", "Entity 1")
        
        entity = graph.get_entity("e1")
        assert entity is not None
        assert entity.name == "Entity 1"
        
        missing = graph.get_entity("nonexistent")
        assert missing is None

    def test_get_entities_by_type(self):
        """Test filtering entities by type."""
        graph = GraphMemory(agent_id="test")
        graph.add_entity("u1", "user", "User 1")
        graph.add_entity("u2", "user", "User 2")
        graph.add_entity("p1", "project", "Project 1")
        
        users = graph.get_entities_by_type("user")
        assert len(users) == 2
        
        projects = graph.get_entities_by_type("project")
        assert len(projects) == 1

    def test_remove_entity(self):
        """Test removing entities."""
        graph = GraphMemory(agent_id="test")
        graph.add_entity("e1", "type1", "Entity 1")
        graph.add_entity("e2", "type1", "Entity 2")
        graph.add_relationship("e1", "e2", "related")
        
        assert graph.entity_count == 2
        assert graph.relationship_count == 1
        
        result = graph.remove_entity("e1")
        assert result is True
        assert graph.entity_count == 1
        assert graph.relationship_count == 0  # Relationship should be removed

    def test_add_relationship(self):
        """Test adding relationships."""
        graph = GraphMemory(agent_id="test")
        graph.add_entity("user_1", "user", "John")
        graph.add_entity("lang_1", "language", "Python")
        
        rel = graph.add_relationship(
            source_id="user_1",
            target_id="lang_1",
            rel_type="prefers",
            properties={"years": 5},
        )
        
        assert rel is not None
        assert rel.source_id == "user_1"
        assert rel.target_id == "lang_1"
        assert rel.type == "prefers"
        assert rel.properties["years"] == 5
        assert graph.relationship_count == 1

    def test_add_relationship_missing_entity(self):
        """Test adding relationship with missing entity."""
        graph = GraphMemory(agent_id="test")
        graph.add_entity("e1", "type1", "Entity 1")
        
        rel = graph.add_relationship("e1", "nonexistent", "related")
        assert rel is None

    def test_get_relationships(self):
        """Test querying relationships."""
        graph = GraphMemory(agent_id="test")
        graph.add_entity("a", "type", "A")
        graph.add_entity("b", "type", "B")
        graph.add_entity("c", "type", "C")
        graph.add_relationship("a", "b", "knows")
        graph.add_relationship("a", "c", "likes")
        graph.add_relationship("b", "c", "knows")
        
        # All relationships
        all_rels = graph.get_relationships()
        assert len(all_rels) == 3
        
        # By source
        from_a = graph.get_relationships(source_id="a")
        assert len(from_a) == 2
        
        # By type
        knows = graph.get_relationships(rel_type="knows")
        assert len(knows) == 2

    def test_get_related(self):
        """Test getting related entities."""
        graph = GraphMemory(agent_id="test")
        graph.add_entity("a", "type", "A")
        graph.add_entity("b", "type", "B")
        graph.add_entity("c", "type", "C")
        graph.add_relationship("a", "b", "knows")
        graph.add_relationship("a", "c", "likes")
        graph.add_relationship("c", "a", "follows")
        
        # Outgoing
        outgoing = graph.get_related("a", direction="outgoing")
        assert set(outgoing) == {"b", "c"}
        
        # Incoming
        incoming = graph.get_related("a", direction="incoming")
        assert incoming == ["c"]
        
        # Both
        both = graph.get_related("a", direction="both")
        assert set(both) == {"b", "c"}
        
        # By type
        knows = graph.get_related("a", rel_type="knows")
        assert knows == ["b"]

    def test_find_path(self):
        """Test finding paths between entities."""
        graph = GraphMemory(agent_id="test", use_networkx=False)
        graph.add_entity("a", "type", "A")
        graph.add_entity("b", "type", "B")
        graph.add_entity("c", "type", "C")
        graph.add_entity("d", "type", "D")
        graph.add_relationship("a", "b", "to")
        graph.add_relationship("b", "c", "to")
        graph.add_relationship("c", "d", "to")
        
        path = graph.find_path("a", "d")
        assert path == ["a", "b", "c", "d"]
        
        # No path
        graph.add_entity("isolated", "type", "Isolated")
        no_path = graph.find_path("a", "isolated")
        assert no_path is None

    def test_traverse(self):
        """Test graph traversal."""
        graph = GraphMemory(agent_id="test")
        graph.add_entity("root", "type", "Root")
        graph.add_entity("child1", "type", "Child 1")
        graph.add_entity("child2", "type", "Child 2")
        graph.add_entity("grandchild", "type", "Grandchild")
        graph.add_relationship("root", "child1", "has")
        graph.add_relationship("root", "child2", "has")
        graph.add_relationship("child1", "grandchild", "has")
        
        result = graph.traverse("root", max_depth=2)
        
        assert "depth_1" in result
        assert len(result["depth_1"]) == 2
        assert "depth_2" in result
        assert len(result["depth_2"]) == 1

    def test_query(self):
        """Test querying entities."""
        graph = GraphMemory(agent_id="test")
        graph.add_entity("u1", "user", "User 1", {"active": True})
        graph.add_entity("u2", "user", "User 2", {"active": False})
        graph.add_entity("p1", "project", "Project 1", {"active": True})
        
        # By type
        users = graph.query(entity_type="user")
        assert len(users) == 2
        
        # By properties
        active = graph.query(properties={"active": True})
        assert len(active) == 2

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        graph = GraphMemory(agent_id="test")
        graph.add_entity("e1", "type1", "Entity 1", {"key": "value"})
        graph.add_entity("e2", "type2", "Entity 2")
        graph.add_relationship("e1", "e2", "related", {"weight": 0.5})
        
        # Serialize
        data = graph.to_dict()
        assert data["agent_id"] == "test"
        assert len(data["entities"]) == 2
        assert len(data["relationships"]) == 1
        
        # Deserialize
        restored = GraphMemory.from_dict(data)
        assert restored.agent_id == "test"
        assert restored.entity_count == 2
        assert restored.relationship_count == 1
        
        entity = restored.get_entity("e1")
        assert entity.properties["key"] == "value"

    def test_to_json_and_from_json(self):
        """Test JSON serialization."""
        graph = GraphMemory(agent_id="test")
        graph.add_entity("e1", "type1", "Entity 1")
        
        json_str = graph.to_json()
        assert '"agent_id": "test"' in json_str
        
        restored = GraphMemory.from_json(json_str)
        assert restored.entity_count == 1

    def test_clear(self):
        """Test clearing the graph."""
        graph = GraphMemory(agent_id="test")
        graph.add_entity("e1", "type1", "Entity 1")
        graph.add_entity("e2", "type1", "Entity 2")
        graph.add_relationship("e1", "e2", "related")
        
        graph.clear()
        
        assert graph.entity_count == 0
        assert graph.relationship_count == 0

    def test_get_stats(self):
        """Test getting graph statistics."""
        graph = GraphMemory(agent_id="test")
        graph.add_entity("u1", "user", "User 1")
        graph.add_entity("u2", "user", "User 2")
        graph.add_entity("p1", "project", "Project 1")
        graph.add_relationship("u1", "p1", "owns")
        graph.add_relationship("u2", "p1", "contributes")
        
        stats = graph.get_stats()
        
        assert stats["total_entities"] == 3
        assert stats["total_relationships"] == 2
        assert stats["entity_types"]["user"] == 2
        assert stats["entity_types"]["project"] == 1
        assert stats["relationship_types"]["owns"] == 1
        assert stats["relationship_types"]["contributes"] == 1
