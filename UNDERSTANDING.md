# Agentic Swarm - Understanding the Architecture

This document explains how the files and folders work together.

---

## Top-Level Files (Public API)

These are the files users import directly:

```
agentic_swarm/
├── __init__.py    # Public exports (Agent, Swarm, Tool)
├── agent.py       # Agent class (immortal, auto-heal, can spawn sub-agents)
├── swarm.py       # Swarm orchestrator (manages multiple agents)
└── tool.py        # Tool decorator and base class
```

### How it works:

```python
# User code
from agentic_swarm import Agent, Swarm, Tool

agent = Agent(name="MyAgent")
swarm = Swarm(agents=[agent])
```

The top-level files provide a **simple API** for users. The real logic lives in the subfolders.

---

## Key Features (from ARCHITECTURE.md)

| Feature | Description |
|---------|-------------|
| **Immortal Agents** | Never die, auto-heal on failure, automatic restart with state recovery |
| **Dynamic Spawning** | Agents can create sub-agents on-the-fly based on task complexity |
| **Isolated Execution** | Each agent runs in sandbox, no user data leakage (SOC2 compliant) |
| **Tiered Memory** | Core (identity), Recall (working), Archival (long-term vector DB) |
| **Smart LLM Routing** | Route to optimal model based on task complexity |

---

## Folder Structure & Responsibilities

```
agentic_swarm/
│
├── core/                  # Core infrastructure
│   ├── config.py          # Configuration management
│   ├── exceptions.py      # Custom exceptions
│   ├── types.py           # Type definitions
│   └── registry.py        # Agent/tool registry
│
├── tools/                 # Tool system
│   ├── base.py            # Tool base class & @tool decorator
│   ├── registry.py        # Tool registry
│   └── builtin/           # Built-in tools
│       ├── agent_management.py  # create_agent, terminate, delegate
│       ├── memory.py            # memory_store, memory_search
│       ├── filesystem.py        # read_file, write_file
│       ├── code_execution.py    # run_python, run_shell (sandboxed)
│       └── web.py               # web_search, web_fetch, api_call
│
├── llm/                   # Intelligent LLM Router
│   ├── base.py            # LLM provider interface
│   ├── router.py          # Smart routing by task complexity
│   ├── classifier.py      # Task complexity classifier
│   ├── token_manager.py   # Token budget & optimization
│   ├── context_compressor.py # Compress context to fit budget
│   ├── providers/         # Pluggable providers
│   │   ├── openai.py      # OpenAI (GPT-4, GPT-4o)
│   │   ├── anthropic.py   # Anthropic (Claude 3.5)
│   │   ├── groq.py        # Groq (fast inference)
│   │   └── ollama.py      # Ollama (local models)
│   └── strategies/        # Routing strategies
│       ├── cost_optimized.py
│       ├── speed_optimized.py
│       └── quality_optimized.py
│
├── memory/                # Tiered memory system
│   ├── base.py            # Memory interface
│   ├── core_memory.py     # Immutable agent identity
│   ├── recall_memory.py   # Working context (sliding window)
│   ├── archival_memory.py # Long-term vector storage
│   └── controller.py      # Memory operations coordinator
│
├── lifecycle/             # Agent lifecycle management
│   ├── supervisor.py      # Health monitoring, auto-restart
│   ├── healer.py          # Auto-recovery logic
│   ├── spawner.py         # Dynamic sub-agent creation
│   └── sandbox.py         # Isolated execution environment
│
├── communication/         # Inter-agent messaging
│   ├── bus.py             # Message bus (encrypted)
│   ├── channel.py         # Point-to-point channels
│   ├── protocols.py       # Message schemas
│   └── router.py          # Message routing
│
├── compliance/            # SOC2 compliance
│   ├── audit.py           # Immutable audit logging
│   ├── encryption.py      # Data encryption (AES-256)
│   ├── isolation.py       # Data isolation enforcement
│   └── access.py          # RBAC and scopes
│
├── rag/                   # RAG Pipeline
│   ├── pipeline.py        # Main RAG orchestrator
│   ├── chunker.py         # Document chunking strategies
│   ├── embedder.py        # Embedding generation
│   ├── retriever.py       # Similarity search & retrieval
│   ├── reranker.py        # Result reranking
│   └── sources/           # Document sources
│       ├── file.py        # Local files (PDF, MD, TXT)
│       ├── web.py         # Web scraping
│       └── github.py      # GitHub repos
│
├── vectordb/              # Vector Database
│   ├── base.py            # VectorDB interface
│   └── qdrant.py          # Qdrant implementation
│
├── storage/               # Persistence backends
│   ├── base.py            # Storage interface
│   ├── local.py           # Local file storage
│   └── redis.py           # Redis backend
│
└── utils/                 # Utilities
    ├── crypto.py          # Cryptographic helpers
    ├── serialization.py   # Safe serialization
    └── validation.py      # Input validation
```

---

## How Files Call Each Other

### 1. User Creates an Agent

```
User Code
    │
    ▼
agent.py (top-level)
    │
    ├──► lifecycle/spawner.py (agent creation)
    │
    ├──► llm/router.py (to call LLM)
    │        │
    │        ├──► llm/classifier.py (determine task complexity)
    │        │
    │        └──► llm/providers/openai.py (actual API call)
    │
    ├──► tools/registry.py (to find tools)
    │        │
    │        └──► tools/builtin/web.py (execute tool)
    │
    └──► memory/controller.py (to store/retrieve memory)
             │
             ├──► memory/core_memory.py (agent identity)
             ├──► memory/recall_memory.py (recent context)
             └──► memory/archival_memory.py → vectordb/qdrant.py
```

### 2. User Creates a Swarm

