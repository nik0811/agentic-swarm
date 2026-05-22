<p align="center">
  <h1 align="center">Agentic Swarm</h1>
  <p align="center">
    A plug-and-play SDK for building immortal, self-healing multi-agent AI systems with SOC2 compliance built-in.
  </p>
</p>

<p align="center">
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#api-reference">API Reference</a> •
  <a href="#examples">Examples</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## Why Agentic Swarm?

Most agent frameworks give you a single agent with basic tool calling. Agentic Swarm gives you a **production-grade multi-agent operating system** where agents:

- **Never die** — auto-heal on failure with state recovery
- **Spawn children** — dynamically create sub-agents for complex subtasks
- **Route intelligently** — pick the optimal LLM model based on task complexity
- **Remember everything** — tiered memory (working context + long-term vector storage)
- **Stay compliant** — audit logs, encryption, RBAC, data isolation from day one

---

## Features

| Feature | Description |
|---------|-------------|
| **Immortal Agents** | Auto-heal on failure, automatic restart with state recovery |
| **Dynamic Spawning** | Agents create sub-agents at runtime based on task needs |
| **Isolated Execution** | Each agent runs in a sandbox — no data leakage |
| **Tiered Memory** | Core (identity), Recall (working context + auto-archive), Archival (vector-indexed) |
| **Smart LLM Routing** | Route to optimal model based on task complexity with cost/speed/quality strategies |
| **Multi-Provider** | OpenAI, Anthropic, Google Gemini, AWS Bedrock, Groq, Ollama, vLLM |
| **Token Management** | Send only required context, compress when budget is exceeded |
| **RAG Pipeline** | Chunk (fixed/recursive/semantic/code) → Embed → Retrieve (dense+BM25+RRF) → Rerank |
| **RAG Sources** | Ingest from local files, web URLs, GitHub repos, and REST APIs |
| **Query Engine** | Query expansion, HyDE, hybrid retrieval, cross-encoder reranking |
| **Communication** | Pub/sub message bus + bidirectional point-to-point channels |
| **Persistent Storage** | Local file-based (dev) or Redis (production) with TTL support |
| **SOC2 Compliance** | Immutable audit logs, encryption at rest, RBAC, data isolation |
| **Access Control** | Fine-grained permission, tool, and model ACLs per agent |
| **Agent Registry** | Global singleton registry for tracking all active agents/swarms |
| **Fully Configurable** | Every hardcoded default can be overridden via `SDKConfig` |

---

## Installation

```bash
pip install agentic-swarm
```

### Optional Dependencies

```bash
pip install agentic-swarm[openai]       # OpenAI provider
pip install agentic-swarm[anthropic]    # Anthropic provider
pip install agentic-swarm[bedrock]      # AWS Bedrock provider
pip install agentic-swarm[gemini]       # Google Gemini provider
pip install agentic-swarm[qdrant]       # Qdrant vector DB
pip install agentic-swarm[crypto]       # Encryption support
pip install agentic-swarm[all]          # Everything
```

### Development Install

```bash
git clone https://github.com/nik0811/agentic-swarm.git
cd agentic-swarm
python -m venv env && source env/bin/activate
pip install -e ".[dev,all]"
pytest tests/ -v
```

---

## Quick Start

```python
import asyncio
from agentic_swarm import Agent, Swarm, tool

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

researcher = Agent(
    name="researcher",
    role="Research and gather information",
    tools=[search_web],
)

swarm = Swarm(agents=[researcher])

async def main():
    result = await swarm.run("Find information about AI agents")
    print(result)

asyncio.run(main())
```

### With LLM Routing (Bedrock)

```python
import os
from agentic_swarm import Agent, Swarm, tool
from agentic_swarm.llm import LLMRouter, BedrockProvider

# Create provider
provider = BedrockProvider(
    model=os.environ["BEDROCK_MODEL_ID"],
    region=os.environ["BEDROCK_REGION"],
    access_key_id=os.environ["BEDROCK_ACCESS_KEY_ID"],
    secret_access_key=os.environ["BEDROCK_SECRET_ACCESS_KEY"],
)

# Create router
router = LLMRouter(strategy="quality_optimized")
router.register_provider("bedrock", provider)

# Create agent with router
agent = Agent(
    name="assistant",
    role="Helpful AI assistant",
    llm_router=router,
    llm=os.environ["BEDROCK_MODEL_ID"],
)

result = await agent.run("Explain quantum computing")
```

---

## Configuration

Every hardcoded value in the SDK can be overridden. Configuration is managed through `SDKConfig`.

### Global Configuration

```python
from agentic_swarm import set_config, SDKConfig
from agentic_swarm.core.config import (
    LLMConfig, MemoryConfig, RAGConfig,
    LifecycleConfig, ComplianceConfig,
)

set_config(SDKConfig(
    llm=LLMConfig(
        default_temperature=0.5,
        default_max_tokens=8192,
        default_strategy="quality_optimized",
    ),
    memory=MemoryConfig(
        recall_max_size=200,
        recall_max_tokens=16000,
    ),
    rag=RAGConfig(
        chunk_size=1024,
        chunk_overlap=100,
        embedding_model="text-embedding-3-large",
    ),
    lifecycle=LifecycleConfig(
        healer_max_retries=5,
        spawner_max_depth=5,
        spawner_max_children=20,
    ),
))
```

