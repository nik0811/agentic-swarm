"""
Example: RAG + Memory + Context Management with Bedrock

Demonstrates the full knowledge pipeline:
1. RAG: Ingest documents → chunk → embed → store in vector DB
2. Memory: Core (identity) + Recall (conversation) + Archival (long-term)
3. Context: Token budgeting, compression, and retrieval-augmented answers

This example runs end-to-end without external services (uses InMemoryVectorDB).
Connect Bedrock for LLM-powered answers, or run in demo mode without credentials.
"""

import os
import asyncio
from agentic_swarm import Agent, tool
from agentic_swarm.llm import LLMRouter, BedrockProvider
from agentic_swarm.memory import MemoryController, CoreMemory, RecallMemory, ArchivalMemory
from agentic_swarm.rag import RAGPipeline, Chunker, Retriever
from agentic_swarm.rag.embedder import MockEmbedder
from agentic_swarm.vectordb import InMemoryVectorDB
from agentic_swarm.llm.token_manager import TokenManager
from agentic_swarm.llm.context_compressor import ContextCompressor


# ─────────────────────────────────────────────────────────────
# SAMPLE KNOWLEDGE BASE (documents to ingest)
# ─────────────────────────────────────────────────────────────

DOCUMENTS = {
    "architecture.md": """
# Multi-Agent Architecture

Multi-agent systems consist of autonomous agents that communicate
and collaborate to solve complex problems. Key components:

- **Agent**: An autonomous entity with goals, tools, and memory
- **Swarm**: An orchestrator managing multiple agents
- **Message Bus**: Pub/sub communication between agents
- **Memory**: Tiered storage (core, recall, archival)

## Design Principles

1. Separation of concerns: Each agent specializes in one domain
2. Fault tolerance: Agents auto-heal on failure
3. Scalability: Horizontal scaling via agent spawning
4. Compliance: SOC2 audit logging from day one
""",
    "memory_guide.md": """
# Memory System Guide

The memory system has three tiers:

## Core Memory
Immutable agent identity. Contains name, persona, and capabilities.
Never changes after initialization.

## Recall Memory  
Sliding window of recent conversation. Configurable size (default 100 entries).
Oldest entries are evicted when full. Supports search by content.

## Archival Memory
Vector-indexed long-term storage. Uses embeddings for semantic search.
Infinite capacity. Used for facts, preferences, and learned knowledge.

## Auto-Archive
When recall memory overflows, evicted entries are automatically stored
in archival memory for later retrieval. This ensures no context is ever lost.
""",
    "rag_guide.md": """
# RAG Pipeline Guide

Retrieval-Augmented Generation enhances LLM responses with relevant context.

## Pipeline Steps

1. **Ingest**: Load documents from files, web, GitHub, or APIs
2. **Chunk**: Split into manageable pieces (fixed, recursive, semantic, code-aware)
3. **Embed**: Convert chunks to vector representations
4. **Store**: Save vectors in database (Qdrant, InMemory)
5. **Retrieve**: Find relevant chunks for a query (dense, sparse, hybrid)
6. **Rerank**: Score and reorder results (cross-encoder, keyword, LLM)
7. **Generate**: Use retrieved context to augment LLM response

## Retrieval Strategies

- **Dense**: Cosine similarity on embeddings (default)
- **Sparse**: BM25 keyword matching
- **Hybrid**: Combines dense + sparse with Reciprocal Rank Fusion (RRF)

## Query Enhancement

- **Query Expansion**: Generate related queries for broader recall
- **HyDE**: Generate hypothetical answer, embed it, search with that
""",
    "tools_guide.md": """
# Tool System

Tools give agents the ability to take actions in the world.

## Built-in Tools

- **web_search**: Search the internet for information
- **web_fetch**: Fetch and parse a URL
- **shell**: Execute shell commands
- **memory_search**: Search agent's archival memory
- **memory_store**: Store information in archival memory

## Custom Tools

Use the @tool decorator to create custom tools:

```python
@tool
def calculate(expression: str) -> str:
    return str(eval(expression))
```

Tools are automatically converted to OpenAI function calling schema.
The agent's LLM decides when and how to call tools.
""",
}


# ─────────────────────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────────────────────

