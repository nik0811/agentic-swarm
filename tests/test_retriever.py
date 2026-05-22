import pytest
from agentic_swarm.rag.embedder import MockEmbedder
from agentic_swarm.rag.retriever import Retriever
from agentic_swarm.vectordb.qdrant import InMemoryVectorDB


@pytest.mark.asyncio
async def test_retriever_dense():
    db = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    retriever = Retriever(db, embedder, strategy="dense")
    
    await db.create_collection("test", vector_size=32)
    
    texts = ["Python programming", "JavaScript coding", "Machine learning"]
    for i, text in enumerate(texts):
        vector = await embedder.embed(text)
        await db.upsert("test", [str(i)], [vector], [{"content": text}])
    
    results = await retriever.retrieve("Python", "test", limit=2)
    
    assert len(results) <= 2
    assert all(r.content for r in results)


@pytest.mark.asyncio
async def test_retriever_with_rerank():
    db = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    retriever = Retriever(db, embedder)
    
    await db.create_collection("test", vector_size=32)
    
    texts = ["Python is great", "I love Python programming", "JavaScript is also good"]
    for i, text in enumerate(texts):
        vector = await embedder.embed(text)
        await db.upsert("test", [str(i)], [vector], [{"content": text}])
    
    results = await retriever.retrieve_with_rerank("Python programming", "test", limit=2)
    
    assert len(results) <= 2


@pytest.mark.asyncio
async def test_retriever_empty_collection():
    db = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    retriever = Retriever(db, embedder)
    
    await db.create_collection("empty", vector_size=32)
    
    results = await retriever.retrieve("test query", "empty", limit=5)
    
    assert len(results) == 0
