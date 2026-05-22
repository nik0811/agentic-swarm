"""
Agentic Swarm — Never-Forget Memory Example
============================================

This example demonstrates the "never forget" memory system:
1. Compresses context when it exceeds token budget
2. Stores important information in archival (vector-indexed) memory
3. Searches relevant memories from past sessions
4. Injects them back into future sessions

Run: python examples/never_forget_memory.py
"""

import asyncio
import os
from agentic_swarm import Agent, tool
from agentic_swarm.vectordb import InMemoryVectorDB
from agentic_swarm.rag.embedder import MockEmbedder
from agentic_swarm.memory.controller import MemoryController
from agentic_swarm.llm.context_compressor import ContextCompressor


# =============================================================================
# Tools
# =============================================================================

@tool
def get_user_preference(key: str) -> str:
    """Get a user preference by key."""
    prefs = {
        "theme": "dark",
        "language": "python",
        "editor": "vscode",
    }
    return prefs.get(key, "unknown")


@tool
def save_note(content: str) -> str:
    """Save a note for later."""
    return f"Note saved: {content}"


# =============================================================================
# Main Example
# =============================================================================

async def main():
    print("=" * 70)
    print("  AGENTIC SWARM — Never-Forget Memory")
    print("=" * 70)
    
    # =========================================================================
    # Setup: Vector DB and Embedder for long-term memory
    # =========================================================================
    print("\n[1] SETUP: Vector DB for Long-Term Memory")
    print("-" * 50)
    
    vectordb = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=384)
    
    print(f"    Vector DB: InMemoryVectorDB")
    print(f"    Embedder: MockEmbedder (384 dimensions)")
    print(f"    For production, use QdrantClient or similar persistent DB")
    
    # =========================================================================
    # Create Agent with Never-Forget Memory
    # =========================================================================
    print("\n[2] CREATE AGENT WITH NEVER-FORGET MEMORY")
    print("-" * 50)
    
    agent = Agent(
        name="assistant",
        role="A helpful assistant that remembers everything",
        tools=[get_user_preference, save_note],
        # Never-forget memory options
        vectordb=vectordb,
        embedder=embedder,
        auto_archive=True,           # Auto-archive evicted recall entries
        auto_inject_memories=True,   # Auto-inject relevant memories
        memory_search_limit=3,       # Max memories to inject per task
    )
    
    print(f"    Agent: {agent.name}")
    print(f"    Memory Controller: {'Enabled' if agent._memory else 'Disabled'}")
    print(f"    Auto-archive: {agent._memory._auto_archive if agent._memory else 'N/A'}")
    print(f"    Auto-inject: {agent._auto_inject_memories}")
    
    # =========================================================================
    # Demonstrate: Explicit Memory Storage
    # =========================================================================
    print("\n[3] EXPLICIT MEMORY STORAGE")
    print("-" * 50)
    
    # Store important facts explicitly
    memories_to_store = [
        "User's name is Alice and she prefers dark mode",
        "User is working on a machine learning project",
        "User's favorite programming language is Python",
        "User asked about neural networks last week",
        "User prefers concise explanations over verbose ones",
    ]
    
    print("    Storing memories explicitly:")
    for memory in memories_to_store:
        memory_id = await agent.remember(memory)
        print(f"      ✓ Stored: {memory[:50]}...")
    
    # =========================================================================
    # Demonstrate: Memory Search
    # =========================================================================
    print("\n[4] MEMORY SEARCH")
    print("-" * 50)
    
    queries = [
        "What does the user prefer?",
        "What project is the user working on?",
        "programming language",
    ]
    
    for query in queries:
        print(f"\n    Query: '{query}'")
        results = await agent.recall(query, limit=2)
        for i, mem in enumerate(results):
            print(f"      {i+1}. {mem.content[:60]}...")
    
    # =========================================================================
    # Demonstrate: Auto-Archive on Recall Overflow
    # =========================================================================
    print("\n\n[5] AUTO-ARCHIVE ON RECALL OVERFLOW")
    print("-" * 50)
    
    # Create agent with small recall window to trigger overflow
    small_agent = Agent(
        name="small_memory_agent",
        role="Agent with limited working memory",
        vectordb=vectordb,
        embedder=embedder,
        auto_archive=True,
    )
    
    # Override recall max_size for demo
    small_agent._recall_memory._entries = small_agent._recall_memory._entries.__class__(maxlen=3)
    
    print("    Agent with max 3 recall entries")
    print("    Adding 5 messages (2 will be evicted and archived):")
    
    messages = [
        "Remember: The API key is stored in .env file",
        "Remember: The database is PostgreSQL on port 5432",
        "Remember: The cache uses Redis",
        "Remember: The frontend is React",
        "Remember: The backend is FastAPI",
    ]
    
    for msg in messages:
        small_agent._memory.push_recall(msg, role="user")
        print(f"      Added: {msg[:40]}...")
    
    print(f"\n    Recall size: {small_agent._recall_memory.size}")
    print(f"    Pending archives: {len(small_agent._memory._fact_buffer)}")
    
    # Flush to archival
    archived = await small_agent._memory.flush_to_archival()
    print(f"    Flushed to archival: {archived} entries")
    
    # =========================================================================
    # Demonstrate: Context Compression
    # =========================================================================
    print("\n[6] CONTEXT COMPRESSION")
    print("-" * 50)
    
    compressor = ContextCompressor()
    
    # Create a long conversation
    long_conversation = [
        {"role": "user", "content": "Tell me about machine learning"},
        {"role": "assistant", "content": "Machine learning is a subset of AI that enables systems to learn from data..."},
        {"role": "user", "content": "What about deep learning?"},
        {"role": "assistant", "content": "Deep learning uses neural networks with many layers to learn complex patterns..."},
        {"role": "user", "content": "Can you explain transformers?"},
        {"role": "assistant", "content": "Transformers are a type of neural network architecture that uses attention mechanisms..."},
        {"role": "user", "content": "What is attention?"},
        {"role": "assistant", "content": "Attention allows the model to focus on relevant parts of the input when generating output..."},
        {"role": "user", "content": "Now explain BERT"},
    ]
    
    print(f"    Original messages: {len(long_conversation)}")
    
    # Compress to fit budget
    compressed = compressor.compress(long_conversation, budget=500, preserve_recent=2)
    print(f"    Compressed messages: {len(compressed)}")
    print(f"    Preserved recent: 2")
    
    if len(compressed) > 0 and compressed[0]["role"] == "system":
        print(f"    Summary created: Yes")
        print(f"    Summary preview: {compressed[0]['content'][:100]}...")
    
    # =========================================================================
    # Demonstrate: Fact Extraction
    # =========================================================================
    print("\n[7] FACT EXTRACTION")
    print("-" * 50)
    
    messages_with_facts = [
        {"role": "user", "content": "Remember: my birthday is March 15th"},
        {"role": "assistant", "content": "The answer is 42. I'll remember your birthday."},
        {"role": "user", "content": "Note: I prefer morning meetings"},
        {"role": "assistant", "content": "Key point: Always use type hints in Python code"},
    ]
    
    facts = compressor.extract_key_facts(messages_with_facts)
    print(f"    Extracted {len(facts)} facts:")
    for fact in facts:
        print(f"      - {fact[:60]}...")
    
    # =========================================================================
    # Demonstrate: Memory Injection Flow
    # =========================================================================
    print("\n[8] MEMORY INJECTION FLOW")
    print("-" * 50)
    
    print("""
    When agent.run(task) is called:
    
    1. SEARCH: Query archival memory for relevant past memories
       └── await agent._memory.search_archival(task, limit=3)
    
    2. INJECT: Add relevant memories to recall context
       └── [Relevant memories from past sessions]
           - User's name is Alice...
           - User prefers dark mode...
    
    3. EXECUTE: Run task with enriched context
       └── LLM sees both current task AND relevant history
    
    4. ARCHIVE: Auto-archive important information
       └── Evicted recall entries → fact buffer → archival
    
    5. FLUSH: Persist to archival on completion
       └── await agent._memory.flush_to_archival()
    """)
    
    # =========================================================================
    # Demonstrate: Cross-Session Memory
    # =========================================================================
    print("\n[9] CROSS-SESSION MEMORY (Simulated)")
    print("-" * 50)
    
    # For cross-session memory, agents need to share the same agent_id
    # or use a shared collection prefix
    
    # Session 1: Store information
    print("    SESSION 1: User tells agent their preferences")
    session1_agent = Agent(
        name="persistent_assistant",
        role="Assistant",
        vectordb=vectordb,
        embedder=embedder,
    )
    
    await session1_agent.remember("User prefers TypeScript over JavaScript")
    await session1_agent.remember("User is building a React Native app")
    await session1_agent.remember("User's deadline is next Friday")
    print("      Stored 3 memories")
    agent_id = session1_agent.id  # Save the agent ID
    
    # Session 2: Create agent with SAME ID to access same memories
    # In production, you'd load the agent_id from storage
    print("\n    SESSION 2: New agent instance with same ID retrieves memories")
    
    # Directly use the archival memory from session 1 (simulating persistence)
    # In production, the vectordb would be persistent (Qdrant, Pinecone, etc.)
    memories = await session1_agent.recall("What is the user building?", limit=3)
    print(f"      Found {len(memories)} relevant memories:")
    for mem in memories:
        print(f"        - {mem.content}")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 70)
    print("  NEVER-FORGET MEMORY COMPLETE")
    print("=" * 70)
    print("""
    Features Demonstrated:
    
    ✓ Explicit Memory Storage
      - agent.remember("important fact") → stores in archival
      - agent.recall("query") → searches archival
    
    ✓ Auto-Archive
      - Evicted recall entries → archived automatically
      - Fact extraction from conversations
      - Deduplication prevents duplicates
    
    ✓ Context Compression
      - Compresses long conversations to fit token budget
      - Preserves recent messages
      - Summarizes older context
    
    ✓ Memory Injection
      - Searches relevant memories before each task
      - Injects into context automatically
      - Agent "remembers" past sessions
    
    ✓ Cross-Session Persistence
      - Use persistent vectordb (Qdrant, Pinecone, etc.)
      - Memories survive agent restarts
      - Share memories across agent instances
    
    Usage:
    
    ```python
    from agentic_swarm import Agent
    from agentic_swarm.vectordb import InMemoryVectorDB  # or QdrantClient
    from agentic_swarm.rag.embedder import Embedder
    
    agent = Agent(
        name="assistant",
        role="Helpful assistant",
        vectordb=InMemoryVectorDB(),
        embedder=Embedder(),  # Uses real embeddings
        auto_archive=True,
        auto_inject_memories=True,
    )
    
    # Explicit storage
    await agent.remember("User prefers dark mode")
    
    # Search memories
    memories = await agent.recall("user preferences")
    
    # Run task (auto-injects relevant memories)
    result = await agent.run("What are my preferences?")
    ```
    """)
    
    # Cleanup
    await agent.terminate()
    await small_agent.terminate()
    await session1_agent.terminate()


if __name__ == "__main__":
    asyncio.run(main())
