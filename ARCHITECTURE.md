# Agentic Swarm SDK - Architecture

## Core Principles

1. **Immortal Agents** - Never die, auto-heal on failure, automatic restart with state recovery
2. **Dynamic Spawning** - Agents spawn sub-agents based on task complexity
3. **Isolated Execution** - Each agent runs in isolation, no user data leakage (SOC2 compliant)
4. **Shared Intelligence** - Agents communicate via secure channels, share context not data
5. **Tiered Memory** - Core (identity), Recall (working), Archival (long-term)

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AGENTIC SWARM SDK                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         ORCHESTRATOR (Supervisor)                        │    │
│  │  • Task decomposition    • Agent lifecycle    • Health monitoring        │    │
│  │  • Load balancing        • Auto-scaling       • Failure recovery         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                           │
│                                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                      SECURE MESSAGE BUS (Encrypted)                      │    │
│  │  • Agent-to-Agent communication    • Event broadcasting                  │    │
│  │  • Task delegation                 • Result aggregation                  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│         │                    │                    │                    │         │
│         ▼                    ▼                    ▼                    ▼         │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐ │
│  │   AGENT A   │      │   AGENT B   │      │   AGENT C   │      │   AGENT N   │ │
│  │  ┌───────┐  │      │  ┌───────┐  │      │  ┌───────┐  │      │  ┌───────┐  │ │
│  │  │SANDBOX│  │      │  │SANDBOX│  │      │  │SANDBOX│  │      │  │SANDBOX│  │ │
│  │  │(Isolated)│      │  │(Isolated)│      │  │(Isolated)│      │  │(Isolated)│ │
│  │  └───────┘  │      │  └───────┘  │      │  └───────┘  │      │  └───────┘  │ │
│  │      │      │      │      │      │      │      │      │      │      │      │ │
│  │      ▼      │      │      ▼      │      │      ▼      │      │      ▼      │ │
│  │  ┌───────┐  │      │  ┌───────┐  │      │  ┌───────┐  │      │  ┌───────┐  │ │
│  │  │ HEALER│  │      │  │ HEALER│  │      │  │ HEALER│  │      │  │ HEALER│  │ │
│  │  │(Auto) │  │      │  │(Auto) │  │      │  │(Auto) │  │      │  │(Auto) │  │ │
│  │  └───────┘  │      │  └───────┘  │      │  └───────┘  │      │  └───────┘  │ │
│  └─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘ │
│         │                    │                    │                    │         │
│         └────────────────────┴────────────────────┴────────────────────┘         │
│                                      │                                           │
│                                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         MEMORY SYSTEM (Per Agent)                        │    │
│  │                                                                          │    │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │    │
│  │  │ CORE MEMORY  │    │RECALL MEMORY │    │ARCHIVAL MEM  │               │    │
│  │  │              │    │              │    │              │               │    │
│  │  │ • Agent ID   │    │ • Working    │    │ • Long-term  │               │    │
│  │  │ • Persona    │    │   context    │    │   storage    │               │    │
│  │  │ • System     │    │ • Recent     │    │ • Searchable │               │    │
│  │  │   prompt     │    │   messages   │    │ • Compressed │               │    │
│  │  │ • Immutable  │    │ • Session    │    │ • Vector DB  │               │    │
│  │  │   identity   │    │   state      │    │   indexed    │               │    │
│  │  │              │    │ • Ephemeral  │    │ • Persistent │               │    │
│  │  └──────────────┘    └──────────────┘    └──────────────┘               │    │
│  │        ▲                    ▲                    ▲                       │    │
│  │        │                    │                    │                       │    │
│  │        └────────── MEMORY CONTROLLER ───────────┘                       │    │
│  │                   (Read/Write/Search)                                    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         SUB-AGENT SPAWNING                               │    │
│  │                                                                          │    │
│  │   Parent Agent                                                           │    │
│  │        │                                                                 │    │
│  │        ├──► spawn("researcher", task) ──► Sub-Agent 1 (isolated)        │    │
│  │        │                                        │                        │    │
│  │        ├──► spawn("coder", task) ──────► Sub-Agent 2 (isolated)         │    │
│  │        │                                        │                        │    │
│  │        └──► collect_results() ◄─────────────────┘                       │    │
│  │                                                                          │    │
│  │   • Sub-agents inherit ONLY task context (not user data)                │    │
│  │   • Auto-terminate on task completion                                    │    │
│  │   • Results sanitized before return                                      │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         SOC2 COMPLIANCE LAYER                            │    │
│  │                                                                          │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │    │
│  │  │   AUDIT     │  │  ENCRYPTION │  │   ACCESS    │  │    DATA     │     │    │
│  │  │   LOGGER    │  │  AT REST &  │  │   CONTROL   │  │  ISOLATION  │     │    │
│  │  │             │  │  IN TRANSIT │  │             │  │             │     │    │
│  │  │ • All ops   │  │ • AES-256   │  │ • RBAC      │  │ • Sandboxed │     │    │
│  │  │   logged    │  │ • TLS 1.3   │  │ • Per-agent │  │ • No cross- │     │    │
│  │  │ • Immutable │  │ • Key       │  │   scopes    │  │   agent     │     │    │
│  │  │ • Tamper-   │  │   rotation  │  │ • Least     │  │   data      │     │    │
│  │  │   proof     │  │             │  │   privilege │  │   access    │     │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Lifecycle (Never Die)

