import pytest
from agentic_swarm.vectordb.qdrant import InMemoryVectorDB


@pytest.mark.asyncio
async def test_inmemory_create_collection():
    db = InMemoryVectorDB()
    await db.create_collection("test", vector_size=128)
    assert "test" in db._collections


@pytest.mark.asyncio
async def test_inmemory_upsert():
    db = InMemoryVectorDB()
    await db.create_collection("test", vector_size=3)
    
    await db.upsert(
        "test",
        ids=["1", "2"],
        vectors=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        payloads=[{"text": "hello"}, {"text": "world"}],
    )
    
    assert len(db._collections["test"]["points"]) == 2


@pytest.mark.asyncio
async def test_inmemory_search():
    db = InMemoryVectorDB()
    await db.create_collection("test", vector_size=3)
    
    await db.upsert(
        "test",
        ids=["1", "2"],
        vectors=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        payloads=[{"text": "hello"}, {"text": "world"}],
    )
    
    results = await db.search("test", [1.0, 0.0, 0.0], limit=1)
    
    assert len(results) == 1
    assert results[0].id == "1"


@pytest.mark.asyncio
async def test_inmemory_search_with_filter():
    db = InMemoryVectorDB()
    await db.create_collection("test", vector_size=3)
    
    await db.upsert(
        "test",
        ids=["1", "2"],
        vectors=[[1.0, 0.0, 0.0], [0.9, 0.1, 0.0]],
        payloads=[{"category": "a"}, {"category": "b"}],
    )
    
    results = await db.search("test", [1.0, 0.0, 0.0], limit=2, filters={"category": "b"})
    
    assert len(results) == 1
    assert results[0].payload["category"] == "b"


@pytest.mark.asyncio
async def test_inmemory_delete():
    db = InMemoryVectorDB()
    await db.create_collection("test", vector_size=3)
    
    await db.upsert("test", ids=["1"], vectors=[[0.1, 0.2, 0.3]], payloads=[{}])
    await db.delete("test", ["1"])
    
    assert len(db._collections["test"]["points"]) == 0


@pytest.mark.asyncio
async def test_inmemory_get():
    db = InMemoryVectorDB()
    await db.create_collection("test", vector_size=3)
    
    await db.upsert("test", ids=["1"], vectors=[[0.1, 0.2, 0.3]], payloads=[{"text": "hello"}])
    
    results = await db.get("test", ["1"])
    
    assert len(results) == 1
    assert results[0]["payload"]["text"] == "hello"


@pytest.mark.asyncio
async def test_inmemory_delete_collection():
    db = InMemoryVectorDB()
    await db.create_collection("test", vector_size=3)
    await db.delete_collection("test")
    
    assert "test" not in db._collections