```
User Code
    │
    ▼
swarm.py (top-level)
    │
    ├──► lifecycle/supervisor.py (health monitoring)
    │
    ├──► agent.py (run each agent)
    │
    └──► communication/bus.py (agents talk to each other)
```

### 3. Agent Spawns Sub-Agent (Dynamic Creation)

```
Parent Agent running a complex task
    │
    ▼
tools/builtin/agent_management.py
    │
    └──► create_agent(name="researcher", tools=[...])
              │
              ▼
         lifecycle/spawner.py
              │
              ├──► Creates new Agent instance
              ├──► Assigns tools and permissions
              ├──► Sets up isolated sandbox
              └──► Returns agent handle to parent
              
Parent Agent
    │
    ├──► researcher.run("Find AI papers")
    │
    ├──► coder = create_agent(name="coder", ...)
    │
    └──► await asyncio.gather(researcher.run(), coder.run())
```

### 4. Agent Uses RAG

```
Agent needs information
    │
    ▼
rag/pipeline.py
    │
    ├──► rag/chunker.py (split documents)
    │
    ├──► rag/embedder.py (create embeddings)
    │
    ├──► rag/retriever.py
    │        │
    │        └──► vectordb/qdrant.py (find similar documents)
    │
    └──► rag/reranker.py (rerank results)
    
    │
    ▼
llm/router.py (generate response with context)
```

### 5. Agent Auto-Heals on Failure

```
Agent crashes
    │
    ▼
lifecycle/supervisor.py (detects failure)
    │
    ▼
lifecycle/healer.py
    │
    ├──► Captures state snapshot
    ├──► Logs error to compliance/audit.py
    ├──► Restores agent from checkpoint
    └──► Resumes execution
```

---

## Example Flow: Complete Request with Dynamic Agent Spawning

```
1. User: "Research Python salary data and create a report"
         │
         ▼
2. swarm.py → Swarm receives task
         │
         ▼
3. lifecycle/supervisor.py → Assigns to Coordinator Agent
         │
         ▼
4. Coordinator Agent thinks (llm/router.py → llm/providers/openai.py)
         │
         ▼
5. LLM decides: "This needs multiple specialists"
         │
         ▼
6. tools/builtin/agent_management.py → create_agent()
         │
         ├──► researcher = Agent(name="researcher", tools=[web_search])
         └──► writer = Agent(name="writer", tools=[write_file])
         │
         ▼
7. lifecycle/spawner.py → Creates agents in isolated sandboxes
         │
         ▼
8. Parallel execution:
         │
         ├──► researcher.run("Find Python salary data")
         │        │
         │        └──► tools/builtin/web.py → web_search()
         │
         └──► (waits for researcher)
         │
         ▼
9. communication/bus.py → researcher sends results to writer
         │
         ▼
10. writer.run("Create report from data")
         │
         └──► tools/builtin/filesystem.py → write_file()
         │
         ▼
11. Results collected, sub-agents terminated
         │
         ▼
12. Return report to user
```

---

## Dynamic Agent Creation (Key Feature)

Agents can create other agents on-the-fly:

```python
# Inside an agent's execution
researcher = await self.create_agent(
    name="researcher",
    role="Research and analyze data",
    tools=[web_search, read_file],
    llm="gpt-4o",
)

result = await researcher.run("Find latest AI papers")

# Create another agent
coder = await self.create_agent(
    name="coder", 
    role="Write and test code",
    tools=[write_file, run_code],
)

# Agents can communicate
await coder.send(researcher, "Need the API specs")

# Parallel execution
results = await asyncio.gather(
    researcher.run("Research task"),
    coder.run("Coding task"),
)
```

**Constraints (Security):**
- Max depth: 3 levels (agent → child → grandchild)
- Permissions: Cannot exceed parent's permissions
- Memory: Isolated, no access to parent's user data
- All creations logged for audit

---

## Why This Structure?

| Layer | Purpose |
|-------|---------|
| **Top-level** (`agent.py`, `swarm.py`) | Simple API for users |
| **lifecycle/** | Agent creation, health, auto-healing, spawning |
| **llm/** | Smart routing to optimal model, token management |
| **tools/** | Actions agents can perform |
| **memory/** | Tiered memory (core, recall, archival) |
| **communication/** | Encrypted inter-agent messaging |
| **compliance/** | SOC2: audit, encryption, isolation |
| **rag/** | Document retrieval and augmentation |
| **vectordb/** | Vector storage (Qdrant) |

This separation allows:
- Easy testing (mock any layer)
- Easy extension (add new providers/tools)
- Clean imports for users
- Security isolation between agents

---

## Import Hierarchy

```
__init__.py imports from:
    ├── agent.py
    ├── swarm.py
    └── tool.py

agent.py imports from:
    ├── lifecycle/ (spawner, healer, supervisor)
    ├── llm/ (router, providers)
    ├── tools/ (registry, builtin)
    ├── memory/ (controller)
    └── communication/ (bus)

swarm.py imports from:
    ├── lifecycle/ (supervisor)
    └── communication/ (bus)

lifecycle/ imports from:
    ├── compliance/ (audit)
    └── storage/ (checkpoints)

llm/ imports from:
    └── utils/

tools/ imports from:
    └── compliance/ (for sandboxing)

rag/ imports from:
    ├── llm/
    └── vectordb/
```

---

## Summary

1. **Top-level files** = Simple API for users (`Agent`, `Swarm`, `Tool`)
2. **Subfolders** = Real implementation with full logic
3. **Dynamic spawning** = Agents create sub-agents as needed
4. **Immortal agents** = Auto-heal on failure, never die
5. **Tiered memory** = Core (identity) + Recall (working) + Archival (long-term)
6. **Smart LLM routing** = Route to optimal model based on task complexity
7. **SOC2 compliance** = Audit, encryption, isolation built-in
