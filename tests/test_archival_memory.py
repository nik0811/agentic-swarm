import pytest
from agentic_swarm.memory.archival_memory import ArchivalMemory
from agentic_swarm.memory.controller import MemoryController
from agentic_swarm.rag.embedder import MockEmbedder
from agentic_swarm.vectordb.qdrant import InMemoryVectorDB


@pytest.mark.asyncio
async def test_archival_store():
    db = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    archival = ArchivalMemory("agent-1", db, embedder)
    
    memory_id = await archival.store("Test memory content")
    
    assert memory_id is not None


@pytest.mark.asyncio
async def test_archival_search():
    db = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    archival = ArchivalMemory("agent-1", db, embedder)
    
    await archival.store("Python programming is fun")
    await archival.store("JavaScript is also popular")
    
    results = await archival.search("Python", limit=1)
    
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_archival_delete():
    db = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    archival = ArchivalMemory("agent-1", db, embedder)
    
    memory_id = await archival.store("To be deleted")
    await archival.delete(memory_id)


@pytest.mark.asyncio
async def test_archival_agent_isolation():
    db = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    
    archival1 = ArchivalMemory("agent-1", db, embedder)
    archival2 = ArchivalMemory("agent-2", db, embedder)
    
    await archival1.store("Agent 1 memory")
    await archival2.store("Agent 2 memory")
    
    results1 = await archival1.search("memory", limit=10)
    results2 = await archival2.search("memory", limit=10)
    
    assert all(r.agent_id == "agent-1" for r in results1)
    assert all(r.agent_id == "agent-2" for r in results2)


@pytest.mark.asyncio
async def test_memory_controller():
    db = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    
    controller = MemoryController(
        agent_id="test-agent",
        name="TestAgent",
        persona="A test agent",
        capabilities=["test"],
        vectordb=db,
        embedder=embedder,
    )
    
    assert controller.core.name == "TestAgent"
    
    controller.push_recall("Hello", role="user")
    assert controller.recall.size == 1
    
    await controller.store_archival("Long term memory")
    results = await controller.search_archival("memory")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_memory_controller_search_all():
    db = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    
    controller = MemoryController(
        agent_id="test",
        name="Test",
        persona="Test",
        vectordb=db,
        embedder=embedder,
    )
    
    controller.push_recall("Python in recall", role="user")
    await controller.store_archival("Python in archival")
    
    results = await controller.search_all("Python")
    
    assert "recall" in results
    assert "archival" in results


def test_memory_controller_stats():
    controller = MemoryController(
        agent_id="test",
        name="Test",
        persona="Test persona",
        capabilities=["a", "b"],
    )
    
    controller.push_recall("msg1", role="user")
    controller.push_recall("msg2", role="assistant")
    
    stats = controller.get_stats()
    
    assert stats["core"]["name"] == "Test"
    assert stats["recall"]["size"] == 2
    assert stats["archival"]["enabled"] is False