### All Configurable Parameters

<details>
<summary><strong>LLM Configuration</strong></summary>

| Parameter | Default | Description |
|-----------|---------|-------------|
| `default_model` | `"gpt-4o-mini"` | Default model when none specified |
| `default_temperature` | `0.7` | Default generation temperature |
| `default_max_tokens` | `4096` | Default max output tokens |
| `default_strategy` | `"cost_optimized"` | Routing strategy: `cost_optimized`, `speed_optimized`, `quality_optimized` |
| `default_provider` | `"openai"` | Default LLM provider |
| `reserved_output_tokens` | `4000` | Tokens reserved for output in budget calculation |
| `system_prompt_tokens` | `500` | Estimated system prompt token count |
| `token_encoding` | `"cl100k_base"` | Tiktoken encoding name |
| `tokens_per_message_overhead` | `4` | Token overhead per message |
| `tokens_per_request_overhead` | `2` | Token overhead per request |

</details>

<details>
<summary><strong>Task Classifier Configuration</strong></summary>

| Parameter | Default | Description |
|-----------|---------|-------------|
| `trivial_word_threshold` | `10` | Max words for trivial classification |
| `moderate_word_threshold` | `30` | Max words for moderate classification |
| `classification_temperature` | `0.0` | Temperature for LLM-based classification |
| `keywords` | `{...}` | Keyword mapping for complexity detection |

Override keywords to customize task classification:

```python
from agentic_swarm.core.config import ClassifierConfig

ClassifierConfig(keywords={
    "trivial": ["hello", "hi", "yes", "no"],
    "moderate": ["summarize", "explain", "list"],
    "complex": ["design", "architect", "implement"],
    "expert": ["research", "novel", "breakthrough"],
})
```

</details>

<details>
<summary><strong>Memory Configuration</strong></summary>

| Parameter | Default | Description |
|-----------|---------|-------------|
| `recall_max_size` | `100` | Maximum entries in recall memory |
| `recall_max_tokens` | `8000` | Token budget for recall memory |
| `archival_collection_prefix` | `"archival"` | Prefix for archival memory collections |
| `archival_list_limit` | `100` | Max entries returned from archival listing |
| `core_memory_version` | `"1.0.0"` | Version string for core memory schema |

</details>

<details>
<summary><strong>Agent Configuration</strong></summary>

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_iterations` | `10` | Max ReAct loop iterations per task |
| `default_timeout` | `300` | Agent timeout in seconds |

</details>

<details>
<summary><strong>Lifecycle Configuration</strong></summary>

| Parameter | Default | Description |
|-----------|---------|-------------|
| `supervisor_check_interval` | `5.0` | Seconds between health checks |
| `supervisor_max_errors` | `3` | Errors before marking agent unhealthy |
| `healer_max_retries` | `3` | Max auto-heal retry attempts |
| `healer_backoff_factor` | `2.0` | Exponential backoff multiplier |
| `healer_max_backoff` | `30.0` | Max backoff delay in seconds |
| `spawner_max_depth` | `3` | Max depth of agent spawn tree |
| `spawner_max_children` | `10` | Max children per agent |

</details>

<details>
<summary><strong>Sandbox Configuration</strong></summary>

| Parameter | Default | Description |
|-----------|---------|-------------|
| `cpu_limit` | `1.0` | CPU cores available to sandbox |
| `memory_limit_mb` | `512` | Memory limit in MB |
| `timeout_seconds` | `60` | Sandbox execution timeout |
| `allow_network` | `True` | Whether sandbox has network access |

</details>

<details>
<summary><strong>RAG Configuration</strong></summary>

| Parameter | Default | Description |
|-----------|---------|-------------|
| `default_chunk_strategy` | `"recursive"` | Chunking strategy: `fixed`, `recursive`, `semantic` |
| `chunk_size` | `512` | Target chunk size in characters |
| `chunk_overlap` | `50` | Overlap between chunks |
| `chunk_separators` | `["\n\n", "\n", ". ", " "]` | Separators for recursive chunking |
| `embedding_model` | `"text-embedding-3-small"` | OpenAI embedding model |
| `embedding_dimensions` | `1536` | Embedding vector dimensions |
| `default_collection` | `"documents"` | Default vector DB collection name |
| `ingest_extensions` | `[".txt", ".md", ".py", ...]` | File extensions to ingest |
| `retrieval_strategy` | `"dense"` | Strategy: `dense`, `sparse`, `hybrid` |
| `rerank_initial_limit` | `20` | Candidates to fetch before reranking |
| `rerank_vector_weight` | `0.7` | Vector score weight in hybrid reranking |
| `rerank_keyword_weight` | `0.3` | Keyword score weight in hybrid reranking |

</details>

<details>
<summary><strong>Context Compressor Configuration</strong></summary>

| Parameter | Default | Description |
|-----------|---------|-------------|
| `preserve_recent` | `5` | Recent messages to always preserve |
| `summary_truncate_length` | `100` | Max chars per message in summary |
| `summary_safety_factor` | `0.9` | Safety margin for token budget |
| `min_fact_length` | `20` | Min chars for extracted facts |
| `max_facts` | `10` | Max key facts to extract |
| `relevance_threshold` | `0.3` | Min relevance score for filtering |

</details>

<details>
<summary><strong>Vector DB Configuration</strong></summary>

| Parameter | Default | Description |
|-----------|---------|-------------|
| `qdrant_host` | `"localhost"` | Qdrant server host |
| `qdrant_port` | `6333` | Qdrant server port |
| `qdrant_prefer_grpc` | `False` | Use gRPC instead of HTTP |

</details>

<details>
<summary><strong>Compliance Configuration</strong></summary>

| Parameter | Default | Description |
|-----------|---------|-------------|
| `audit_query_limit` | `100` | Max audit entries per query |
| `encryption_iterations` | `480000` | PBKDF2 iterations for key derivation |
| `encryption_key_length` | `32` | Encryption key length in bytes |
| `encryption_salt_length` | `16` | Salt length in bytes |

</details>

<details>
<summary><strong>Built-in Tools Configuration</strong></summary>

| Parameter | Default | Description |
|-----------|---------|-------------|
| `shell_timeout` | `30` | Shell command timeout in seconds |
| `web_fetch_timeout` | `30` | HTTP fetch timeout in seconds |
| `web_fetch_max_chars` | `10000` | Max characters from web fetch |
| `web_search_max_results` | `10` | Max search results to return |
| `memory_search_limit` | `5` | Default memory search result limit |
| `memory_recall_depth` | `10` | Default recall history depth |

</details>

### Reset Configuration

```python
from agentic_swarm import reset_config