```
                    ┌─────────────────┐
                    │   AGENT BORN    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
              ┌────►│    RUNNING      │◄────┐
              │     └────────┬────────┘     │
              │              │              │
              │         (failure)           │
              │              │              │
              │              ▼              │
              │     ┌─────────────────┐     │
              │     │   RECOVERING    │     │
              │     │                 │     │
              │     │ • State snapshot│     │
              │     │ • Error logged  │     │
              │     │ • Auto-restart  │     │
              │     └────────┬────────┘     │
              │              │              │
              │         (recovered)         │
              │              │              │
              └──────────────┘              │
                                           │
              (health check passes)────────┘
```

---

## Memory Architecture Detail

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT MEMORY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CORE MEMORY (Immutable Identity)                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ {                                                          │  │
│  │   "agent_id": "uuid",                                      │  │
│  │   "name": "researcher",                                    │  │
│  │   "persona": "You are a research specialist...",          │  │
│  │   "capabilities": ["search", "analyze", "summarize"],     │  │
│  │   "created_at": "timestamp",                               │  │
│  │   "version": "1.0.0"                                       │  │
│  │ }                                                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  RECALL MEMORY (Working Context - Sliding Window)               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ • Current conversation (last N messages)                   │  │
│  │ • Active task state                                        │  │
│  │ • Temporary variables                                      │  │
│  │ • Session-specific context                                 │  │
│  │ • Auto-evicts oldest when full                            │  │
│  │ • Max size: configurable (default 100 entries)            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ARCHIVAL MEMORY (Long-term - Vector Indexed)                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ • Completed task summaries                                 │  │
│  │ • Learned patterns                                         │  │
│  │ • Important facts extracted from conversations            │  │
│  │ • Searchable via semantic similarity                      │  │
│  │ • Compressed and deduplicated                             │  │
│  │ • Persistent across restarts                              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  MEMORY OPERATIONS:                                             │
│  • core_read()      - Read identity (always available)          │
│  • recall_push()    - Add to working memory                     │
│  • recall_search()  - Search recent context                     │
│  • archive_store()  - Persist to long-term                      │
│  • archive_search() - Semantic search archival                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Inter-Agent Communication

```
┌──────────────┐                              ┌──────────────┐
│   AGENT A    │                              │   AGENT B    │
│              │                              │              │
│  ┌────────┐  │    ┌──────────────────┐     │  ┌────────┐  │
│  │ Outbox │──┼───►│  MESSAGE BUS     │◄────┼──│ Outbox │  │
│  └────────┘  │    │                  │     │  └────────┘  │
│              │    │  • Encrypted     │     │              │
│  ┌────────┐  │    │  • Authenticated │     │  ┌────────┐  │
│  │ Inbox  │◄─┼────│  • Logged        │────►┼──│ Inbox  │  │
│  └────────┘  │    │  • No user data  │     │  └────────┘  │
│              │    └──────────────────┘     │              │
└──────────────┘                              └──────────────┘

Message Types:
• TASK_DELEGATE   - Assign work to another agent
• TASK_RESULT     - Return completed work
• CONTEXT_SHARE   - Share relevant context (sanitized)
• HEALTH_PING     - Liveness check
• SPAWN_REQUEST   - Request sub-agent creation
```

---

## Folder Structure

