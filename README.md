# Agentic Swarm SDK

A plug-and-play SDK for building immortal, self-healing multi-agent AI systems with SOC2 compliance built-in.

## Features

- **Immortal Agents** - Never die, auto-heal on failure, automatic restart with state recovery
- **Dynamic Spawning** - Agents spawn sub-agents based on task complexity
- **Isolated Execution** - Each agent runs in isolation, no user data leakage
- **Tiered Memory** - Core (identity), Recall (working), Archival (long-term vector storage)
- **Smart LLM Routing** - Route to optimal model based on task complexity
- **Token Management** - Send only required context, compress when needed
- **RAG Pipeline** - Chunk, embed, retrieve, rerank for knowledge augmentation
- **SOC2 Compliance** - Audit logs, encryption, RBAC, data isolation from day one

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AGENTIC SWARM                           │
├─────────────────────────────────────────────────────────────┤
│  Orchestrator (Supervisor)                                  │
│       │                                                     │
│       ▼                                                     │
│  Secure Message Bus (Encrypted)                             │
│       │                                                     │
│       ├──► Agent A ──► [Sandbox] ──► [Healer]              │
│       ├──► Agent B ──► [Sandbox] ──► [Healer]              │
│       └──► Agent N ──► [Sandbox] ──► [Healer]              │
│                                                             │
│  Memory: Core │ Recall │ Archival (Vector DB)              │
│  LLM Router: Classify → Budget → Compress → Route          │
│  RAG: Chunk → Embed → Retrieve → Rerank                    │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install agentic-swarm
```

With optional dependencies:

```bash
pip install agentic-swarm[openai]      # OpenAI provider
pip install agentic-swarm[anthropic]   # Anthropic provider
pip install agentic-swarm[qdrant]      # Qdrant vector DB
pip install agentic-swarm[all]         # Everything
```

## Quick Start

```python
from agentic_swarm import Agent, Swarm, tool

# Define a tool
@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

# Create an agent
researcher = Agent(
    name="researcher",
    role="Research and gather information",
    tools=[search_web],
)

# Create a swarm and run
swarm = Swarm(agents=[researcher])
result = await swarm.run("Find information about AI agents")
```

## Memory System

```python
from agentic_swarm import Agent

agent = Agent(
    name="assistant",
    role="Helpful assistant with memory",
)

# Core memory - immutable identity (set at creation)
# Recall memory - working context (auto-managed sliding window)
# Archival memory - long-term storage (vector indexed)

# Store to archival memory
await agent.memory.archive("User prefers concise responses")

# Search archival memory
results = await agent.memory.search("user preferences")
```

## Multi-Agent Swarm

```python
from agentic_swarm import Agent, Swarm

researcher = Agent(name="researcher", role="Research topics")
writer = Agent(name="writer", role="Write content")
reviewer = Agent(name="reviewer", role="Review and improve")

swarm = Swarm(
    agents=[researcher, writer, reviewer],
    strategy="sequential",  # or "parallel", "adaptive"
)

result = await swarm.run("Write an article about quantum computing")
```

## Dynamic Sub-Agent Spawning

```python
from agentic_swarm import Agent

agent = Agent(name="coordinator", role="Coordinate complex tasks")

# Agent can spawn sub-agents at runtime
async def handle_complex_task(task):
    # Spawns isolated sub-agent, inherits only task context
    sub_agent = await agent.spawn(
        name="specialist",
        role="Handle specific subtask",
        task=task,
    )
    result = await sub_agent.run()
    return result  # Sub-agent auto-terminates
```

## LLM Routing

```python
from agentic_swarm.llm import LLMRouter

router = LLMRouter(
    strategy="cost_optimized",  # or "speed_optimized", "quality_optimized"
    providers=["openai", "anthropic", "ollama"],
)

# Automatically routes based on task complexity:
# - Simple tasks → Local/cheap models (Llama-8B, GPT-3.5)
# - Complex tasks → Powerful models (GPT-4o, Claude-3.5)
# - Expert tasks → Best models (Claude-3-opus, o1)
```

## RAG Pipeline

```python
from agentic_swarm.rag import RAGPipeline
from agentic_swarm.vectordb import Qdrant

# Initialize
vectordb = Qdrant(url="localhost:6333")
rag = RAGPipeline(vectordb=vectordb)

# Ingest documents
await rag.ingest("./docs/", chunk_strategy="recursive")

# Query with retrieval
context = await rag.retrieve("How do I configure autoscaling?", top_k=5)
```

## Project Structure

```
agentic_swarm/
├── agent.py              # Base Agent class
├── swarm.py              # Swarm orchestrator
├── tool.py               # Tool decorator
├── core/                 # Config, types, registry
├── memory/               # Core, Recall, Archival memory
├── lifecycle/            # Supervisor, healer, spawner, sandbox
├── communication/        # Message bus, channels, protocols
├── llm/                  # Router, classifier, token manager, providers
├── rag/                  # Pipeline, chunker, embedder, retriever
├── vectordb/             # Qdrant, Chroma, Pinecone, pgvector
├── compliance/           # Audit, encryption, isolation, access
├── storage/              # Local, Redis backends
└── utils/                # Crypto, serialization, validation
```

## Documentation

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture diagrams and design decisions.

## License

Copyright (c) 2026 Nikhil Kumar. All rights reserved.

This software may be viewed and used for personal, educational, or evaluation purposes only. Commercial use, redistribution, sublicensing, hosting as a service, or resale is prohibited without explicit written permission from the author.

See [LICENSE](./LICENSE) for details.