reset_config()  # Restores all defaults
```

---

## API Reference

### Agent

```python
from agentic_swarm import Agent

agent = Agent(
    name="my-agent",
    role="Description of what this agent does",
    tools=[tool1, tool2],           # List of @tool decorated functions
    llm="us.anthropic.claude-opus-4-6-v1",  # Force a specific model
    llm_router=router,              # LLM router instance
    max_iterations=10,              # Max ReAct loop cycles
    parent=None,                    # Parent agent (for sub-agents)
)

# Run a task
result = await agent.run("Do something")

# Create child agent
child = await agent.create_agent(name="child", role="Sub-task handler")

# Send message to another agent
await agent.send(other_agent, "Here's some data")

# Terminate agent
await agent.terminate()
```

### Swarm

```python
from agentic_swarm import Swarm

swarm = Swarm(agents=[agent1, agent2, agent3])

# Execution strategies
result = await swarm.run("task", strategy="parallel")     # All agents work simultaneously
result = await swarm.run("task", strategy="sequential")   # Each builds on previous
result = await swarm.run("task", strategy="adaptive")     # Auto-select based on task

# Broadcast message to all agents
await swarm.broadcast("Important update for all agents")

# Terminate all
await swarm.terminate_all()
```

### Tool Decorator

```python
from agentic_swarm import tool

@tool
def my_tool(query: str, limit: int = 10) -> str:
    """Tool description shown to the LLM.
    
    Args:
        query: The search query
        limit: Max results to return
    """
    return f"Found {limit} results for {query}"

# Tools auto-generate OpenAI-compatible schemas from type hints + docstring
```

### LLM Router

```python
from agentic_swarm.llm import (
    LLMRouter, 
    OpenAIProvider, AnthropicProvider, BedrockProvider, 
    GeminiProvider, GroqProvider, OllamaProvider, VLLMProvider,
)

router = LLMRouter(strategy="cost_optimized")

# Register multiple providers
router.register_provider("openai", OpenAIProvider(model="gpt-4o"))
router.register_provider("anthropic", AnthropicProvider(model="claude-sonnet-4-20250514"))
router.register_provider("gemini", GeminiProvider(model="gemini-2.0-flash"))
router.register_provider("groq", GroqProvider(model="llama-3.3-70b-versatile"))
router.register_provider("ollama", OllamaProvider(model="llama3.2", base_url="http://localhost:11434"))
router.register_provider("vllm", VLLMProvider(model="meta-llama/Llama-3-8B", base_url="http://gpu-server:8000"))
router.register_provider("bedrock", BedrockProvider(
    model="us.anthropic.claude-opus-4-6-v1",
    region="us-east-1",
    access_key_id="...",
    secret_access_key="...",
))

# Custom routing rules
router.set_routing({
    TaskComplexity.TRIVIAL: {"cost_optimized": ["gpt-4o-mini"]},
    TaskComplexity.MODERATE: {"cost_optimized": ["gpt-4o"]},
    TaskComplexity.COMPLEX: {"cost_optimized": ["claude-sonnet-4-20250514"]},
    TaskComplexity.EXPERT: {"cost_optimized": ["us.anthropic.claude-opus-4-6-v1"]},
})