```
agentic_swarm/
├── __init__.py              # Public API exports
├── agent.py                 # Base Agent class (immortal, auto-heal)
├── swarm.py                 # Swarm orchestrator
├── tool.py                  # Tool decorator and base class
│
├── core/                    # Core infrastructure
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── exceptions.py        # Custom exceptions
│   ├── types.py             # Type definitions
│   └── registry.py          # Agent/tool registry
│
├── memory/                  # Tiered memory system
│   ├── __init__.py
│   ├── base.py              # Memory interface
│   ├── core_memory.py       # Immutable agent identity
│   ├── recall_memory.py     # Working context (sliding window)
│   ├── archival_memory.py   # Long-term vector storage
│   └── controller.py        # Memory operations coordinator
│
├── lifecycle/               # Agent lifecycle management
│   ├── __init__.py
│   ├── supervisor.py        # Health monitoring, auto-restart
│   ├── healer.py            # Auto-recovery logic
│   ├── spawner.py           # Dynamic sub-agent creation
│   └── sandbox.py           # Isolated execution environment
│
├── communication/           # Inter-agent messaging
│   ├── __init__.py
│   ├── bus.py               # Message bus (encrypted)
│   ├── channel.py           # Point-to-point channels
│   ├── protocols.py         # Message schemas
│   └── router.py            # Message routing
│
├── llm/                     # Intelligent LLM Router
│   ├── __init__.py
│   ├── base.py              # LLM provider interface
│   ├── router.py            # Smart routing by task complexity
│   ├── classifier.py        # Task complexity classifier
│   ├── token_manager.py     # Token budget & optimization
│   ├── context_compressor.py # Compress context to fit budget
│   ├── providers/           # Pluggable providers
│   │   ├── __init__.py
│   │   ├── openai.py        # OpenAI (GPT-4, GPT-4o, GPT-3.5)
│   │   ├── anthropic.py     # Anthropic (Claude 3.5, Claude 3)
│   │   ├── vllm.py          # Local vLLM (Llama, Mistral)
│   │   ├── groq.py          # Groq (fast inference)
│   │   └── ollama.py        # Ollama (local models)
│   └── strategies/          # Routing strategies
│       ├── __init__.py
│       ├── cost_optimized.py    # Minimize cost
│       ├── speed_optimized.py   # Minimize latency
│       └── quality_optimized.py # Maximize quality
│
├── compliance/              # SOC2 compliance
│   ├── __init__.py
│   ├── audit.py             # Immutable audit logging
│   ├── encryption.py        # Data encryption (AES-256)
│   ├── isolation.py         # Data isolation enforcement
│   └── access.py            # RBAC and scopes
│
├── storage/                 # Persistence backends
│   ├── __init__.py
│   ├── base.py              # Storage interface
│   ├── local.py             # Local file storage
│   └── redis.py             # Redis backend
│
├── rag/                     # RAG Pipeline
│   ├── __init__.py
│   ├── pipeline.py          # Main RAG orchestrator
│   ├── chunker.py           # Document chunking strategies
│   ├── embedder.py          # Embedding generation
│   ├── retriever.py         # Similarity search & retrieval
│   ├── reranker.py          # Result reranking (cross-encoder)
│   ├── query_engine.py      # Query processing & expansion
│   └── sources/             # Document sources
│       ├── __init__.py
│       ├── base.py          # Source interface
│       ├── file.py          # Local files (PDF, MD, TXT)
│       ├── web.py           # Web scraping
│       ├── github.py        # GitHub repos
│       └── api.py           # REST API sources
│
├── vectordb/                # Vector Database Backends
│   ├── __init__.py
│   ├── base.py              # VectorDB interface
│   ├── qdrant.py            # Qdrant (recommended)
│   ├── chroma.py            # ChromaDB (local)
│   ├── pinecone.py          # Pinecone (cloud)
│   ├── weaviate.py          # Weaviate
│   ├── pgvector.py          # PostgreSQL pgvector
│   └── milvus.py            # Milvus
│
└── utils/                   # Utilities
    ├── __init__.py
    ├── crypto.py            # Cryptographic helpers
    ├── serialization.py     # Safe serialization
    └── validation.py        # Input validation

examples/                    # Usage examples
├── simple_agent.py
├── multi_agent_swarm.py
├── sub_agent_spawning.py
└── memory_usage.py

tests/                       # Test suite
├── __init__.py
├── test_agent.py
├── test_memory.py
├── test_communication.py
└── test_compliance.py
```

---

## Key Features Summary

