import pytest
from agentic_swarm.rag.pipeline import RAGPipeline
from agentic_swarm.rag.embedder import MockEmbedder
from agentic_swarm.rag.chunker import Chunker
from agentic_swarm.vectordb.qdrant import InMemoryVectorDB


@pytest.mark.asyncio
async def test_rag_ingest():
    db = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    chunker = Chunker(chunk_size=50)
    
    rag = RAGPipeline(db, embedder, chunker)
    
    text = "This is a test document. " * 20
    num_chunks = await rag.ingest(text, collection="test")
    
    assert num_chunks > 0


@pytest.mark.asyncio
async def test_rag_query():
    db = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    
    rag = RAGPipeline(db, embedder)
    
    await rag.ingest("Python is a programming language.", collection="test")
    await rag.ingest("Machine learning uses Python.", collection="test")
    
    result = await rag.query("What is Python?", collection="test", limit=2)
    
    assert result.context
    assert result.num_chunks > 0


@pytest.mark.asyncio
async def test_rag_with_metadata():
    db = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    
    rag = RAGPipeline(db, embedder)
    
    await rag.ingest("Test content", collection="test", metadata={"source": "test.txt"})
    
    result = await rag.query("Test", collection="test")
    
    assert len(result.sources) > 0


@pytest.mark.asyncio
async def test_rag_delete_collection():
    db = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    
    rag = RAGPipeline(db, embedder)
    
    await rag.ingest("Test", collection="to_delete")
    await rag.delete_collection("to_delete")
    
    assert "to_delete" not in db._collections
