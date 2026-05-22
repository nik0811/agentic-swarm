# API Reference

## Core Classes

### Agent

```python
from agentic_swarm import Agent

agent = Agent(
    name="my-agent",
    role="Description of what this agent does",
    tools=[tool1, tool2],           # List of @tool decorated functions
    llm="gpt-4o",                   # Force a specific model
    llm_router=router,              # LLM router instance
    max_iterations=10,              # Max ReAct loop cycles
    parent=None,                    # Parent agent (for sub-agents)
    # Never-forget memory options
    vectordb=vectordb,              # Vector DB for archival memory
    embedder=embedder,              # Embedder for memory search
    auto_archive=True,              # Auto-archive evicted entries
    auto_inject_memories=True,      # Auto-inject relevant memories
    memory_search_limit=3,          # Max memories to inject
    # Isolation options
    sandbox_config=config,          # Sandbox resource limits
    enable_isolation=True,          # Enable data isolation
    tenant_id="company",            # Multi-tenant isolation
)

# Run a task
result = await agent.run("Do something")

# Create child agent
child = await agent.create_agent(name="child", role="Sub-task handler")

# Send message to another agent
await agent.send(other_agent, "Here's some data")

# Memory operations
await agent.remember("Important fact")  # Store in archival
memories = await agent.recall("query")  # Search archival

# Isolated execution
result = await agent.execute_isolated(func, *args)

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

---

## LLM System

### LLMRouter

```python
from agentic_swarm.llm import LLMRouter

router = LLMRouter(strategy="cost_optimized")

# Register providers
router.register_provider("openai", OpenAIProvider(model="gpt-4o"))
router.register_provider("anthropic", AnthropicProvider(model="claude-sonnet-4-20250514"))

# Direct routing
response = await router.route("Explain recursion", system_prompt="You are a teacher")
```

### Providers

```python
from agentic_swarm.llm import (
    OpenAIProvider, AnthropicProvider, BedrockProvider,
    GeminiProvider, GroqProvider, OllamaProvider, VLLMProvider,
)

# OpenAI
openai = OpenAIProvider(model="gpt-4o", api_key="...")

# Anthropic
anthropic = AnthropicProvider(model="claude-sonnet-4-20250514", api_key="...")

# AWS Bedrock
bedrock = BedrockProvider(
    model="us.anthropic.claude-opus-4-6-v1",
    region="us-east-1",
    access_key_id="...",
    secret_access_key="...",
)

# Google Gemini
gemini = GeminiProvider(model="gemini-2.0-flash", api_key="...")

# Groq
groq = GroqProvider(model="llama-3.3-70b-versatile", api_key="...")

# Ollama (local)
ollama = OllamaProvider(model="llama3.2", base_url="http://localhost:11434")

# vLLM (self-hosted)
vllm = VLLMProvider(model="meta-llama/Llama-3-8B", base_url="http://gpu-server:8000")
```

---

## Memory System

### MemoryController

```python
from agentic_swarm.memory import MemoryController

controller = MemoryController(
    agent_id="agent-1",
    name="assistant",
    persona="Helpful AI",
    vectordb=vectordb,
    embedder=embedder,
)

# Core memory (read-only identity)
controller.core.to_prompt()
controller.core.name
controller.core.persona

# Recall memory (working context)
controller.push_recall("User said hello", role="user")
messages = controller.get_recall_messages()
results = controller.search_recall("hello")

# Archival memory (long-term)
await controller.store_archival("User prefers concise answers")
results = await controller.search_archival("preferences", limit=5)

# Combined search
results = await controller.search_all("important topic")
```

---

## RAG Pipeline

```python
from agentic_swarm.rag import RAGPipeline, Chunker, Embedder
from agentic_swarm.vectordb import QdrantClient, InMemoryVectorDB

vectordb = InMemoryVectorDB()  # or QdrantClient(url="localhost:6333")
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

### RAG Sources