| Feature | Implementation |
|---------|----------------|
| **Never Die** | Supervisor monitors health, auto-restarts with state recovery |
| **Auto-Heal** | Healer captures state snapshot, logs error, restores agent |
| **Multi-Agent** | Swarm orchestrator manages N agents in parallel |
| **Sub-Agent Spawning** | Spawner creates task-specific agents on demand |
| **Communication** | Encrypted message bus, no user data in transit |
| **Memory Isolation** | Each agent has private memory, no cross-access |
| **Core Memory** | Immutable identity (persona, capabilities) |
| **Recall Memory** | Sliding window working context |
| **Archival Memory** | Vector-indexed long-term storage |
| **SOC2 Compliance** | Audit logs, encryption, RBAC, data isolation |
| **Smart LLM Routing** | Route to optimal model based on task complexity |
| **Token Management** | Send only required context, compress when needed |
| **RAG Pipeline** | Chunk, embed, retrieve, rerank for knowledge augmentation |
| **Vector DB** | Pluggable backends (Qdrant, Chroma, Pinecone, pgvector) |

---

## LLM Router Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           INTELLIGENT LLM ROUTER                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        INCOMING REQUEST                                  │    │
│  │  { task, context, memory, constraints }                                 │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                           │
│                                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                     TASK COMPLEXITY CLASSIFIER                           │    │
│  │                                                                          │    │
│  │  Analyzes task to determine:                                            │    │
│  │  • Reasoning depth required (simple → complex → expert)                 │    │
│  │  • Domain specificity (general → specialized)                           │    │
│  │  • Output format (text, code, structured data)                          │    │
│  │  • Latency requirements (real-time, batch)                              │    │
│  │                                                                          │    │
│  │  Classification uses SMALL/FAST model (e.g., GPT-3.5, Llama-8B)        │    │
│  │  Cost: ~0.001$ per classification                                       │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                           │
│                                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                       TOKEN BUDGET CALCULATOR                            │    │
│  │                                                                          │    │
│  │  Input:                          Output:                                 │    │
│  │  • Task complexity score         • Max input tokens                     │    │
│  │  • Selected model limits         • Max output tokens                    │    │
│  │  • Cost constraints              • Context window allocation            │    │
│  │  • Priority level                • Reserved tokens for response         │    │
│  │                                                                          │    │
│  │  Formula: budget = min(model_limit, cost_limit / price_per_token)       │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                           │
│                                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                       CONTEXT COMPRESSOR                                 │    │
│  │                                                                          │    │
│  │  Strategies (applied in order until within budget):                     │    │
│  │                                                                          │    │
│  │  1. RELEVANCE FILTER                                                    │    │
│  │     └─ Keep only context relevant to current task                       │    │
│  │                                                                          │    │
│  │  2. SUMMARIZATION                                                       │    │
│  │     └─ Summarize older messages (use small model)                       │    │
│  │                                                                          │    │
│  │  3. TRUNCATION                                                          │    │
│  │     └─ Remove oldest context first (preserve recent)                    │    │
│  │                                                                          │    │
│  │  4. EXTRACTION                                                          │    │
│  │     └─ Extract only key facts/entities from context                     │    │
│  │                                                                          │    │
│  │  Priority: Core Memory > Recent Recall > Archival Search Results        │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                           │
│                                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        MODEL SELECTOR                                    │    │
│  │                                                                          │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │    │
│  │  │  COMPLEXITY     │  PRIMARY MODEL      │  FALLBACK              │    │    │
│  │  ├─────────────────┼─────────────────────┼────────────────────────┤    │    │
│  │  │  TRIVIAL        │  Local Llama-8B     │  GPT-3.5-turbo        │    │    │
│  │  │  (classification│  Ollama/Mistral-7B  │  Claude-3-haiku       │    │    │
│  │  │   simple Q&A)   │  Groq/Llama-70B     │                        │    │    │
│  │  ├─────────────────┼─────────────────────┼────────────────────────┤    │    │
│  │  │  MODERATE       │  GPT-4o-mini        │  Claude-3.5-sonnet    │    │    │
│  │  │  (summarization │  Local Llama-70B    │  GPT-4-turbo          │    │    │
│  │  │   basic coding) │  Groq/Llama-70B     │                        │    │    │
│  │  ├─────────────────┼─────────────────────┼────────────────────────┤    │    │
│  │  │  COMPLEX        │  GPT-4o             │  Claude-3.5-sonnet    │    │    │
│  │  │  (multi-step    │  Claude-3.5-sonnet  │  GPT-4-turbo          │    │    │
│  │  │   reasoning)    │                     │                        │    │    │
│  │  ├─────────────────┼─────────────────────┼────────────────────────┤    │    │
│  │  │  EXPERT         │  Claude-3-opus      │  GPT-4o               │    │    │
│  │  │  (research,     │  GPT-4o (high temp) │  o1-preview           │    │    │
│  │  │   architecture) │  o1-mini            │                        │    │    │
│  │  └─────────────────┴─────────────────────┴────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                           │
│                                      ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                      PROVIDER POOL (Load Balanced)                       │    │
│  │                                                                          │    │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │    │
│  │   │  LOCAL   │  │  OPENAI  │  │ANTHROPIC │  │   GROQ   │  │  OLLAMA  │ │    │
│  │   │  vLLM    │  │          │  │          │  │          │  │          │ │    │
│  │   │          │  │ GPT-4o   │  │ Claude   │  │ Llama    │  │ Mistral  │ │    │
│  │   │ Llama-70B│  │ GPT-3.5  │  │ 3.5/3    │  │ 70B/8B   │  │ Phi-3    │ │    │
│  │   │          │  │ o1       │  │ Opus     │  │          │  │ Gemma    │ │    │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │    │
│  │        │              │              │              │              │     │    │
│  │        └──────────────┴──────────────┴──────────────┴──────────────┘     │    │
│  │                                   │                                       │    │
│  │                          HEALTH MONITOR                                  │    │
│  │                    (latency, errors, rate limits)                        │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Token Management Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          TOKEN MANAGEMENT PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  STEP 1: CALCULATE AVAILABLE BUDGET                                             │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                            │  │
│  │  model_context_limit = 128000  (e.g., GPT-4o)                             │  │
│  │  reserved_for_output = 4000    (expected response size)                   │  │
│  │  system_prompt_tokens = 500    (agent persona, instructions)              │  │
│  │                                                                            │  │
│  │  AVAILABLE_FOR_CONTEXT = 128000 - 4000 - 500 = 123,500 tokens            │  │
│  │                                                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                           │
│                                      ▼                                           │
│  STEP 2: PRIORITIZE CONTEXT SOURCES                                             │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                            │  │
│  │  PRIORITY 1 (MUST INCLUDE):                                               │  │
│  │  ├─ Core Memory (agent identity)           ~200 tokens                    │  │
│  │  ├─ Current task/query                     ~100-500 tokens                │  │
│  │  └─ Tool definitions (if needed)           ~500-2000 tokens               │  │
│  │                                                                            │  │
│  │  PRIORITY 2 (INCLUDE IF SPACE):                                           │  │
│  │  ├─ Recent recall memory (last 5 msgs)     ~1000-3000 tokens              │  │
│  │  ├─ Relevant archival search results       ~500-2000 tokens               │  │
│  │  └─ Sub-agent results (if any)             ~500-1500 tokens               │  │
│  │                                                                            │  │
│  │  PRIORITY 3 (COMPRESS OR SKIP):                                           │  │
│  │  ├─ Older recall memory                    → Summarize                    │  │
│  │  ├─ Full conversation history              → Extract key points           │  │
│  │  └─ Background context                     → Skip if over budget          │  │
│  │                                                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                           │
│                                      ▼                                           │
│  STEP 3: APPLY COMPRESSION STRATEGIES                                           │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                            │  │
│  │  IF total_tokens > available_budget:                                      │  │
│  │                                                                            │  │
│  │    Strategy A: SEMANTIC CHUNKING                                          │  │
│  │    ┌─────────────────────────────────────────────────────────────────┐    │  │
│  │    │ • Split context into semantic chunks                             │    │  │
│  │    │ • Score each chunk by relevance to current task                  │    │  │
│  │    │ • Keep top-K chunks that fit budget                              │    │  │
│  │    └─────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                            │  │
│  │    Strategy B: PROGRESSIVE SUMMARIZATION                                  │  │
│  │    ┌─────────────────────────────────────────────────────────────────┐    │  │
│  │    │ • Older messages → 1-line summaries (use small model)            │    │  │
│  │    │ • Recent messages → Keep full text                               │    │  │
│  │    │ • Ratio: 10:1 compression for old, 1:1 for recent               │    │  │
│  │    └─────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                            │  │
│  │    Strategy C: ENTITY EXTRACTION                                          │  │
│  │    ┌─────────────────────────────────────────────────────────────────┐    │  │
│  │    │ • Extract: names, dates, numbers, decisions, action items        │    │  │
│  │    │ • Format as structured key-value pairs                           │    │  │
│  │    │ • Discard narrative/filler text                                  │    │  │
│  │    └─────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                           │
│                                      ▼                                           │
│  STEP 4: ASSEMBLE FINAL PROMPT                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                            │  │
│  │  final_prompt = {                                                         │  │
│  │    "system": core_memory + agent_instructions,     # ~700 tokens         │  │
│  │    "context": compressed_recall + archival_hits,   # ~3000 tokens        │  │
│  │    "tools": relevant_tool_definitions,             # ~1000 tokens        │  │
│  │    "task": current_user_query                      # ~200 tokens         │  │
│  │  }                                                                        │  │
│  │                                                                            │  │
│  │  TOTAL: ~4900 tokens (well under 123,500 budget)                         │  │
│  │  SAVINGS: 95%+ reduction from naive "send everything" approach           │  │
│  │                                                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Routing Decision Tree