# Direct routing
response = await router.route("Explain recursion", system_prompt="You are a teacher")
```

### Memory System

```python
from agentic_swarm.memory import MemoryController, CoreMemory, RecallMemory, ArchivalMemory
from agentic_swarm.vectordb import InMemoryVectorDB
from agentic_swarm.rag import MockEmbedder

# Full memory controller
controller = MemoryController(
    agent_id="agent-1",
    name="assistant",
    persona="Helpful AI",
    vectordb=InMemoryVectorDB(),
    embedder=MockEmbedder(),
)

# Core memory (read-only identity)
controller.core.to_prompt()       # System prompt with identity
controller.core.name              # Agent name
controller.core.persona           # Agent role/persona

# Recall memory (working context)
controller.push_recall("User said hello", role="user")
messages = controller.get_recall_messages(limit=5)
results = controller.search_recall("hello")

# Archival memory (long-term vector storage)
await controller.store_archival("User prefers concise answers")
results = await controller.search_archival("preferences", limit=5)

# Combined search across all memory tiers
results = await controller.search_all("important topic")
```

### RAG Pipeline

```python
from agentic_swarm.rag import RAGPipeline, Embedder, Chunker, Retriever
from agentic_swarm.vectordb import QdrantClient

vectordb = QdrantClient(url="localhost:6333")
rag = RAGPipeline(vectordb=vectordb)

# Ingest content
await rag.ingest("Document text here", collection="knowledge")
await rag.ingest_file("./docs/guide.md", collection="knowledge")
await rag.ingest_directory("./docs/", collection="knowledge")

# Query
result = await rag.query("How do I deploy?", collection="knowledge", limit=5)
print(result.context)   # Merged relevant context
print(result.sources)   # Source attribution
print(result.chunks)    # Individual retrieved chunks
```

### Lifecycle Management

```python
from agentic_swarm.lifecycle import Supervisor, Healer, Spawner, Sandbox

# Health monitoring
supervisor = Supervisor(check_interval=5.0, max_errors=3)
supervisor.register(agent)
status = await supervisor.health_check(agent)
await supervisor.start_monitoring()

# Auto-healing
healer = Healer(max_retries=3, backoff_factor=2.0)
snapshot = healer.snapshot(agent)
recovered = await healer.recover(agent)

# Dynamic spawning
spawner = Spawner(max_depth=3, max_children=10)
spawner.register_root(coordinator.id)
child = await spawner.spawn(coordinator, name="worker", role="Process data")

# Sandboxed execution
sandbox = Sandbox(cpu_limit=1.0, memory_limit_mb=512, timeout_seconds=60)
result = await sandbox.execute(agent.run, "task")
```

### SOC2 Compliance

```python
from agentic_swarm.compliance import AuditLogger, Encryption, DataIsolation, AuditEventType

# Immutable audit log
audit = AuditLogger()
audit.log(AuditEventType.AGENT_CREATED, agent_id="123", data={"name": "agent"})
entries = audit.query(agent_id="123")
valid = audit.verify_integrity()  # Verify checksum chain

# Encryption at rest
crypto = Encryption(Encryption.generate_key())
encrypted = crypto.encrypt("sensitive data")
decrypted = crypto.decrypt_string(encrypted)
crypto.rotate_key(new_key)  # Key rotation

# Data isolation + RBAC
isolation = DataIsolation()
isolation.register_agent("agent-1", tenant_id="tenant-1")
isolation.validate_access("agent-1", "agent:agent-1:data")  # True
isolation.validate_access("agent-1", "agent:agent-2:data")  # False
```

### Access Control

```python
from agentic_swarm.compliance.access import AccessController, Permission, AccessPolicy

controller = AccessController()

# Set fine-grained policy for an agent
policy = AccessPolicy(
    agent_id="agent-1",
    permissions={Permission.READ, Permission.WRITE, Permission.EXECUTE},
    allowed_tools=["web_search", "read_file"],
    denied_tools=["run_shell"],
    allowed_models=["gpt-4o-mini", "gpt-4o"],
    rate_limit_per_minute=30,
)
controller.set_policy("agent-1", policy)

# Check permissions
controller.check_permission("agent-1", Permission.EXECUTE)   # True
controller.check_permission("agent-1", Permission.ADMIN)     # False
controller.check_tool_access("agent-1", "web_search")        # True
controller.check_tool_access("agent-1", "run_shell")         # False
controller.check_model_access("agent-1", "gpt-4o")           # True
```

### Inter-Agent Communication

```python
from agentic_swarm.communication import MessageBus, Channel, MessageRouter, Message, MessageType

# Message Bus (pub/sub)
bus = MessageBus()
bus.subscribe("agent-1", handler_fn)
bus.subscribe_topic("alerts", alert_handler)

await bus.publish(Message(
    type=MessageType.TASK_DELEGATE,
    sender_id="coordinator",
    receiver_id="agent-1",
    content="Research quantum computing",
))

await bus.broadcast("coordinator", "System update", topic="alerts")

# Direct Channels (point-to-point)
router = MessageRouter()
channel = router.create_channel("agent-a", "agent-b")
await channel.send("agent-a", "Here's the data you requested")
msg = await channel.receive("agent-b", timeout=5.0)
```

### Storage (Persistence)

```python
from agentic_swarm.storage import LocalStorage, RedisStorage

