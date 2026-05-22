"""
Agentic Swarm — Vector Database + Persistent Storage Example
============================================================

This example demonstrates:
1. Vector database for semantic search (InMemoryVectorDB or Qdrant)
2. Persistent storage for agent state and data
3. RAG pipeline with document ingestion
4. Archival memory with vector-indexed long-term storage
5. Data persistence across sessions

Run: python examples/vectordb_persistent.py
"""

import asyncio
import os
from pathlib import Path

from agentic_swarm import Agent, tool
from agentic_swarm.vectordb import InMemoryVectorDB
from agentic_swarm.rag.pipeline import RAGPipeline
from agentic_swarm.rag.chunker import Chunker
from agentic_swarm.rag.embedder import MockEmbedder
from agentic_swarm.memory.controller import MemoryController
from agentic_swarm.memory.archival_memory import ArchivalMemory
from agentic_swarm.storage.local import LocalStorage


# =============================================================================
# Configuration
# =============================================================================

STORAGE_DIR = ".agentic_swarm_demo"
COLLECTION_NAME = "knowledge_base"


# =============================================================================
# Sample Documents for Ingestion
# =============================================================================

SAMPLE_DOCUMENTS = [
    {
        "title": "Multi-Agent Systems Overview",
        "content": """
        Multi-agent systems (MAS) consist of multiple autonomous agents that interact 
        within an environment. These agents can cooperate, compete, or coexist to achieve 
        individual or collective goals. Key characteristics include:
        
        - Autonomy: Agents operate independently without direct human intervention
        - Social ability: Agents interact with other agents via communication protocols
        - Reactivity: Agents perceive and respond to their environment
        - Pro-activeness: Agents take initiative to achieve goals
        
        Applications include robotics, distributed computing, and AI assistants.
        """
    },
    {
        "title": "RAG (Retrieval-Augmented Generation)",
        "content": """
        RAG combines retrieval systems with generative AI models. The process involves:
        
        1. Document Ingestion: Text is chunked and embedded into vectors
        2. Vector Storage: Embeddings are stored in a vector database
        3. Query Processing: User queries are embedded and matched against stored vectors
        4. Context Retrieval: Most relevant chunks are retrieved
        5. Generation: LLM generates response using retrieved context
        
        Benefits include reduced hallucination, up-to-date information, and source attribution.
        """
    },
    {
        "title": "Vector Databases",
        "content": """
        Vector databases are specialized systems for storing and querying high-dimensional 
        vectors (embeddings). Popular options include:
        
        - Qdrant: Open-source, supports filtering and payload storage
        - Pinecone: Managed service with high scalability
        - Weaviate: GraphQL API with hybrid search
        - Milvus: Distributed architecture for large-scale deployments
        - ChromaDB: Lightweight, embedded database
        
        Key operations: similarity search (cosine, euclidean), filtering, and CRUD.
        """
    },
    {
        "title": "Agent Memory Systems",
        "content": """
        Modern AI agents use tiered memory systems:
        
        1. Core Memory: Immutable identity (name, persona, capabilities)
        2. Recall Memory: Working context with sliding window (recent conversations)
        3. Archival Memory: Long-term vector-indexed storage (facts, knowledge)
        
        Memory management strategies:
        - Auto-archiving: Move old recall entries to archival
        - Fact extraction: Extract key facts from conversations
        - Deduplication: Prevent storing duplicate information
        - Relevance scoring: Prioritize important memories
        """
    },
    {
        "title": "Persistent Storage Patterns",
        "content": """
        Agent systems require persistent storage for:
        
        - Session state: Current task, conversation history
        - Agent configuration: Tools, permissions, settings
        - Cached responses: LLM outputs for repeated queries
        - Audit logs: Compliance and debugging
        
        Storage backends:
        - Local file system: JSON files for development
        - Redis: Distributed caching with TTL support
        - PostgreSQL: Relational data with JSONB columns
        - S3/GCS: Object storage for large artifacts
        """
    },
]


# =============================================================================
# Tools for the Agent
# =============================================================================

# Global references for tools
_rag_pipeline = None
_archival_memory = None
_storage = None


@tool
async def search_knowledge(query: str, limit: int = 3) -> str:
    """Search the knowledge base for relevant information."""
    global _rag_pipeline
    if _rag_pipeline is None:
        return "Knowledge base not initialized."
    
    results = await _rag_pipeline.query(query, limit=limit)
    if not results.chunks:
        return f"No results found for: {query}"
    
    response = f"Found {len(results.chunks)} relevant results for '{query}':\n\n"
    for i, chunk in enumerate(results.chunks, 1):
        content = chunk.get("content", chunk.get("text", ""))[:200]
        score = chunk.get("score", 0)
        response += f"{i}. (score: {score:.2f}) {content}...\n\n"
    
    return response


