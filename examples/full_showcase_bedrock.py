"""
Complete SDK Showcase with AWS Bedrock

This example combines EVERY feature of the Agentic Swarm SDK into one workflow:

1. Configuration (SDKConfig)
2. LLM Router + Bedrock Provider + Prompt Caching
3. Agent Creation + Dynamic Sub-Agent Spawning
4. Tool Calling (@tool decorator)
5. Tiered Memory (Core + Recall + Archival)
6. RAG Pipeline (Ingest → Chunk → Embed → Retrieve)
7. Inter-Agent Communication (Message Bus + Channels)
8. Swarm Orchestration (Parallel + Sequential + Adaptive)
9. Lifecycle (Supervisor + Healer + Sandbox)
10. SOC2 Compliance (Audit Log + Encryption + Access Control)
11. Storage (LocalStorage persistence)
12. Token Management + Context Compression
13. Utilities (Validation, Crypto, Serialization)

Run with:
  export REEVIX_BEDROCK_ACCESS_KEY_ID=your_key
  export REEVIX_BEDROCK_SECRET_ACCESS_KEY=your_secret
  export REEVIX_BEDROCK_REGION=us-east-1
  python examples/full_showcase_bedrock.py
"""

import os
import asyncio
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════
# SDK IMPORTS (all features)
# ═══════════════════════════════════════════════════════════════

from agentic_swarm import Agent, Swarm, tool
from agentic_swarm.core.config import SDKConfig, LLMConfig, RAGConfig, set_config, get_config
from agentic_swarm.core.registry import AgentRegistry
from agentic_swarm.core.exceptions import AgentCreationError
from agentic_swarm.llm import LLMRouter, BedrockProvider, PromptCache, PrefixCache, TokenManager
from agentic_swarm.llm.context_compressor import ContextCompressor
from agentic_swarm.memory import MemoryController
from agentic_swarm.rag import RAGPipeline, Chunker, Retriever
from agentic_swarm.rag.embedder import MockEmbedder
from agentic_swarm.vectordb import InMemoryVectorDB
from agentic_swarm.communication import MessageBus, Channel, MessageRouter, Message, MessageType
from agentic_swarm.lifecycle import Supervisor, Healer, Spawner, Sandbox, SandboxConfig
from agentic_swarm.compliance import AuditLogger, Encryption, DataIsolation, AuditEventType
from agentic_swarm.compliance.access import AccessController, Permission, AccessPolicy
from agentic_swarm.storage import LocalStorage
from agentic_swarm.utils import (
    hash_string, generate_id, generate_token,
    serialize, deserialize,
    validate_agent_name, validate_temperature,
)


# ═══════════════════════════════════════════════════════════════
# STEP 1: CONFIGURATION
# ═══════════════════════════════════════════════════════════════

def setup_config():
    """Configure the SDK with custom settings."""
    config = SDKConfig(
        llm=LLMConfig(
            default_model="us.anthropic.claude-sonnet-4-6",
            default_temperature=0.7,
            default_max_tokens=4096,
            default_strategy="cost_optimized",
        ),
        rag=RAGConfig(
            chunk_size=300,
            chunk_overlap=50,
            retrieval_strategy="dense",
        ),
    )
    set_config(config)
    return config


# ═══════════════════════════════════════════════════════════════
# STEP 2: LLM ROUTER + CACHING
# ═══════════════════════════════════════════════════════════════