# Local file-based storage (dev/single-node)
storage = LocalStorage(base_dir=".data/storage")
await storage.set("agent:state:123", {"status": "running", "task": "research"})
state = await storage.get("agent:state:123")
await storage.set("session:token", "abc123", ttl=3600)  # Expires in 1 hour
keys = await storage.list_keys(prefix="agent:")

# Redis storage (distributed/production)
redis_store = RedisStorage(url="redis://localhost:6379", prefix="swarm:")
await redis_store.set("agent:state:123", {"status": "running"})
batch = await redis_store.get_many(["key1", "key2", "key3"])
```

### RAG Sources

```python
from agentic_swarm.rag.sources import FileSource, WebSource, GitHubSource, APISource

# Ingest from local files
source = FileSource("./docs/", extensions=[".md", ".txt"], recursive=True)
docs = await source.load()

# Ingest from web URLs
web = WebSource(urls=["https://docs.example.com/guide", "https://docs.example.com/api"])
docs = await web.load()

# Ingest from GitHub repo
github = GitHubSource(repo="owner/repo", branch="main", path="docs/", token="ghp_...")
docs = await github.load()

# Ingest from REST API
api = APISource(endpoints=[
    {"url": "https://api.example.com/articles", "content_field": "body", "source_field": "title"},
])
docs = await api.load()

# Use with RAG pipeline
from agentic_swarm.rag import RAGPipeline
pipeline = RAGPipeline(vectordb=vectordb)
await pipeline.ingest_source(github, collection="knowledge")
```

### RAG Query Engine (Advanced)

```python
from agentic_swarm.rag import RAGPipeline, Retriever, Reranker, QueryEngine, Chunker

# Full pipeline with all features
pipeline = RAGPipeline(
    vectordb=vectordb,
    chunker=Chunker(strategy="code", chunk_size=512),  # Code-aware chunking
    reranker=Reranker(strategy="cross_encoder"),
    llm_provider=openai_provider,
    retrieval_strategy="hybrid",           # Dense + BM25 with RRF fusion
    enable_query_expansion=True,           # Generate related queries
    enable_hyde=True,                      # Hypothetical Document Embedding
)

# Ingest code files (auto-detects code-aware chunking for .py/.js/.ts)
await pipeline.ingest_file("./src/auth.py")
await pipeline.ingest_directory("./src/", extensions=[".py", ".ts"])

# Query with full engine (expansion + HyDE + rerank + LLM answer)
result = await pipeline.query("How does authentication work?", use_query_engine=True)
print(result.context)    # LLM-generated answer grounded in code
print(result.sources)    # Source attribution
```

### Routing Strategies

```python
from agentic_swarm.llm import LLMRouter
from agentic_swarm.llm.strategies import CostOptimizedStrategy, SpeedOptimizedStrategy, QualityOptimizedStrategy

# Strategy objects can rank models
cost_strategy = CostOptimizedStrategy()
ranked = cost_strategy.rank_models(
    ["gpt-4o", "gpt-4o-mini", "claude-3-opus-20240229"],
    model_info={"gpt-4o": {"input_cost": 0.005}, "gpt-4o-mini": {"input_cost": 0.00015}, ...}
)
# → ["gpt-4o-mini", "gpt-4o", "claude-3-opus-20240229"]  (cheapest first)

# Strategies auto-select best model for complexity
quality = QualityOptimizedStrategy()
model = quality.select(providers_dict, complexity="expert")  # Returns best model
```

### Agent Registry

```python
from agentic_swarm.core.registry import AgentRegistry

registry = AgentRegistry()

# Register agents and swarms
registry.register("agent-1", agent_instance)
registry.register("swarm-1", swarm_instance)

# Query
agent = registry.get("agent-1")
all_agents = registry.list_agents()
count = registry.count()

# Cleanup
registry.unregister("agent-1")
registry.clear()
```

### Utilities

```python
from agentic_swarm.utils import (
    hash_string, generate_id, generate_token,
    serialize, deserialize,
    validate_agent_name, validate_temperature, validate_max_tokens,
)

# Cryptographic utilities
id = generate_id()                     # UUID-like unique ID
token = generate_token(32)             # Secure random hex token
digest = hash_string("data", "sha256") # SHA-256 hash

# Serialization (handles datetime, nested objects)
json_str = serialize({"created": datetime.now(), "data": [1, 2, 3]})
obj = deserialize(json_str)