@tool
async def store_memory(fact: str) -> str:
    """Store an important fact in long-term archival memory."""
    global _archival_memory
    if _archival_memory is None:
        return "Archival memory not initialized."
    
    await _archival_memory.store(fact)
    return f"Stored in archival memory: {fact[:100]}..."


@tool
async def recall_memories(query: str, limit: int = 5) -> str:
    """Recall relevant memories from archival storage."""
    global _archival_memory
    if _archival_memory is None:
        return "Archival memory not initialized."
    
    results = await _archival_memory.search(query, limit=limit)
    if not results:
        return f"No memories found for: {query}"
    
    response = f"Recalled {len(results)} memories for '{query}':\n"
    for i, mem in enumerate(results, 1):
        content = mem.content[:150] if hasattr(mem, 'content') else str(mem)[:150]
        response += f"{i}. {content}...\n"
    
    return response


@tool
async def save_session_data(key: str, value: str) -> str:
    """Save data to persistent storage."""
    global _storage
    if _storage is None:
        return "Storage not initialized."
    
    await _storage.set(f"session:{key}", {"value": value})
    return f"Saved '{key}' to persistent storage."


@tool
async def load_session_data(key: str) -> str:
    """Load data from persistent storage."""
    global _storage
    if _storage is None:
        return "Storage not initialized."
    
    data = await _storage.get(f"session:{key}")
    if data is None:
        return f"No data found for key: {key}"
    
    return f"Loaded '{key}': {data.get('value', data)}"


# =============================================================================
# Main Example
# =============================================================================

