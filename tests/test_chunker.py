import pytest
from agentic_swarm.rag.chunker import Chunker


def test_chunker_fixed():
    chunker = Chunker(strategy="recursive", chunk_size=50, overlap=10)
    text = "This is a test document with multiple sentences. It has some content."
    
    chunks = chunker.chunk(text)
    
    assert len(chunks) >= 1
    assert all(c.content for c in chunks)


def test_chunker_recursive():
    chunker = Chunker(strategy="recursive", chunk_size=100)
    text = """# Header 1

This is paragraph one. It has multiple sentences.

# Header 2

This is paragraph two. It also has content."""
    
    chunks = chunker.chunk(text)
    
    assert len(chunks) >= 1


def test_chunker_with_metadata():
    chunker = Chunker()
    text = "Hello world"
    
    chunks = chunker.chunk(text, metadata={"source": "test.txt"})
    
    assert chunks[0].metadata.get("source") == "test.txt"


def test_chunker_empty_text():
    chunker = Chunker()
    chunks = chunker.chunk("")
    
    assert len(chunks) <= 1


def test_chunk_index():
    chunker = Chunker(strategy="recursive", chunk_size=100)
    text = "Hello world. This is a test."
    
    chunks = chunker.chunk(text)
    
    assert len(chunks) >= 1
    assert chunks[0].index == 0