# Input validation (raises ValueError on invalid)
validate_agent_name("my-agent")       # OK
validate_temperature(0.7)              # OK (0.0 - 2.0)
validate_max_tokens(4096)              # OK (1 - 1_000_000)
```

---

## Project Structure

```
agentic-swarm/
├── agentic_swarm/
│   ├── __init__.py               # Public API exports
│   ├── agent.py                  # Base Agent with ReAct loop
│   ├── swarm.py                  # Multi-agent orchestrator + message bus
│   ├── tool.py                   # @tool decorator
│   ├── core/
│   │   ├── config.py             # SDKConfig (all configurable values)
│   │   ├── types.py              # Enums, models (AgentState, TaskComplexity)
│   │   ├── exceptions.py         # Custom exception hierarchy
│   │   └── registry.py           # Global agent registry (singleton)
│   ├── memory/
│   │   ├── core_memory.py        # Immutable agent identity
│   │   ├── recall_memory.py      # Sliding window (auto-evicts, returns evicted)
│   │   ├── archival_memory.py    # Vector-indexed long-term memory
│   │   └── controller.py         # Unified interface + auto-archive + fact extraction
│   ├── communication/
│   │   ├── protocols.py          # Message types, priorities, protocols
│   │   ├── bus.py                # Pub/sub message bus
│   │   ├── channel.py            # Bidirectional point-to-point channels
│   │   └── router.py             # Message routing (channel + bus)
│   ├── llm/
│   │   ├── router.py             # Smart model routing with fallback
│   │   ├── classifier.py         # Task complexity classification
│   │   ├── token_manager.py      # Token counting and budgeting
│   │   ├── context_compressor.py # Context compression strategies
│   │   ├── base.py               # Provider interface
│   │   ├── providers/
│   │   │   ├── openai.py         # OpenAI (GPT-4o, GPT-4o-mini, o1)
│   │   │   ├── anthropic.py      # Anthropic (Claude 3.5, Claude 3)
│   │   │   ├── bedrock.py        # AWS Bedrock (Claude, Llama, Titan)
│   │   │   ├── gemini.py         # Google Gemini (2.0 Flash, 1.5 Pro)
│   │   │   ├── groq.py           # Groq (Llama, Mixtral - fast inference)
│   │   │   ├── ollama.py         # Ollama (local models)
│   │   │   └── vllm.py           # vLLM (self-hosted)
│   │   └── strategies/
│   │       ├── cost_optimized.py  # Minimize cost
│   │       ├── speed_optimized.py # Minimize latency
│   │       └── quality_optimized.py # Maximize quality
│   ├── rag/
│   │   ├── pipeline.py           # End-to-end RAG (ingest + query)
│   │   ├── chunker.py            # Fixed, recursive, semantic, code-aware
│   │   ├── embedder.py           # OpenAI embeddings + MockEmbedder
│   │   ├── retriever.py          # Dense, sparse (BM25), hybrid (RRF)
│   │   ├── reranker.py           # Cross-encoder, keyword, LLM reranking
│   │   ├── query_engine.py       # Query expansion, HyDE, context assembly
│   │   └── sources/
│   │       ├── file.py           # Local files and directories
│   │       ├── web.py            # Web URL scraping
│   │       ├── github.py         # GitHub repository files
│   │       └── api.py            # REST API endpoints
│   ├── vectordb/
│   │   ├── base.py               # Vector DB interface
│   │   └── qdrant.py             # Qdrant + InMemory implementations
│   ├── lifecycle/
│   │   ├── supervisor.py         # Health monitoring + auto-restart
│   │   ├── healer.py             # State snapshot + auto-recovery
│   │   ├── spawner.py            # Dynamic sub-agent creation (depth/children limits)
│   │   └── sandbox.py            # Isolated execution (CPU/mem/timeout)
│   ├── compliance/
│   │   ├── audit.py              # Immutable audit logging (checksum chain)
│   │   ├── encryption.py         # AES-256 encryption + key rotation
│   │   ├── isolation.py          # Data isolation + RBAC
│   │   └── access.py             # Fine-grained permission/tool/model ACLs
│   ├── storage/
│   │   ├── base.py               # Storage interface
│   │   ├── local.py              # File-based JSON storage with TTL
│   │   └── redis.py              # Redis backend (distributed)
│   ├── utils/
│   │   ├── crypto.py             # Hashing, ID generation, tokens
│   │   ├── serialization.py      # JSON serialization with datetime support
│   │   └── validation.py         # Input validation helpers
│   └── tools/
│       └── builtin/              # Built-in tools (shell, web, memory, etc.)
├── tests/                        # Full test suite (100+ tests)
├── examples/                     # Working examples
├── ARCHITECTURE.md               # System architecture documentation
├── CHANGELOG.md                  # Version history
├── pyproject.toml                # Package configuration
└── README.md                     # This file
```

---

## Examples

| Example | Description |
|---------|-------------|
| [`simple_agent.py`](examples/simple_agent.py) | Basic agent with tools |
| [`multi_agent_swarm.py`](examples/multi_agent_swarm.py) | Multi-agent parallel and sequential coordination |
| [`sub_agent_spawning.py`](examples/sub_agent_spawning.py) | Dynamic sub-agent creation at runtime |
| [`memory_usage.py`](examples/memory_usage.py) | All three memory tiers in action |
| [`rag_pipeline.py`](examples/rag_pipeline.py) | Document ingestion and retrieval |
| [`full_showcase.py`](examples/full_showcase.py) | **Complete SDK showcase with all providers** (OpenAI, Anthropic, Bedrock, Gemini, Groq, Ollama, vLLM) |
| [`full_showcase_bedrock.py`](examples/full_showcase_bedrock.py) | Full SDK showcase specifically for AWS Bedrock |
| [`immortal_swarm_bedrock.py`](examples/immortal_swarm_bedrock.py) | Full immortal swarm with AWS Bedrock, auto-healing, and agent communication |
| [`agent_collaboration_bedrock.py`](examples/agent_collaboration_bedrock.py) | Parent-child agent collaboration with Bedrock |
| [`auto_tools.py`](examples/auto_tools.py) | Automatic tool discovery and retry |
| [`custom_tools.py`](examples/custom_tools.py) | Creating and registering custom tools |
| [`communication.py`](examples/communication.py) | Message bus and channels between agents |
| [`storage_example.py`](examples/storage_example.py) | Persistent state with local and Redis storage |
| [`rag_sources.py`](examples/rag_sources.py) | Ingest from GitHub, web, and files |
| [`rag_memory_context.py`](examples/rag_memory_context.py) | RAG + Memory + Context management combined |
| [`vectordb_persistent.py`](examples/vectordb_persistent.py) | Vector database + persistent storage demo |

### Running the Full Showcase

The `full_showcase.py` example demonstrates all 19 SDK features with any LLM provider:

```bash
# Run with OpenAI (default)
python examples/full_showcase.py --provider openai

