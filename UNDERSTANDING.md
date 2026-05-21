# Agentic Swarm - Understanding the Architecture

This document explains how the files and folders work together.

---

## Top-Level Files (Public API)

These are the files users import directly:

```
agentic_swarm/
├── __init__.py    # Public exports (Agent, Swarm, Tool)
├── agent.py       # Simple Agent wrapper (uses core/)
├── swarm.py       # Simple Swarm wrapper (uses core/)
└── tool.py        # Simple Tool wrapper (uses tools/)
```

### How it works:

```python
# User code
from agentic_swarm import Agent, Swarm, Tool

agent = Agent(name="MyAgent")
swarm = Swarm(agents=[agent])
```

The top-level files are **thin wrappers** that provide a simple API. The real logic lives in the subfolders.

---

## Folder Structure & Responsibilities

```
agentic_swarm/
│
├── core/                  # Core abstractions
│   ├── base_agent.py      # BaseAgent class with full logic
│   ├── base_swarm.py      # BaseSwarm orchestration logic
│   └── task.py            # Task definition and state
│
├── tools/                 # Tool system
│   ├── base_tool.py       # BaseTool class
│   ├── registry.py        # Tool registry (find tools by name)
│   └── builtin/           # Built-in tools
│       ├── search.py      # Web search tool
│       ├── calculator.py  # Math tool
│       └── file_reader.py # Read files tool
│
├── llm/                   # LLM integration
│   ├── client.py          # Base LLM client interface
│   ├── providers/         # Provider implementations
│   │   ├── openai.py      # OpenAI API
│   │   └── anthropic.py   # Anthropic API
│   └── strategies/        # Calling strategies
│       ├── retry.py       # Retry on failure
│       └── fallback.py    # Fallback to another provider
│
├── memory/                # Agent memory
│   ├── short_term.py      # Current conversation
│   ├── long_term.py       # Persistent memory
│   └── manager.py         # Memory manager
│
├── vectordb/              # Vector database
│   ├── base.py            # Base vector store interface
│   └── qdrant.py          # Qdrant implementation
│
├── rag/                   # Retrieval-Augmented Generation
│   ├── retriever.py       # Retrieve relevant documents
│   ├── generator.py       # Generate response with context
│   └── sources/           # Data sources
│       ├── pdf.py         # PDF loader
│       └── web.py         # Web scraper
│
├── storage/               # Persistent storage
│   ├── checkpoint.py      # Save/load agent state
│   └── serializer.py      # Serialize objects
│
├── lifecycle/             # Agent lifecycle management
│   ├── manager.py         # Start, stop, pause agents
│   └── healer.py          # Auto-recover failed agents
│
├── communication/         # Inter-agent communication
│   ├── message.py         # Message format
│   └── broker.py          # Message broker (pub/sub)
│
├── compliance/            # Safety & compliance
│   ├── filter.py          # Content filtering
│   └── rate_limiter.py    # Rate limiting
│
└── utils/                 # Utilities
    ├── logger.py          # Logging
    └── config.py          # Configuration
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
    ▼
core/base_agent.py (real logic)
    │
    ├──► llm/client.py (to call LLM)
    │        │
    │        ▼
    │    llm/providers/openai.py (actual API call)
    │
    ├──► tools/registry.py (to find tools)
    │        │
    │        ▼
    │    tools/builtin/search.py (execute tool)
    │
    └──► memory/manager.py (to store/retrieve memory)
             │
             ▼
         vectordb/qdrant.py (semantic search)
```

### 2. User Creates a Swarm

```
User Code
    │
    ▼
swarm.py (top-level)
    │
    ▼
core/base_swarm.py (orchestration logic)
    │
    ├──► core/base_agent.py (run each agent)
    │
    ├──► communication/broker.py (agents talk to each other)
    │
    └──► lifecycle/manager.py (manage agent states)
```

### 3. Agent Uses RAG

```
Agent needs information
    │
    ▼
rag/retriever.py
    │
    ├──► vectordb/qdrant.py (find similar documents)
    │
    └──► rag/sources/pdf.py (load source documents)
    
    │
    ▼
rag/generator.py
    │
    └──► llm/client.py (generate response with context)
```

---

## Example Flow: Complete Request

```
1. User: "Search for Python tutorials and summarize"
         │
         ▼
2. swarm.py → Swarm receives task
         │
         ▼
3. core/base_swarm.py → Assigns task to Agent
         │
         ▼
4. core/base_agent.py → Agent thinks about task
         │
         ▼
5. llm/providers/openai.py → LLM decides to use search tool
         │
         ▼
6. tools/builtin/search.py → Executes web search
         │
         ▼
7. memory/manager.py → Stores search results
         │
         ▼
8. llm/providers/openai.py → LLM summarizes results
         │
         ▼
9. Return summary to user
```

---

## Why This Structure?

| Layer | Purpose |
|-------|---------|
| **Top-level** (`agent.py`, `swarm.py`) | Simple API for users |
| **core/** | Core logic, can be extended |
| **llm/** | Swap providers without changing agent code |
| **tools/** | Add new tools without changing agent code |
| **memory/** | Different memory backends |
| **vectordb/** | Different vector databases |

This separation allows:
- Easy testing (mock any layer)
- Easy extension (add new providers/tools)
- Clean imports for users

---

## Import Hierarchy

```
__init__.py imports from:
    ├── agent.py (which uses core/)
    ├── swarm.py (which uses core/)
    └── tool.py (which uses tools/)

core/ imports from:
    ├── llm/
    ├── tools/
    ├── memory/
    └── communication/

llm/ imports from:
    └── utils/

tools/ imports from:
    └── utils/

rag/ imports from:
    ├── llm/
    └── vectordb/
```

---

## Summary

1. **Top-level files** = Simple API for users
2. **Subfolders** = Real implementation
3. **Each folder** = One responsibility
4. **Files call each other** through clean interfaces
5. **User only sees** `Agent`, `Swarm`, `Tool`