```
                              ┌─────────────────┐
                              │  INCOMING TASK  │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Is it a simple  │
                              │ classification/ │───YES──► LOCAL MODEL (Llama-8B)
                              │ yes-no question?│          Cost: $0.00
                              └────────┬────────┘
                                       │ NO
                                       ▼
                              ┌─────────────────┐
                              │ Is it basic     │
                              │ text generation │───YES──► GPT-3.5 / Groq
                              │ or formatting?  │          Cost: ~$0.001
                              └────────┬────────┘
                                       │ NO
                                       ▼
                              ┌─────────────────┐
                              │ Does it require │
                              │ code generation │───YES──► GPT-4o-mini / Claude-3.5-sonnet
                              │ or analysis?    │          Cost: ~$0.01
                              └────────┬────────┘
                                       │ NO
                                       ▼
                              ┌─────────────────┐
                              │ Does it require │
                              │ multi-step      │───YES──► GPT-4o / Claude-3.5-sonnet
                              │ reasoning?      │          Cost: ~$0.05
                              └────────┬────────┘
                                       │ NO
                                       ▼
                              ┌─────────────────┐
                              │ Is it expert-   │
                              │ level research/ │───YES──► Claude-3-opus / o1
                              │ architecture?   │          Cost: ~$0.15
                              └────────┬────────┘
                                       │ NO
                                       ▼
                              ┌─────────────────┐
                              │ DEFAULT: Use    │
                              │ GPT-4o-mini     │
                              │ (balanced)      │
                              └─────────────────┘
```

