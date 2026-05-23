<p align="center">
  <img src="https://raw.githubusercontent.com/nik0811/agentic-swarm/master/assets/banner.png" alt="Agentic Swarm Banner" width="100%">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/nik0811/agentic-swarm/master/assets/logo.png" alt="Agentic Swarm Logo" width="120">
</p>

<p align="center">
  <strong>Build immortal, self-healing multi-agent AI systems</strong>
</p>

<p align="center">
  <a href="https://github.com/nik0811/agentic-swarm/actions/workflows/ci.yml"><img src="https://github.com/nik0811/agentic-swarm/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/agentic-swarm/"><img src="https://img.shields.io/pypi/v/agentic-swarm.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/agentic-swarm/"><img src="https://img.shields.io/pypi/dm/agentic-swarm" alt="Downloads"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python"></a>
  <a href="https://github.com/nik0811/agentic-swarm/stargazers"><img src="https://img.shields.io/github/stars/nik0811/agentic-swarm" alt="Stars"></a>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="docs/">Documentation</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/📖-README-blue" alt="README"></a>
  <a href=".github/CODE_OF_CONDUCT.md"><img src="https://img.shields.io/badge/🤝-Code%20of%20Conduct-green" alt="Code of Conduct"></a>
  <a href=".github/CONTRIBUTING.md"><img src="https://img.shields.io/badge/👥-Contributing-orange" alt="Contributing"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/📜-Apache%202.0-red" alt="License"></a>
  <a href=".github/SECURITY.md"><img src="https://img.shields.io/badge/🔒-Security-purple" alt="Security"></a>
</p>

---

## What is Agentic Swarm?

Agentic Swarm is a production-grade SDK for building multi-agent AI systems where agents:

- **Never die** — Auto-heal on failure with state recovery
- **Spawn children** — Dynamically create sub-agents for complex subtasks  
- **Route intelligently** — Pick the optimal LLM based on task complexity
- **Remember everything** — Tiered memory with vector-indexed long-term storage
- **Stay secure** — Audit logs, encryption, RBAC, and data isolation

## Highlights

<p align="center">
  <img src="https://img.shields.io/badge/423-Tests%20Passing-success?style=for-the-badge" alt="Tests Passing">
  <img src="https://img.shields.io/badge/7-LLM%20Providers-blue?style=for-the-badge" alt="LLM Providers">
  <img src="https://img.shields.io/badge/27-Examples-orange?style=for-the-badge" alt="Examples">
  <img src="https://img.shields.io/badge/0-External%20DBs-purple?style=for-the-badge" alt="External DBs">
</p>

## Features

| Feature | Description |
|---------|-------------|
| **Immortal Agents** | Auto-heal on failure with state recovery |
| **Dynamic Spawning** | Create sub-agents at runtime |
| **7 LLM Providers** | OpenAI, Anthropic, Bedrock, Gemini, Groq, Ollama, vLLM |
| **Smart Routing** | Cost/speed/quality optimized model selection |
| **Tiered Memory** | Core + Recall + Archival (vector-indexed) |
| **Never-Forget Memory** | Compress, store, search, inject memories across sessions |
| **RAG Pipeline** | Chunk → Embed → Retrieve (dense+BM25+RRF) → Rerank |
| **Hybrid Search** | Dense vectors + BM25 sparse + Reciprocal Rank Fusion |
| **Sandbox Isolation** | CPU/memory limits, data isolation per agent |
| **Security** | Audit logs, AES-256 encryption, RBAC |

## Installation

```bash
pip install agentic-swarm
```

With optional providers:

```bash
pip install agentic-swarm[openai]      # OpenAI
pip install agentic-swarm[anthropic]   # Anthropic
pip install agentic-swarm[bedrock]     # AWS Bedrock
pip install agentic-swarm[all]         # Everything
```

## Quick Start

```python
import asyncio
from agentic_swarm import Agent, Swarm, tool

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

agent = Agent(
    name="researcher",
    role="Research and gather information",
    tools=[search_web],
)

swarm = Swarm(agents=[agent])

async def main():
    result = await swarm.run("Find information about AI agents")
    print(result)

asyncio.run(main())
```

### With LLM Provider

```python
from agentic_swarm import Agent
from agentic_swarm.llm import LLMRouter, OpenAIProvider

router = LLMRouter(strategy="quality_optimized")
router.register_provider("openai", OpenAIProvider(model="gpt-4o"))

agent = Agent(
    name="assistant",
    role="Helpful AI assistant",
    llm_router=router,
)

result = await agent.run("Explain quantum computing")
```

### Never-Forget Memory

```python
from agentic_swarm import Agent
from agentic_swarm.vectordb import InMemoryVectorDB
from agentic_swarm.rag.embedder import Embedder

# Agent that remembers across sessions
agent = Agent(
    name="assistant",
    role="Helpful assistant",
    vectordb=InMemoryVectorDB(),
    embedder=Embedder(),
    auto_archive=True,
    auto_inject_memories=True,
)

# Store memories
await agent.remember("User prefers dark mode")

# Search memories
memories = await agent.recall("user preferences")

# Run task - automatically injects relevant memories
result = await agent.run("What are my preferences?")
```

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | Installation and first steps |
| [Configuration](docs/configuration.md) | All configurable parameters |
| [API Reference](docs/api-reference.md) | Complete API documentation |
| [Examples](docs/examples.md) | Code examples and tutorials |
| [Architecture](docs/ARCHITECTURE.md) | System design |

## Examples

```bash
# Full SDK showcase
python examples/full_showcase.py --provider openai

# With AWS Bedrock
python examples/full_showcase.py --provider bedrock

# Demo mode (no LLM)
python examples/full_showcase.py --skip-llm
```

See [examples/](examples/) for working examples covering all features.

## Contributing

We welcome contributions! Please see our contributing guidelines.

| Resource | Link |
|----------|------|
| 📖 README | [README.md](README.md) |
| 🤝 Code of Conduct | [CODE_OF_CONDUCT.md](.github/CODE_OF_CONDUCT.md) |
| 👥 Contributing | [CONTRIBUTING.md](.github/CONTRIBUTING.md) |
| 📜 License | [Apache 2.0](LICENSE) |
| 🔒 Security | [SECURITY.md](.github/SECURITY.md) |

### Development Setup

```bash
git clone https://github.com/nik0811/agentic-swarm.git
cd agentic-swarm
python -m venv env && source env/bin/activate
pip install -e ".[dev,all]"
pytest tests/ -v
```

## Roadmap

- [x] 7 LLM Providers (OpenAI, Anthropic, Bedrock, Gemini, Groq, Ollama, vLLM)
- [x] Tiered Memory (Core + Recall + Archival)
- [x] RAG Pipeline with Hybrid Search
- [x] Agent Sandbox & Data Isolation
- [x] Never-Forget Memory
- [ ] Web UI Dashboard
- [ ] Distributed Multi-Node Swarms
- [ ] OpenTelemetry Integration

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with ❤️ for the AI community</sub>
</p>