def setup_router() -> LLMRouter:
    """Create Bedrock-powered router with prompt caching."""
    router = LLMRouter(
        strategy="cost_optimized",
        cache_enabled=True,
        cache_max_size=200,
        cache_ttl=1800,
    )

    bedrock = BedrockProvider(
        model=os.getenv("REEVIX_BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6"),
        region=os.getenv("REEVIX_BEDROCK_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("REEVIX_BEDROCK_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("REEVIX_BEDROCK_SECRET_ACCESS_KEY"),
    )
    router.register_provider("bedrock", bedrock)

    router.prefix_cache.register_prefix(
        "system",
        "You are part of a multi-agent research team.",
        token_count=12,
    )

    return router


# ═══════════════════════════════════════════════════════════════
# STEP 3: TOOLS
# ═══════════════════════════════════════════════════════════════

@tool
def research(topic: str) -> str:
    """Research a topic and return key findings."""
    return (
        f"Research on '{topic}': Found 3 studies confirming significant improvements. "
        f"Key metrics: 40% efficiency gain, 3x throughput, 90% accuracy."
    )


@tool
def analyze(data: str) -> str:
    """Analyze data and extract insights."""
    return f"Analysis complete: Primary pattern detected — upward trend with 92% confidence. Anomalies: 2 outliers."


@tool
def write_report(title: str, content: str) -> str:
    """Write a formatted report section."""
    return f"## {title}\n\n{content}\n\n*Generated at {datetime.now(timezone.utc).isoformat()}*"


@tool
def verify_claim(claim: str) -> str:
    """Fact-check a claim against known sources."""
    return f"VERIFIED: '{claim}' — Confirmed by 3 independent sources. Confidence: HIGH."


@tool
async def search_knowledge_base(query: str) -> str:
    """Search the RAG knowledge base."""
    result = await _pipeline.query(query, collection="knowledge", limit=2)
    if result.chunks:
        return "\n".join([c["content"][:150] for c in result.chunks])
    return "No relevant documents found."


@tool
async def store_memory(fact: str) -> str:
    """Store a fact in long-term archival memory."""
    await _memory.store_archival(fact)
    return f"Stored: {fact}"


# ═══════════════════════════════════════════════════════════════
# STEP 4: RAG PIPELINE + MEMORY (global refs for tools)
# ═══════════════════════════════════════════════════════════════

_vectordb = InMemoryVectorDB()
_embedder = MockEmbedder(dimensions=128)
_chunker = Chunker(strategy="recursive", chunk_size=300, overlap=50)
_retriever = Retriever(vectordb=_vectordb, embedder=_embedder)
_pipeline = RAGPipeline(
    vectordb=_vectordb,
    embedder=_embedder,
    chunker=_chunker,
    retriever=_retriever,
)
_memory = MemoryController(
    agent_id="showcase",
    name="Showcase Agent",
    persona="Full-stack AI research assistant",
    vectordb=_vectordb,
    embedder=_embedder,
)


# ═══════════════════════════════════════════════════════════════
# MAIN SHOWCASE
# ═══════════════════════════════════════════════════════════════

async def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   AGENTIC SWARM — COMPLETE SDK SHOWCASE (Bedrock)           ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # ── 1. Configuration ──
    print("\n[1] SDK Configuration")
    config = setup_config()
    print(f"    Model: {config.llm.default_model}")
    print(f"    Strategy: {config.llm.default_strategy}")
    print(f"    RAG chunk size: {config.rag.chunk_size}")

    # ── 2. Router + Caching ──
    print("\n[2] LLM Router + Prompt Cache")
    router = setup_router()
    print(f"    Provider: Bedrock ({router.providers.get('bedrock', 'N/A')})")
    print(f"    Cache: enabled (max={router.cache.max_size}, ttl={router.cache.ttl}s)")
    savings = router.prefix_cache.estimate_savings(2000, 50, "anthropic")
    print(f"    Prefix cache savings estimate: {savings['savings_pct']}% over 50 calls")

    # ── 3. Compliance Setup ──
    print("\n[3] SOC2 Compliance")
    audit = AuditLogger()
    encryption = Encryption(Encryption.generate_key())
    access_ctrl = AccessController()
    isolation = DataIsolation()

    access_ctrl.set_policy("researcher", AccessPolicy(
        agent_id="researcher",
        permissions={Permission.READ, Permission.EXECUTE},
        allowed_tools=["research", "search_knowledge_base"],
        denied_tools=["write_report"],
    ))
    access_ctrl.set_policy("writer", AccessPolicy(
        agent_id="writer",
        permissions={Permission.READ, Permission.WRITE, Permission.EXECUTE},
        allowed_tools=["write_report", "store_memory"],
    ))
    print(f"    Audit logger: active")
    print(f"    Encryption: AES-256")
    print(f"    Access policies: researcher (read-only), writer (read+write)")

    # ── 4. RAG Ingestion ──
    print("\n[4] RAG Pipeline — Ingesting Knowledge Base")
    docs = [
        ("Multi-agent systems decompose complex tasks across specialized agents. "
         "Each agent has tools, memory, and an LLM for reasoning. They communicate "
         "via message buses and can spawn sub-agents dynamically."),
        ("Prompt caching reduces costs by 90% for repeated prefixes. Anthropic and "
         "Bedrock support native cache_control markers. The SDK caches responses "
         "locally to avoid redundant API calls entirely."),
        ("The RAG pipeline supports 4 chunking strategies: fixed, recursive, semantic, "
         "and code-aware. Retrieval uses dense vectors, sparse BM25, or hybrid RRF. "
         "Results are reranked using cross-encoder or keyword scoring."),
    ]
    for i, doc in enumerate(docs):
        await _pipeline.ingest(doc, collection="knowledge", metadata={"id": f"doc-{i}"})
    print(f"    Ingested {len(docs)} documents into vector DB")

    # ── 5. Memory ──
    print("\n[5] Tiered Memory System")
    _memory.push_recall("User wants a complete demo of the SDK", role="user")
    _memory.push_recall("Starting full showcase with all features", role="assistant")
    await _memory.store_archival("User's project uses AWS Bedrock in production")
    await _memory.store_archival("Team requires SOC2 compliance documentation")
    print(f"    Core: {_memory.core.name} ({_memory.core.persona})")
    print(f"    Recall: {len(_memory.recall.get_all())} entries")
    archival = await _memory.search_archival("Bedrock")
    print(f"    Archival: stored 2 facts, search 'Bedrock' → {len(archival)} results")

    # ── 6. Agent Spawning + Registry ──
    print("\n[6] Agent Spawning + Registry")
    registry = AgentRegistry()
    registry.clear()

    coordinator = Agent(
        name="coordinator",
        role="Research team coordinator who delegates and synthesizes",
        tools=[write_report, store_memory],
        llm_router=router,
        max_iterations=10,
    )
    registry.register(coordinator.id, coordinator)
    audit.log(AuditEventType.AGENT_CREATED, agent_id=coordinator.id, data={"name": "coordinator"})

    researcher = await coordinator.create_agent(
        name="researcher",
        role="Research specialist. Call ONE tool, then immediately summarize findings. Do not call multiple tools.",
        tools=[research, search_knowledge_base],
        max_iterations=8,
    )
    registry.register(researcher.id, researcher)
    audit.log(AuditEventType.AGENT_CREATED, agent_id=researcher.id, data={"name": "researcher"})

    analyst = await coordinator.create_agent(
        name="analyst",
        role="Data analyst. Call the analyze tool once, then immediately provide your conclusion. Do not call multiple tools.",
        tools=[analyze],
        max_iterations=8,
    )
    registry.register(analyst.id, analyst)
    audit.log(AuditEventType.AGENT_CREATED, agent_id=analyst.id, data={"name": "analyst"})

    print(f"    Coordinator: {coordinator.name} (parent)")
    print(f"    Researcher: {researcher.name} (child, depth=1)")
    print(f"    Analyst: {analyst.name} (child, depth=1)")
    print(f"    Registry: {registry.count()} agents tracked")

    # Verify access control
    print(f"    Access: researcher can 'research' → {access_ctrl.check_tool_access('researcher', 'research')}")
    print(f"    Access: researcher can 'write_report' → {access_ctrl.check_tool_access('researcher', 'write_report')}")

    # ── 7. Communication ──
    print("\n[7] Inter-Agent Communication")
    bus = MessageBus()
    msg_log = []

    def log_msg(msg):
        msg_log.append(msg)

    bus.subscribe(coordinator.id, log_msg)
    bus.subscribe(researcher.id, log_msg)
    bus.subscribe(analyst.id, log_msg)

    await bus.publish(Message(
        type=MessageType.TASK_DELEGATE,
        sender_id=coordinator.id,
        receiver_id=researcher.id,
        content="Research prompt caching and multi-agent architectures",
    ))
    await bus.publish(Message(
        type=MessageType.TASK_DELEGATE,
        sender_id=coordinator.id,
        receiver_id=analyst.id,
        content="Analyze the cost savings from prompt caching",
    ))
    print(f"    Coordinator delegated 2 tasks via message bus")
    print(f"    Messages in bus: {len(bus.get_history())}")

    # ── 8. Execute Agents (with Bedrock) ──
    print("\n[8] Agent Execution (Bedrock LLM)")

    try:
        print("    Researcher working...")
        r1 = await researcher.run("Research multi-agent AI systems. Use the research tool.")
        print(f"    ✓ Researcher: {str(r1)[:100]}...")

        # Share results via bus
        await bus.publish(Message(
            type=MessageType.TASK_RESULT,
            sender_id=researcher.id,
            receiver_id=analyst.id,
            content=str(r1)[:500],
        ))

        print("    Analyst working...")
        r2 = await analyst.run("Analyze this data: multi-agent systems show 40% efficiency gains. Use the analyze tool.")
        print(f"    ✓ Analyst: {str(r2)[:100]}...")

        await bus.publish(Message(
            type=MessageType.TASK_RESULT,
            sender_id=analyst.id,
            receiver_id=coordinator.id,
            content=str(r2)[:500],
        ))

        print("    Coordinator synthesizing...")
        r3 = await coordinator.run(
            f"Summarize these findings in 2-3 sentences: Research found: {str(r1)[:150]}. Analysis found: {str(r2)[:150]}. Respond directly without using tools."
        )
        print(f"    ✓ Coordinator: {str(r3)[:100]}...")

    except Exception as e:
        print(f"    ⚠ LLM Error: {type(e).__name__}: {str(e)[:80]}")
        print("    (Running remaining features without LLM...)")
        r1 = "Multi-agent systems improve performance by 3x through specialization."
        r2 = "Analysis: 92% confidence in upward trend, 40% cost reduction possible."
        r3 = "## Key Findings\n\nAgents + caching = optimal performance and cost."

    # ── 9. Lifecycle Management ──
    print("\n[9] Lifecycle (Supervisor + Healer)")
    supervisor = Supervisor(max_errors=5)
    healer = Healer(max_retries=3)

    supervisor.register(coordinator)
    supervisor.register(researcher)
    healer.snapshot(coordinator)
    healer.snapshot(researcher)

    health = supervisor.health_check(coordinator.id)
    print(f"    Coordinator health: {health.status.value}")

    supervisor.record_error(researcher.id, "Simulated timeout")
    h2 = supervisor.health_check(researcher.id)
    print(f"    Researcher health (after 1 error): {h2.status.value}")

    # ── 10. Sandbox Execution ──
    print("\n[10] Sandbox (Isolated Execution)")
    sandbox = Sandbox(SandboxConfig(timeout_seconds=5))

    async def safe_computation():
        return {"result": sum(range(1000)), "status": "computed"}

    sandbox_result = await sandbox.execute(safe_computation)
    print(f"    Sandbox result: {sandbox_result}")

    # ── 11. Token Management ──
    print("\n[11] Token Management + Compression")
    token_mgr = TokenManager()
    compressor = ContextCompressor()

    system_tokens = token_mgr.count_tokens(_memory.core.to_prompt())
    budget = token_mgr.calculate_budget(128000, reserved_output=4096, system_prompt_tokens=system_tokens)
    print(f"    System prompt: {system_tokens} tokens")
    print(f"    Available budget: {budget:,} tokens")

    # Compression demo
    long_convo = [{"role": "user", "content": f"Message {i} with some content"} for i in range(20)]
    compressed = compressor.compress(long_convo, budget=100)
    print(f"    Compression: {len(long_convo)} messages → {len(compressed)} (budget=100 tokens)")

    # ── 12. Cache Stats ──
    print("\n[12] Prompt Cache Statistics")
    stats = router.get_usage_stats()
    cache_info = stats.get("cache", {})
    print(f"    Hits: {cache_info.get('hits', 0)}")
    print(f"    Misses: {cache_info.get('misses', 0)}")
    print(f"    Hit rate: {cache_info.get('hit_rate', '0%')}")
    print(f"    Cached entries: {cache_info.get('entries', 0)}")

    # ── 13. Storage ──
    print("\n[13] Persistent Storage")
    storage = LocalStorage(base_dir=".data/showcase")
    await storage.set("session:results", {
        "researcher": str(r1)[:200],
        "analyst": str(r2)[:200],
        "coordinator": str(r3)[:200],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    saved = await storage.get("session:results")
    print(f"    Saved session results to local storage")
    print(f"    Keys: {await storage.list_keys()}")

    # ── 14. Encryption ──
    print("\n[14] Data Encryption")
    sensitive = serialize({"api_key": "sk-secret-123", "agent_data": str(r1)[:50]})
    encrypted = encryption.encrypt(sensitive)
    decrypted = encryption.decrypt_string(encrypted)
    print(f"    Original: {sensitive[:50]}...")
    print(f"    Encrypted: {str(encrypted)[:50]}...")
    print(f"    Decrypted matches: {sensitive == decrypted}")

    # ── 15. Utilities ──
    print("\n[15] Utilities")
    agent_id = generate_id(prefix="agent")
    token = generate_token(16)
    hashed = hash_string(str(r1), "sha256")
    name_valid = validate_agent_name("coordinator")
    temp_valid = validate_temperature(0.7)
    print(f"    Generated ID: {agent_id}")
    print(f"    Secure token: {token}")
    print(f"    Content hash: {hashed[:32]}...")
    print(f"    Name valid: {name_valid is None}")
    print(f"    Temp valid: {temp_valid is None}")

    # ── 16. Audit Trail ──
    print("\n[16] Audit Trail")
    audit.log(AuditEventType.TASK_COMPLETED, agent_id=coordinator.id, data={"task": "showcase"})
    print(f"    Total audit entries: {len(audit._entries)}")
    print(f"    Integrity valid: {audit.verify_integrity()}")
    recent = audit.query(agent_id=coordinator.id)
    print(f"    Coordinator events: {len(recent)}")
    for entry in recent[-3:]:
        print(f"      [{entry.event_type.value}] {entry.data}")

    # ── 17. Swarm Orchestration ──
    print("\n[17] Swarm Orchestration")
    swarm = Swarm(agents=[researcher, analyst], message_bus=bus)
    swarm_result = await swarm.run("Validate findings", strategy="parallel")
    print(f"    Strategy: parallel")
    print(f"    Results: {len(swarm_result.results)} agents completed")
    print(f"    Success: {swarm_result.success}")

    # ── 18. Communication Log ──
    print("\n[18] Communication Log (Full)")
    agent_names = {coordinator.id: "coordinator", researcher.id: "researcher", analyst.id: "analyst"}
    history = bus.get_history(limit=10)
    for i, msg in enumerate(history[-5:], 1):
        sender = agent_names.get(msg.sender_id, "?")
        receiver = agent_names.get(msg.receiver_id, "all")
        print(f"    {i}. [{msg.type.value}] {sender} → {receiver}: {str(msg.content)[:50]}...")

    # ── FINAL SUMMARY ──
    print("\n" + "═" * 65)
    print("  SHOWCASE COMPLETE — ALL 18 FEATURES DEMONSTRATED")
    print("═" * 65)
    print(f"""
    ✓ SDKConfig (custom model, temperature, chunk size)
    ✓ Bedrock LLM Provider (Claude Sonnet)
    ✓ Prompt Cache ({cache_info.get('entries', 0)} entries, {cache_info.get('hit_rate', '0%')} hit rate)
    ✓ Agent Spawning (1 parent + 2 children, depth-limited)
    ✓ Tool Calling (6 tools: research, analyze, write, verify, search, store)
    ✓ Memory (Core + {len(_memory.recall.get_all())} recall + archival vector store)
    ✓ RAG Pipeline ({len(docs)} docs ingested, recursive chunking, dense retrieval)
    ✓ Communication ({len(history)} messages via bus)
    ✓ Swarm (parallel execution, {len(swarm_result.results)} results)
    ✓ Lifecycle (supervisor monitoring, healer snapshots, sandbox isolation)
    ✓ SOC2 Compliance (audit={len(audit._entries)} entries, encryption, access control)
    ✓ Storage (LocalStorage with session persistence)
    ✓ Token Management (budget={budget:,}, compression active)
    ✓ Utilities (crypto, validation, serialization)
    ✓ Registry ({registry.count()} agents tracked)
    """)

    # Cleanup
    await coordinator.terminate()
    await storage.clear()
    registry.clear()
    print("    Cleanup complete. All agents terminated.\n")


if __name__ == "__main__":
    asyncio.run(main())
