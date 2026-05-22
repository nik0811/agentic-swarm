"""
RAG Pipeline Example

This example shows how to use the RAG pipeline for document retrieval.
"""
import asyncio
from agentic_swarm.rag import RAGPipeline, MockEmbedder, Chunker
from agentic_swarm.vectordb import InMemoryVectorDB


SAMPLE_DOCUMENTS = [
    """
    # Python Programming Guide
    
    Python is a high-level programming language known for its simplicity and readability.
    It supports multiple programming paradigms including procedural, object-oriented, and functional programming.
    
    ## Key Features
    - Easy to learn and use
    - Extensive standard library
    - Large ecosystem of packages
    - Cross-platform compatibility
    """,
    """
    # Machine Learning Basics
    
    Machine learning is a subset of artificial intelligence that enables systems to learn from data.
    Common types include supervised learning, unsupervised learning, and reinforcement learning.
    
    ## Popular Libraries
    - TensorFlow
    - PyTorch
    - scikit-learn
    - Keras
    """,
    """
    # Web Development with Python
    
    Python is widely used for web development with frameworks like Django and Flask.
    Django provides a full-featured framework while Flask offers a lightweight alternative.
    
    ## Best Practices
    - Use virtual environments
    - Follow PEP 8 style guide
    - Write tests for your code
    - Use type hints
    """,
]


async def main():
    vectordb = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    chunker = Chunker(strategy="recursive", chunk_size=200)
    
    rag = RAGPipeline(
        vectordb=vectordb,
        embedder=embedder,
        chunker=chunker,
        default_collection="knowledge_base",
    )
    
    print("=== Ingesting Documents ===")
    total_chunks = 0
    for i, doc in enumerate(SAMPLE_DOCUMENTS):
        chunks = await rag.ingest(doc, metadata={"doc_id": i})
        total_chunks += chunks
        print(f"Document {i+1}: {chunks} chunks")
    print(f"Total chunks: {total_chunks}")
    
    print("\n=== Querying the RAG Pipeline ===")
    
    queries = [
        "What is Python?",
        "How do I do machine learning?",
        "What web frameworks are available?",
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        result = await rag.query(query, limit=2)
        print(f"Found {result.num_chunks} relevant chunks")
        print(f"Context preview: {result.context[:200]}...")
        print(f"Sources: {result.sources}")


if __name__ == "__main__":
    asyncio.run(main())