async def main():
    global _rag_pipeline, _archival_memory, _storage
    
    print("=" * 70)
    print("  AGENTIC SWARM — Vector Database + Persistent Storage Example")
    print("=" * 70)
    
    # --- 1. Initialize Storage ---
    print("\n[1] Initializing Persistent Storage...")
    _storage = LocalStorage(base_dir=STORAGE_DIR)
    print(f"    Storage directory: {STORAGE_DIR}")
    
    # Check for existing data
    existing_keys = await _storage.list_keys()
    if existing_keys:
        print(f"    Found {len(existing_keys)} existing keys from previous session")
        for key in existing_keys[:5]:
            print(f"      - {key}")
    
    # --- 2. Initialize Vector Database ---
    print("\n[2] Initializing Vector Database...")
    vectordb = InMemoryVectorDB()
    await vectordb.create_collection(COLLECTION_NAME, vector_size=384)
    print(f"    Collection: {COLLECTION_NAME}")
    print(f"    Vector dimensions: 384")
    
    # --- 3. Initialize Embedder ---
    print("\n[3] Initializing Embedder...")
    embedder = MockEmbedder(dimensions=384)
    print(f"    Using MockEmbedder (384 dimensions)")
    print("    Note: For production, use OpenAI or sentence-transformers embeddings")
    
    # --- 4. Initialize RAG Pipeline ---
    print("\n[4] Initializing RAG Pipeline...")
    chunker = Chunker(chunk_size=300, overlap=50, strategy="recursive")
    _rag_pipeline = RAGPipeline(
        vectordb=vectordb,
        embedder=embedder,
        chunker=chunker,
        default_collection=COLLECTION_NAME,
    )
    print(f"    Chunking strategy: recursive")
    print(f"    Chunk size: 300, Overlap: 50")
    
    # --- 5. Ingest Documents ---
    print("\n[5] Ingesting Documents into Vector Database...")
    for doc in SAMPLE_DOCUMENTS:
        await _rag_pipeline.ingest(
            doc["content"],
            metadata={"title": doc["title"]},
        )
        print(f"    ✓ Ingested: {doc['title']}")
    
    # --- 6. Initialize Archival Memory ---
    print("\n[6] Initializing Archival Memory...")
    _archival_memory = ArchivalMemory(
        agent_id="demo_agent",
        vectordb=vectordb,
        embedder=embedder,
    )
    
    # Store some initial facts
    initial_facts = [
        "The user prefers concise explanations with examples.",
        "Multi-agent systems are the primary topic of interest.",
        "Vector databases enable semantic search capabilities.",
    ]
    for fact in initial_facts:
        await _archival_memory.store(fact)
    print(f"    Stored {len(initial_facts)} initial facts")
    
    # --- 7. Initialize Memory Controller ---
    print("\n[7] Initializing Memory Controller...")
    memory = MemoryController(
        agent_id="demo_agent",
        name="Knowledge Assistant",
        persona="An AI assistant specialized in multi-agent systems and RAG",
        vectordb=vectordb,
        embedder=embedder,
        recall_max_size=50,
        auto_archive=True,
    )
    print(f"    Agent: {memory._core.name}")
    print(f"    Persona: {memory._core.persona}")
    
    # --- 8. Create Agent with Tools ---
    print("\n[8] Creating Agent with Vector DB Tools...")
    agent = Agent(
        name="knowledge_agent",
        role="Knowledge management assistant with vector search and persistent storage",
        tools=[
            search_knowledge,
            store_memory,
            recall_memories,
            save_session_data,
            load_session_data,
        ],
        max_iterations=5,
    )
    print(f"    Agent: {agent.name}")
    print(f"    Tools: {list(agent.tools.keys())}")
    
    # --- 9. Demonstrate Vector Search ---
    print("\n[9] Demonstrating Vector Search...")
    
    queries = [
        "How do multi-agent systems work?",
        "What is RAG and how does it help?",
        "What are the best vector databases?",
    ]
    
    for query in queries:
        print(f"\n    Query: '{query}'")
        result = await _rag_pipeline.query(query, limit=2)
        if result.chunks:
            for i, chunk in enumerate(result.chunks, 1):
                content = chunk.get("content", "")[:100]
                score = chunk.get("score", 0)
                print(f"      {i}. (score: {score:.2f}) {content}...")
    
    # --- 10. Demonstrate Archival Memory ---
    print("\n[10] Demonstrating Archival Memory...")
    
    # Store new memories
    new_memories = [
        "The demo successfully showed vector search capabilities.",
        "Persistent storage allows data to survive across sessions.",
    ]
    for mem in new_memories:
        await _archival_memory.store(mem)
        print(f"    Stored: {mem[:50]}...")
    
    # Search memories
    print("\n    Searching memories for 'vector'...")
    results = await _archival_memory.search("vector", limit=3)
    for i, mem in enumerate(results, 1):
        content = mem.content[:80] if hasattr(mem, 'content') else str(mem)[:80]
        print(f"      {i}. {content}...")
    
    # --- 11. Demonstrate Persistent Storage ---
    print("\n[11] Demonstrating Persistent Storage...")
    
    # Save session data
    session_data = {
        "last_query": "multi-agent systems",
        "documents_ingested": len(SAMPLE_DOCUMENTS),
        "session_id": "demo_001",
    }
    
    for key, value in session_data.items():
        await _storage.set(f"demo:{key}", {"value": value, "type": type(value).__name__})
        print(f"    Saved: demo:{key} = {value}")
    
    # List all keys
    all_keys = await _storage.list_keys()
    print(f"\n    Total keys in storage: {len(all_keys)}")
    
    # Load data back
    print("\n    Loading saved data...")
    for key, _ in session_data.items():
        data = await _storage.get(f"demo:{key}")
        if data:
            print(f"      demo:{key} = {data.get('value')}")
    
    # --- 12. Demonstrate Memory Controller ---
    print("\n[12] Demonstrating Memory Controller...")
    
    # Push to recall memory
    memory.push_recall("User asked about vector databases", role="user")
    memory.push_recall("I explained the different options available", role="assistant")
    memory.push_recall("User wanted to know about Qdrant specifically", role="user")
    
    print(f"    Recall memory size: {memory._recall.size}")
    
    # Get recall messages
    messages = memory.get_recall_messages()
    print(f"    Recent messages: {len(messages)}")
    for msg in messages[-3:]:
        print(f"      [{msg['role']}] {msg['content'][:50]}...")
    
    # Store to archival via controller
    await memory.store_archival("Qdrant is the user's preferred vector database")
    print("    Stored preference to archival memory")
    
    # Search archival via controller
    results = await memory.search_archival("preferred", limit=2)
    print(f"    Found {len(results)} archival results for 'preferred'")
    
    # --- 13. Data Persistence Demo ---
    print("\n[13] Data Persistence Verification...")
    print(f"    Storage location: {Path(STORAGE_DIR).absolute()}")
    
    # Count files
    storage_path = Path(STORAGE_DIR)
    if storage_path.exists():
        files = list(storage_path.glob("*.json"))
        print(f"    Persistent files: {len(files)}")
        for f in files[:5]:
            print(f"      - {f.name}")
    
    print("\n    Data will persist across sessions!")
    print("    Run this example again to see existing data loaded.")
    
    # --- Summary ---
    print("\n" + "=" * 70)
    print("  EXAMPLE COMPLETE")
    print("=" * 70)
    print(f"""
    Features Demonstrated:
    ✓ Vector Database (InMemoryVectorDB)
    ✓ RAG Pipeline (chunking, embedding, retrieval)
    ✓ Archival Memory (vector-indexed long-term storage)
    ✓ Memory Controller (core + recall + archival)
    ✓ Persistent Storage (LocalStorage with JSON files)
    ✓ Agent with custom tools for knowledge management
    
    Storage Location: {Path(STORAGE_DIR).absolute()}
    
    To use Qdrant (production):
      pip install qdrant-client
      from agentic_swarm.vectordb import QdrantClient
      vectordb = QdrantClient(url="localhost:6333")
    
    To use Redis storage (production):
      pip install redis
      from agentic_swarm.storage import RedisStorage
      storage = RedisStorage(url="redis://localhost:6379")
    """)


if __name__ == "__main__":
    asyncio.run(main())