# Run with Anthropic
python examples/full_showcase.py --provider anthropic --model claude-3-5-sonnet-latest

# Run with AWS Bedrock
python examples/full_showcase.py --provider bedrock --model us.anthropic.claude-sonnet-4-6

# Run with Groq (fast inference)
python examples/full_showcase.py --provider groq --model llama-3.1-70b-versatile

# Run with Ollama (local)
python examples/full_showcase.py --provider ollama --model llama3.2

# Run with Google Gemini
python examples/full_showcase.py --provider gemini --model gemini-1.5-pro

# Run in demo mode (no LLM calls)
python examples/full_showcase.py --skip-llm
```

Features demonstrated:
1. SDKConfig - Custom configuration
2. LLM Providers - All 7 supported providers
3. Prompt Cache - Response caching
4. Agent Spawning - Parent/child agents
5. Tool Calling - Custom tools
6. Memory - Core + Recall + Archival
7. RAG Pipeline - Document ingestion & retrieval
8. Communication - Message bus
9. Swarm - Parallel execution
10. Lifecycle - Supervisor, Healer, Sandbox
11. SOC2 Compliance - Audit, Encryption, Access Control
12. Storage - Persistent local storage
13. Token Management - Budget & compression
14. Utilities - Crypto, validation, serialization
15. Registry - Agent tracking
16. Auto Tool Discovery - Dynamic tool loading

### Vector Database + Persistent Storage

The `vectordb_persistent.py` example demonstrates semantic search and data persistence:

```bash
python examples/vectordb_persistent.py
```

```python
from agentic_swarm.vectordb import InMemoryVectorDB
from agentic_swarm.rag.pipeline import RAGPipeline
from agentic_swarm.rag.chunker import Chunker
from agentic_swarm.rag.embedder import MockEmbedder
from agentic_swarm.memory.archival_memory import ArchivalMemory
from agentic_swarm.storage.local import LocalStorage

# Initialize vector database
vectordb = InMemoryVectorDB()
await vectordb.create_collection("knowledge", vector_size=384)

# Initialize RAG pipeline
embedder = MockEmbedder(dimensions=384)
chunker = Chunker(chunk_size=300, overlap=50, strategy="recursive")
rag = RAGPipeline(vectordb=vectordb, embedder=embedder, chunker=chunker)

# Ingest documents
await rag.ingest("Your document content here...", metadata={"title": "Doc 1"})

# Semantic search
results = await rag.query("How does this work?", limit=3)
for chunk in results.chunks:
    print(f"Score: {chunk['score']:.2f} - {chunk['content'][:100]}...")

# Archival memory (vector-indexed long-term storage)
archival = ArchivalMemory(agent_id="my_agent", vectordb=vectordb, embedder=embedder)
await archival.store("Important fact to remember")
memories = await archival.search("important", limit=5)

# Persistent storage (survives across sessions)
storage = LocalStorage(base_dir=".my_app_data")
await storage.set("user:preferences", {"theme": "dark", "language": "en"})
data = await storage.get("user:preferences")  # Returns {"theme": "dark", ...}