def create_router() -> LLMRouter | None:
    """Create Bedrock router if credentials available."""
    key = os.getenv("AWS_ACCESS_KEY_ID")
    if not key:
        return None

    router = LLMRouter(strategy="cost_optimized")
    bedrock = BedrockProvider(
        model=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v2:0"),
        region=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=key,
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    router.register_provider("bedrock", bedrock)
    return router


async def main():
    print("=" * 65)
    print("  RAG + MEMORY + CONTEXT MANAGEMENT")
    print("=" * 65)

    # ═══════════════════════════════════════════════════════════
    # PART 1: RAG Pipeline
    # ═══════════════════════════════════════════════════════════
    print("\n" + "─" * 65)
    print("  PART 1: RAG PIPELINE")
    print("─" * 65)

    # Setup components
    vectordb = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=128)
    chunker = Chunker(strategy="recursive", chunk_size=200, overlap=30)
    retriever = Retriever(vectordb=vectordb, embedder=embedder)
    pipeline = RAGPipeline(
        vectordb=vectordb,
        embedder=embedder,
        chunker=chunker,
        retriever=retriever,
    )

    # Ingest documents
    print("\n[1.1] Ingesting knowledge base...")
    for name, content in DOCUMENTS.items():
        await pipeline.ingest(content, collection="knowledge", metadata={"source": name})
        print(f"      Ingested: {name} ({len(content)} chars)")

    # Query the RAG pipeline
    print("\n[1.2] Querying RAG pipeline...")

    queries = [
        "How does the memory system work?",
        "What retrieval strategies are available?",
        "How do agents communicate with each other?",
        "How do I create a custom tool?",
    ]

    for query in queries:
        result = await pipeline.query(query, collection="knowledge", limit=3)
        print(f"\n      Q: {query}")
        print(f"      Found {len(result.chunks)} chunks")
        if result.chunks:
            top_chunk = result.chunks[0]
            print(f"      Top match: \"{top_chunk['content'][:80]}...\"")
            print(f"      Source: {top_chunk.get('metadata', {}).get('source', 'unknown')}")

    # ═══════════════════════════════════════════════════════════
    # PART 2: Memory System (All 3 Tiers)
    # ═══════════════════════════════════════════════════════════
    print("\n\n" + "─" * 65)
    print("  PART 2: TIERED MEMORY SYSTEM")
    print("─" * 65)

    # Create memory controller
    memory = MemoryController(
        agent_id="agent-demo",
        name="Knowledge Assistant",
        persona="An AI assistant specialized in explaining multi-agent systems",
        vectordb=vectordb,
        embedder=embedder,
    )

    # Core Memory (immutable identity)
    print("\n[2.1] Core Memory (Identity)...")
    print(f"      Name: {memory.core.name}")
    print(f"      Persona: {memory.core.persona}")
    print(f"      System prompt preview: \"{memory.core.to_prompt()[:80]}...\"")

    # Recall Memory (conversation context)
    print("\n[2.2] Recall Memory (Conversation Window)...")
    conversation = [
        ("user", "What is a multi-agent system?"),
        ("assistant", "A multi-agent system consists of multiple autonomous agents that collaborate to solve complex problems."),
        ("user", "How do they communicate?"),
        ("assistant", "Agents communicate via a message bus (pub/sub) or direct channels for point-to-point messaging."),
        ("user", "What about memory?"),
        ("assistant", "Each agent has tiered memory: core (identity), recall (recent context), and archival (long-term vector storage)."),
        ("user", "Can agents spawn children?"),
        ("assistant", "Yes! Agents can dynamically spawn child agents using the Spawner, with configurable depth and children limits."),
        ("user", "Tell me about RAG"),
        ("assistant", "RAG augments LLM responses by retrieving relevant documents. The pipeline: chunk → embed → store → retrieve → rerank → generate."),
    ]

    for role, content in conversation:
        memory.push_recall(content, role=role)

    messages = memory.get_recall_messages()
    print(f"      Total entries: {len(memory.recall.get_all())}")
    print(f"      Last 5 messages:")
    for msg in messages[-5:]:
        print(f"        [{msg['role']}] {msg['content'][:60]}...")

    # Search recall
    print("\n[2.3] Searching Recall Memory...")
    recall_results = memory.search_recall("spawn children")
    print(f"      Query: 'spawn children'")
    print(f"      Found: {len(recall_results)} matches")
    for r in recall_results[:2]:
        print(f"        → \"{r.content[:70]}...\"")

    # Archival Memory (long-term)
    print("\n[2.4] Archival Memory (Long-term Vector Store)...")
    facts = [
        "User prefers concise, technical explanations",
        "User is building a production multi-agent system",
        "User's stack: Python, AWS Bedrock, Docker",
        "User needs SOC2 compliance for their deployment",
        "Project deadline is Q3 2026",
    ]
    for fact in facts:
        await memory.store_archival(fact)
        print(f"      Stored: \"{fact}\"")

    # Search archival
    print("\n[2.5] Searching Archival Memory...")
    archival_results = await memory.search_archival("compliance requirements", limit=3)
    print(f"      Query: 'compliance requirements'")
    print(f"      Found: {len(archival_results)} matches")
    for r in archival_results:
        print(f"        → \"{r.content[:70]}...\"")

    # Combined search
    print("\n[2.6] Combined Search (All Memory Tiers)...")
    all_results = await memory.search_all("agent communication")
    print(f"      Query: 'agent communication'")
    print(f"      Recall matches: {len(all_results.get('recall', []))}")
    print(f"      Archival matches: {len(all_results.get('archival', []))}")

    # ═══════════════════════════════════════════════════════════
    # PART 3: Token Management & Context Compression
    # ═══════════════════════════════════════════════════════════
    print("\n\n" + "─" * 65)
    print("  PART 3: TOKEN MANAGEMENT & CONTEXT")
    print("─" * 65)

    token_mgr = TokenManager()
    compressor = ContextCompressor()

    # Count tokens
    print("\n[3.1] Token Counting...")
    sample_text = memory.core.to_prompt()
    token_count = token_mgr.count_tokens(sample_text)
    print(f"      System prompt: {token_count} tokens")

    msg_tokens = token_mgr.count_messages_tokens(messages)
    print(f"      Last 5 messages: {msg_tokens} tokens")

    # Calculate budget
    print("\n[3.2] Token Budget Allocation...")
    budget = token_mgr.calculate_budget(
        model_context_limit=128000,
        reserved_output=4000,
        system_prompt_tokens=token_count,
    )
    print(f"      Model context limit: 128,000")
    print(f"      Reserved for output: 4,000")
    print(f"      System prompt: {token_count}")
    print(f"      Available for context: {budget}")

    # Allocate budget
    allocation = token_mgr.allocate_budget(
        total_budget=budget,
        core_memory=sample_text,
        task="Explain how agents communicate",
        tools=[{"name": "search", "description": "Search docs"}],
    )
    print(f"\n[3.3] Budget Allocation Breakdown...")
    for key, value in allocation.items():
        print(f"      {key}: {value} tokens")

    # Context compression
    print("\n[3.4] Context Compression...")
    all_messages = [{"role": r, "content": c} for r, c in conversation]
    compressed = compressor.compress(all_messages, budget=200)
    print(f"      Original messages: {len(all_messages)}")
    print(f"      After compression: {len(compressed)} messages")
    print(f"      Original tokens: ~{token_mgr.count_messages_tokens(all_messages)}")
    print(f"      Compressed tokens: ~{token_mgr.count_messages_tokens(compressed)}")

    # ═══════════════════════════════════════════════════════════
    # PART 4: Full Agent with RAG + Memory + Bedrock
    # ═══════════════════════════════════════════════════════════
    print("\n\n" + "─" * 65)
    print("  PART 4: AGENT WITH RAG + MEMORY (Bedrock)")
    print("─" * 65)

    router = create_router()

    @tool
    async def search_knowledge(query: str) -> str:
        """Search the knowledge base for relevant information."""
        result = await pipeline.query(query, collection="knowledge", limit=3)
        if result.chunks:
            return "\n".join([c["content"][:200] for c in result.chunks[:3]])
        return "No relevant information found."

    @tool
    async def remember_fact(fact: str) -> str:
        """Store an important fact in long-term memory."""
        await memory.store_archival(fact)
        return f"Stored in archival memory: {fact}"

    agent = Agent(
        name="knowledge-agent",
        role="You are a knowledge assistant with access to a documentation knowledge base. "
             "Use search_knowledge to find relevant information before answering. "
             "Use remember_fact to store important information for later.",
        tools=[search_knowledge, remember_fact],
        llm_router=router,
        max_iterations=3,
    )

    print(f"\n[4.1] Agent created: {agent.name}")
    print(f"      Tools: {list(agent.tools.keys())}")
    print(f"      LLM: {'Bedrock (real)' if router else 'None (demo mode)'}")

    if router:
        print("\n[4.2] Running agent with Bedrock...")
        try:
            result = await agent.run(
                "What retrieval strategies does the RAG pipeline support? "
                "Use search_knowledge to find the answer."
            )
            print(f"      Agent response: {str(result)[:300]}...")
        except Exception as e:
            print(f"      Error: {e}")
    else:
        print("\n[4.2] Bedrock not configured - showing what would happen:")
        print("      Agent would call search_knowledge('retrieval strategies')")
        print("      RAG returns: Dense, Sparse (BM25), Hybrid (RRF)")
        print("      Agent synthesizes answer using Bedrock LLM")

    # ═══════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════
    print("\n\n" + "=" * 65)
    print("  SUMMARY")
    print("=" * 65)

    stats = memory.get_stats()
    print(f"\n  Memory Stats:")
    print(f"    Core: {stats.get('core', 'active')}")
    print(f"    Recall entries: {stats.get('recall_count', len(memory.recall.get_all()))}")
    print(f"    Archival entries: {stats.get('archival_count', len(facts))}")
    print(f"\n  RAG Stats:")
    print(f"    Documents ingested: {len(DOCUMENTS)}")
    print(f"    Vector DB collections: knowledge")
    print(f"    Chunking strategy: recursive (200 chars, 30 overlap)")
    print(f"    Retrieval: dense (MockEmbedder, dim=128)")
    print(f"\n  Token Management:")
    print(f"    System prompt: {token_count} tokens")
    print(f"    Available budget: {budget} tokens")
    print(f"    Compression: {len(all_messages)} → {len(compressed)} messages")

    print("\n\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