```python
from agentic_swarm.rag.sources import FileSource, WebSource, GitHubSource, APISource

# Local files
source = FileSource("./docs/", extensions=[".md", ".txt"], recursive=True)

# Web URLs
web = WebSource(urls=["https://docs.example.com/guide"])

# GitHub repo
github = GitHubSource(repo="owner/repo", branch="main", path="docs/", token="ghp_...")

# REST API
api = APISource(endpoints=[
    {"url": "https://api.example.com/articles", "content_field": "body"},
])

# Use with pipeline
await pipeline.ingest_source(github, collection="knowledge")
```

---

## Lifecycle Management

### Supervisor

```python
from agentic_swarm.lifecycle import Supervisor

supervisor = Supervisor(check_interval=5.0, max_errors=3)
supervisor.register(agent)
status = supervisor.health_check(agent.id)
supervisor.start_monitoring()
```

### Healer

```python
from agentic_swarm.lifecycle import Healer

healer = Healer(max_retries=3, backoff_factor=2.0)
snapshot = healer.snapshot(agent)
recovered = await healer.recover(agent, error)
```

### Spawner

```python
from agentic_swarm.lifecycle import Spawner

spawner = Spawner(max_depth=3, max_children=10)
spawner.register_root(coordinator.id)
child = await spawner.spawn(coordinator, name="worker", role="Process data")
```

### Sandbox

```python
from agentic_swarm.lifecycle import Sandbox, SandboxConfig

config = SandboxConfig(cpu_limit=1.0, memory_limit_mb=512, timeout_seconds=60)
sandbox = Sandbox(config)
result = await sandbox.execute(func, *args)
```

---

## Security & Compliance

### AuditLogger

```python
from agentic_swarm.compliance import AuditLogger, AuditEventType

audit = AuditLogger()
audit.log(AuditEventType.AGENT_CREATED, agent_id="123", data={"name": "agent"})
entries = audit.query(agent_id="123")
valid = audit.verify_integrity()
```

### Encryption

```python
from agentic_swarm.compliance import Encryption

crypto = Encryption(Encryption.generate_key())
encrypted = crypto.encrypt("sensitive data")
decrypted = crypto.decrypt_string(encrypted)
```

### AccessController

```python
from agentic_swarm.compliance.access import AccessController, Permission, AccessPolicy

controller = AccessController()
policy = AccessPolicy(
    agent_id="agent-1",
    permissions={Permission.READ, Permission.WRITE},
    allowed_tools=["web_search"],
    denied_tools=["run_shell"],
)
controller.set_policy("agent-1", policy)
controller.check_permission("agent-1", Permission.EXECUTE)
```

---

## Communication

### MessageBus

```python
from agentic_swarm.communication import MessageBus, Message, MessageType

bus = MessageBus()
bus.subscribe("agent-1", handler_fn)
await bus.publish(Message(
    type=MessageType.TASK_DELEGATE,
    sender_id="coordinator",
    receiver_id="agent-1",
    content="Research quantum computing",
))
```

### Channel

```python
from agentic_swarm.communication import MessageRouter

router = MessageRouter()
channel = router.create_channel("agent-a", "agent-b")
await channel.send("agent-a", "Here's the data")
msg = await channel.receive("agent-b", timeout=5.0)
```

---

## Storage

```python
from agentic_swarm.storage import LocalStorage, RedisStorage

# Local file-based
storage = LocalStorage(base_dir=".data/storage")
await storage.set("key", {"data": "value"})
data = await storage.get("key")
await storage.set("session", "token", ttl=3600)  # Expires in 1 hour

# Redis (distributed)
redis_store = RedisStorage(url="redis://localhost:6379", prefix="swarm:")
await redis_store.set("key", {"data": "value"})
```

---

## Utilities

```python
from agentic_swarm.utils import (
    hash_string, generate_id, generate_token,
    serialize, deserialize,
    validate_agent_name, validate_temperature, validate_max_tokens,
)

# Cryptographic utilities
id = generate_id()
token = generate_token(32)
digest = hash_string("data", "sha256")

# Serialization
json_str = serialize({"created": datetime.now()})
obj = deserialize(json_str)

# Validation
validate_agent_name("my-agent")
validate_temperature(0.7)
validate_max_tokens(4096)
```