# Data persists to disk as JSON files
# Run again to see existing data loaded
```

Features:
- **InMemoryVectorDB**: Fast in-memory vector search for development
- **QdrantClient**: Production-ready vector database (requires `pip install qdrant-client`)
- **RAG Pipeline**: Chunk → Embed → Store → Retrieve → Rerank
- **Archival Memory**: Long-term vector-indexed storage for agents
- **LocalStorage**: JSON file-based persistence for development
- **RedisStorage**: Distributed persistence for production
15. Registry - Agent tracking
16. Auto Tool Discovery - Dynamic tool loading

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | For OpenAI provider | OpenAI API key |
| `OPENAI_MODEL` | For OpenAI provider | Model name (e.g. `gpt-4o`, `gpt-4o-mini`) |
| `ANTHROPIC_API_KEY` | For Anthropic provider | Anthropic API key |
| `ANTHROPIC_MODEL` | For Anthropic provider | Model name (e.g. `claude-sonnet-4-20250514`, `claude-3-haiku-20240307`) |
| `GOOGLE_API_KEY` | For Gemini provider | Google AI API key |
| `GEMINI_MODEL` | For Gemini provider | Model name (e.g. `gemini-1.5-flash`, `gemini-1.5-pro`) |
| `GROQ_API_KEY` | For Groq provider | Groq API key |
| `GROQ_MODEL` | For Groq provider | Model name (e.g. `llama-3.1-8b-instant`, `llama-3.1-70b-versatile`) |
| `AWS_ACCESS_KEY_ID` | For Bedrock provider | AWS access key ID |
| `AWS_SECRET_ACCESS_KEY` | For Bedrock provider | AWS secret access key |
| `AWS_REGION` | For Bedrock provider | AWS region (e.g. `us-east-1`) |
| `BEDROCK_MODEL_ID` | For Bedrock provider | Model ID (e.g. `us.anthropic.claude-sonnet-4-6`) |
| `OLLAMA_BASE_URL` | For Ollama provider | Server URL (default: `http://localhost:11434`) |
| `OLLAMA_MODEL` | For Ollama provider | Model name (e.g. `llama3.2`, `mistral`, `codellama`) |
| `VLLM_BASE_URL` | For vLLM provider | Server URL (default: `http://localhost:8000/v1`) |
| `VLLM_MODEL` | For vLLM provider | Model name (e.g. `meta-llama/Llama-3.1-8B-Instruct`) |

---

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_agent.py -v
pytest tests/test_memory.py -v
pytest tests/test_router.py -v

# Run with coverage
pytest tests/ --cov=agentic_swarm --cov-report=html
```

---

## Supported Models

### OpenAI
- `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `o1`, `o1-mini`

### Anthropic
- `claude-sonnet-4-20250514`, `claude-3-5-sonnet-latest`, `claude-3-opus-20240229`, `claude-3-haiku-20240307`

### Google Gemini
- `gemini-2.0-flash`, `gemini-2.0-flash-lite`, `gemini-1.5-pro`, `gemini-1.5-flash`

### AWS Bedrock
- `us.anthropic.claude-opus-4-6-v1`, `us.anthropic.claude-sonnet-4-20250514-v2:0`
- `us.meta.llama3-2-90b-instruct-v1:0`, `amazon.titan-text-premier-v1:0`
- `mistral.mistral-large-2402-v1:0`

### Groq (Fast Inference)
- `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`, `gemma2-9b-it`

### Ollama (Local)
- `llama3.2`, `mistral`, `codellama`, `phi3` (any model available locally)

### vLLM (Self-hosted)
- Any model served via vLLM's OpenAI-compatible API

---

## Contributing

We welcome contributions. Please follow these guidelines:

### Reporting Issues

1. **Search existing issues** first to avoid duplicates
2. **Use the issue template** and include:
   - Python version (`python --version`)
   - SDK version (`pip show agentic-swarm`)
   - Full error traceback
   - Minimal reproducible example
   - Expected vs actual behavior

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests for your changes
4. Ensure all tests pass: `pytest tests/ -v`
5. Lint your code: `ruff check agentic_swarm/`
6. Commit with clear messages: `git commit -m "Add: feature description"`
7. Push and open a PR against `main`

### Development Setup

```bash
git clone https://github.com/nik0811/agentic-swarm.git
cd agentic-swarm
python -m venv env && source env/bin/activate
pip install -e ".[dev,all]"
```

### Code Style

- **Formatter**: Ruff (line length 100)
- **Type hints**: Required for all public APIs
- **Docstrings**: Google style for public methods
- **Tests**: pytest + pytest-asyncio for async tests

### Commit Conventions

| Prefix | Meaning |
|--------|---------|
| `Add:` | New feature |
| `Fix:` | Bug fix |
| `Update:` | Enhancement to existing feature |
| `Refactor:` | Code restructuring (no behavior change) |
| `Docs:` | Documentation only |
| `Test:` | Test additions/modifications |

---

## Roadmap

- [x] Google Gemini provider
- [x] Groq, Ollama, vLLM providers
- [x] Inter-agent communication (message bus + channels)
- [x] Persistent storage (local + Redis)
- [x] Access control and fine-grained permissions
- [x] RAG sources (file, web, GitHub, API)
- [x] BM25 sparse retrieval + RRF fusion
- [x] Query expansion and HyDE
- [x] Code-aware chunking
- [ ] Agent-to-agent streaming
- [ ] Web UI dashboard for swarm monitoring
- [ ] Distributed multi-node swarms
- [ ] Plugin system for custom providers and tools
- [ ] OpenTelemetry tracing integration

---

## License

Copyright (c) 2026 Nikhil Kumar. All rights reserved.

This software may be viewed and used for personal, educational, or evaluation purposes only. Commercial use, redistribution, sublicensing, hosting as a service, or resale is prohibited without explicit written permission from the author.

---

<p align="center">
  Built with purpose. Designed for production.
</p>