---

## RAG Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RAG PIPELINE                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         INGESTION PIPELINE                               │    │
│  │                                                                          │    │
│  │   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐         │    │
│  │   │  SOURCE  │───►│  LOADER  │───►│ CHUNKER  │───►│ EMBEDDER │         │    │
│  │   │          │    │          │    │          │    │          │         │    │
│  │   │ • Files  │    │ • PDF    │    │ • Fixed  │    │ • OpenAI │         │    │
│  │   │ • Web    │    │ • MD     │    │ • Semantic│   │ • Cohere │         │    │
│  │   │ • GitHub │    │ • HTML   │    │ • Sentence│   │ • Local  │         │    │
│  │   │ • API    │    │ • Code   │    │ • Recursive│  │ • HF     │         │    │
│  │   └──────────┘    └──────────┘    └──────────┘    └──────────┘         │    │
│  │                                                          │              │    │
│  │                                                          ▼              │    │
│  │                                                   ┌──────────┐         │    │
│  │                                                   │ VECTOR   │         │    │
│  │                                                   │ DATABASE │         │    │
│  │                                                   │          │         │    │
│  │                                                   │ • Qdrant │         │    │
│  │                                                   │ • Chroma │         │    │
│  │                                                   │ • Pinecone│        │    │
│  │                                                   │ • pgvector│        │    │
│  │                                                   └──────────┘         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         RETRIEVAL PIPELINE                               │    │
│  │                                                                          │    │
│  │   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐         │    │
│  │   │  QUERY   │───►│ QUERY    │───►│RETRIEVER │───►│ RERANKER │         │    │
│  │   │          │    │ ENGINE   │    │          │    │          │         │    │
│  │   │ User     │    │          │    │ • Dense  │    │ • Cross- │         │    │
│  │   │ question │    │ • Expand │    │ • Sparse │    │   encoder│         │    │
│  │   │          │    │ • Rewrite│    │ • Hybrid │    │ • Cohere │         │    │
│  │   │          │    │ • HyDE   │    │ • MMR    │    │ • ColBERT│         │    │
│  │   └──────────┘    └──────────┘    └──────────┘    └──────────┘         │    │
│  │                                                          │              │    │
│  │                                                          ▼              │    │
│  │                                                   ┌──────────┐         │    │
│  │                                                   │ CONTEXT  │         │    │
│  │                                                   │ (Top-K   │         │    │
│  │                                                   │  chunks) │         │    │
│  │                                                   └──────────┘         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## RAG Retrieval Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          RAG RETRIEVAL DETAIL                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  STEP 1: QUERY PROCESSING                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                            │  │
│  │  Original Query: "How do I configure Kubernetes autoscaling?"             │  │
│  │                                                                            │  │
│  │  Query Expansion (generate related queries):                              │  │
│  │  ├─ "Kubernetes HPA configuration"                                        │  │
│  │  ├─ "kubectl autoscale deployment"                                        │  │
│  │  └─ "Horizontal Pod Autoscaler YAML"                                      │  │
│  │                                                                            │  │
│  │  HyDE (Hypothetical Document Embedding):                                  │  │
│  │  └─ Generate hypothetical answer, embed that instead of query             │  │
│  │                                                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                           │
│                                      ▼                                           │
│  STEP 2: MULTI-STRATEGY RETRIEVAL                                               │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                            │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │  │
│  │  │  DENSE SEARCH   │  │  SPARSE SEARCH  │  │  KEYWORD SEARCH │            │  │
│  │  │                 │  │                 │  │                 │            │  │
│  │  │ Semantic        │  │ BM25            │  │ Exact match     │            │  │
│  │  │ similarity      │  │ TF-IDF          │  │ Regex patterns  │            │  │
│  │  │ (embeddings)    │  │                 │  │                 │            │  │
│  │  │                 │  │                 │  │                 │            │  │
│  │  │ Returns: 20     │  │ Returns: 20     │  │ Returns: 10     │            │  │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │  │
│  │           │                    │                    │                      │  │
│  │           └────────────────────┴────────────────────┘                      │  │
│  │                                │                                           │  │
│  │                                ▼                                           │  │
│  │                    ┌─────────────────────┐                                 │  │
│  │                    │   FUSION (RRF)      │                                 │  │
│  │                    │                     │                                 │  │
│  │                    │ Reciprocal Rank     │                                 │  │
│  │                    │ Fusion combines     │                                 │  │
│  │                    │ all results         │                                 │  │
│  │                    │                     │                                 │  │
│  │                    │ Output: 30 chunks   │                                 │  │
│  │                    └─────────────────────┘                                 │  │
│  │                                                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                           │
│                                      ▼                                           │
│  STEP 3: RERANKING                                                              │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                            │  │
│  │  Cross-Encoder Reranker (e.g., Cohere Rerank, BGE-reranker)              │  │
│  │                                                                            │  │
│  │  Input: 30 candidate chunks                                               │  │
│  │  Process: Score each (query, chunk) pair with cross-encoder              │  │
│  │  Output: Top 5-10 most relevant chunks                                    │  │
│  │                                                                            │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │ Rank │ Score │ Chunk                                                │  │  │
│  │  ├──────┼───────┼──────────────────────────────────────────────────────┤  │  │
│  │  │  1   │ 0.95  │ "To configure HPA, create a YAML with..."           │  │  │
│  │  │  2   │ 0.89  │ "kubectl autoscale deployment nginx --min=2..."     │  │  │
│  │  │  3   │ 0.82  │ "The Horizontal Pod Autoscaler automatically..."    │  │  │
│  │  │  4   │ 0.78  │ "Metrics server must be installed for HPA..."       │  │  │
│  │  │  5   │ 0.71  │ "Custom metrics can be used with Prometheus..."     │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                           │
│                                      ▼                                           │
│  STEP 4: CONTEXT ASSEMBLY                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                            │  │
│  │  final_context = """                                                      │  │
│  │  [Source: k8s-docs/autoscaling.md]                                        │  │
│  │  To configure HPA, create a YAML with...                                  │  │
│  │                                                                            │  │
│  │  [Source: runbooks/scaling.md]                                            │  │
│  │  kubectl autoscale deployment nginx --min=2...                            │  │
│  │                                                                            │  │
│  │  [Source: k8s-docs/hpa-overview.md]                                       │  │
│  │  The Horizontal Pod Autoscaler automatically...                           │  │
│  │  """                                                                       │  │
│  │                                                                            │  │
│  │  → Passed to LLM along with user query                                    │  │
│  │  → Token budget respected (compress if needed)                            │  │
│  │                                                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Vector Database Comparison

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        VECTOR DATABASE OPTIONS                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  DATABASE    │ TYPE    │ BEST FOR                │ SCALE              │    │
│  ├──────────────┼─────────┼─────────────────────────┼────────────────────┤    │
│  │  Qdrant      │ Native  │ Production, hybrid      │ Billions vectors   │    │
│  │              │         │ search, filtering       │ Distributed        │    │
│  ├──────────────┼─────────┼─────────────────────────┼────────────────────┤    │
│  │  ChromaDB    │ Native  │ Local dev, prototyping  │ Millions vectors   │    │
│  │              │         │ Simple setup            │ Single node        │    │
│  ├──────────────┼─────────┼─────────────────────────┼────────────────────┤    │
│  │  Pinecone    │ Cloud   │ Managed, serverless     │ Billions vectors   │    │
│  │              │         │ Zero ops                │ Auto-scaling       │    │
│  ├──────────────┼─────────┼─────────────────────────┼────────────────────┤    │
│  │  pgvector    │ Extension│ Existing Postgres      │ Millions vectors   │    │
│  │              │         │ ACID transactions       │ Single node        │    │
│  ├──────────────┼─────────┼─────────────────────────┼────────────────────┤    │
│  │  Weaviate    │ Native  │ GraphQL, modules        │ Billions vectors   │    │
│  │              │         │ Built-in vectorizers    │ Distributed        │    │
│  ├──────────────┼─────────┼─────────────────────────┼────────────────────┤    │
│  │  Milvus      │ Native  │ GPU acceleration        │ Trillions vectors  │    │
│  │              │         │ High throughput         │ Distributed        │    │
│  └──────────────┴─────────┴─────────────────────────┴────────────────────┘    │
│                                                                                  │
│  RECOMMENDED:                                                                   │
│  • Development: ChromaDB (zero config, in-memory)                              │
│  • Production: Qdrant (fast, feature-rich, self-hosted or cloud)              │
│  • Existing Postgres: pgvector (no new infra)                                  │
│  • Serverless: Pinecone (managed, pay-per-use)                                 │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Chunking Strategies

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          CHUNKING STRATEGIES                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  1. FIXED SIZE CHUNKING                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  • Split by character/token count (e.g., 512 tokens)                      │  │
│  │  • Overlap between chunks (e.g., 50 tokens)                               │  │
│  │  • Simple but may break mid-sentence                                      │  │
│  │                                                                            │  │
│  │  [====CHUNK 1====]                                                        │  │
│  │              [====CHUNK 2====]                                            │  │
│  │                          [====CHUNK 3====]                                │  │
│  │         ↑ overlap ↑                                                       │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  2. SEMANTIC CHUNKING                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  • Split by semantic similarity (embedding distance)                      │  │
│  │  • Keeps related content together                                         │  │
│  │  • More expensive (requires embeddings)                                   │  │
│  │                                                                            │  │
│  │  [== Topic A ==][=== Topic B ===][== Topic C ==]                         │  │
│  │  (natural boundaries based on meaning)                                    │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  3. RECURSIVE CHUNKING                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  • Split by hierarchy: headers → paragraphs → sentences                   │  │
│  │  • Respects document structure                                            │  │
│  │  • Best for structured docs (Markdown, HTML)                              │  │
│  │                                                                            │  │
│  │  Document                                                                  │  │
│  │  ├── # Section 1 ──────► [Chunk]                                         │  │
│  │  │   ├── ## Subsection ─► [Chunk]                                        │  │
│  │  │   └── ## Subsection ─► [Chunk]                                        │  │
│  │  └── # Section 2 ──────► [Chunk]                                         │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  4. CODE-AWARE CHUNKING                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  • Split by AST (functions, classes, methods)                             │  │
│  │  • Preserves code structure                                               │  │
│  │  • Language-specific parsers (tree-sitter)                                │  │
│  │                                                                            │  │
│  │  file.py                                                                   │  │
│  │  ├── class UserService ──► [Chunk: full class]                           │  │
│  │  │   ├── def create() ───► [Chunk: method + docstring]                   │  │
│  │  │   └── def delete() ───► [Chunk: method + docstring]                   │  │
│  │  └── def helper() ───────► [Chunk: function]                             │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  RECOMMENDED SETTINGS:                                                          │
│  • Chunk size: 256-512 tokens (balance context vs precision)                   │
│  • Overlap: 10-20% of chunk size                                               │
│  • Strategy: Recursive for docs, Code-aware for code                           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```
