"""
Agentic Swarm — Complete SDK Showcase (All Providers)
=====================================================

This example demonstrates ALL SDK features with support for multiple LLM providers.
Run with: python examples/full_showcase.py --provider <provider>

Supported providers:
  - openai (default)
  - anthropic
  - bedrock
  - gemini
  - groq
  - ollama
  - vllm

Features demonstrated:
  1. SDKConfig - Custom configuration
  2. LLM Providers - All supported providers
  3. Prompt Cache - Response caching
  4. Agent Spawning - Parent/child agents
  5. Tool Calling - Custom tools
  6. Memory - Core + Recall + Archival
  7. RAG Pipeline - Document ingestion & retrieval
  8. Communication - Message bus
  9. Swarm - Parallel execution
  10. Lifecycle - Supervisor, Healer, Sandbox
  11. Security Features - Audit, Encryption, Access Control
  12. Storage - Persistent local storage
  13. Token Management - Budget & compression
  14. Utilities - Crypto, validation, serialization
  15. Registry - Agent tracking
  16. Auto Tool Discovery - Dynamic tool loading
"""

import asyncio
import argparse
import os
import sys
from typing import Optional

# SDK imports
from agentic_swarm import Agent, Swarm, tool, register_tool, SDKConfig
from agentic_swarm.llm.router import LLMRouter
from agentic_swarm.llm.providers.openai import OpenAIProvider
from agentic_swarm.llm.providers.anthropic import AnthropicProvider
from agentic_swarm.llm.providers.bedrock import BedrockProvider
from agentic_swarm.llm.providers.gemini import GeminiProvider
from agentic_swarm.llm.providers.groq import GroqProvider
from agentic_swarm.llm.providers.ollama import OllamaProvider
from agentic_swarm.llm.providers.vllm import VLLMProvider

from agentic_swarm.memory.controller import MemoryController
from agentic_swarm.memory.archival_memory import ArchivalMemory
from agentic_swarm.rag.pipeline import RAGPipeline
from agentic_swarm.rag.chunker import Chunker
from agentic_swarm.rag.embedder import MockEmbedder
from agentic_swarm.vectordb import InMemoryVectorDB
from agentic_swarm.communication.bus import MessageBus
from agentic_swarm.communication.protocols import Message, MessageType, Priority
from agentic_swarm.lifecycle.supervisor import Supervisor
from agentic_swarm.lifecycle.healer import Healer
from agentic_swarm.lifecycle.sandbox import Sandbox, SandboxConfig
from agentic_swarm.lifecycle.spawner import Spawner
from agentic_swarm.core.registry import AgentRegistry
from agentic_swarm.compliance.audit import AuditLogger, AuditEventType
from agentic_swarm.compliance.encryption import Encryption
from agentic_swarm.compliance.access import AccessController, Permission, AccessPolicy
from agentic_swarm.storage.local import LocalStorage
from agentic_swarm.llm.token_manager import TokenManager
from agentic_swarm.llm.context_compressor import ContextCompressor
from agentic_swarm.utils.crypto import generate_id, generate_token, hash_string
from agentic_swarm.utils.validation import validate_agent_name, validate_temperature


# =============================================================================
# Provider Configuration
# =============================================================================

PROVIDER_CONFIGS = {
    "openai": {
        "class": OpenAIProvider,
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
        "kwargs": {},
    },
    "anthropic": {
        "class": AnthropicProvider,
        "default_model": "claude-3-haiku-20240307",
        "env_key": "ANTHROPIC_API_KEY",
        "kwargs": {},
    },
    "bedrock": {
        "class": BedrockProvider,
        "default_model": "us.anthropic.claude-sonnet-4-6",
        "env_key": "AWS_ACCESS_KEY_ID",
        "kwargs": {"region": os.getenv("AWS_REGION", "us-east-1")},
    },
    "gemini": {
        "class": GeminiProvider,
        "default_model": "gemini-1.5-flash",
        "env_key": "GOOGLE_API_KEY",
        "kwargs": {},
    },
    "groq": {
        "class": GroqProvider,
        "default_model": "llama-3.1-8b-instant",
        "env_key": "GROQ_API_KEY",
        "kwargs": {},
    },
    "ollama": {
        "class": OllamaProvider,
        "default_model": "llama3.2",
        "env_key": None,  # No API key needed
        "kwargs": {"base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")},
    },
    "vllm": {
        "class": VLLMProvider,
        "default_model": "meta-llama/Llama-3.1-8B-Instruct",
        "env_key": None,
        "kwargs": {"base_url": os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")},
    },
}


def create_provider(provider_name: str, model: Optional[str] = None):
    """Create an LLM provider instance."""
    if provider_name not in PROVIDER_CONFIGS:
        raise ValueError(f"Unknown provider: {provider_name}. Choose from: {list(PROVIDER_CONFIGS.keys())}")
    
    config = PROVIDER_CONFIGS[provider_name]
    model = model or config["default_model"]
    
    # Check for API key if required
    if config["env_key"] and not os.getenv(config["env_key"]):
        print(f"  ⚠ Warning: {config['env_key']} not set. LLM calls may fail.")
    
    return config["class"](model=model, **config["kwargs"])


def create_router(provider_name: str, model: Optional[str] = None) -> LLMRouter:
    """Create an LLM router with the specified provider."""
    provider = create_provider(provider_name, model)
    router = LLMRouter(
        providers={provider_name: provider},
        strategy="cost_optimized",
        cache_enabled=True,
        cache_max_size=200,
        cache_ttl=1800,
    )
    return router


# =============================================================================
# Define Tools
# =============================================================================

@tool
def research_topic(topic: str) -> str:
    """Research a topic and return findings."""
    findings = {
        "ai": "AI systems use neural networks for pattern recognition and decision making.",
        "agents": "Multi-agent systems coordinate multiple AI agents for complex tasks.",
        "llm": "Large Language Models are trained on vast text corpora for language understanding.",
        "rag": "Retrieval-Augmented Generation combines search with generation for accuracy.",
    }
    for key, value in findings.items():
        if key in topic.lower():
            return f"Research findings on {topic}: {value}"
    return f"Research on {topic}: This is a complex topic requiring further investigation."


@tool
def analyze_data(data: str) -> str:
    """Analyze data and provide insights."""
    return f"Analysis complete. Key insight: The data shows patterns consistent with {data[:50]}..."


@tool
def write_report(title: str, content: str) -> str:
    """Write a formatted report."""
    return f"# {title}\n\n{content}\n\n---\nGenerated by Agentic Swarm"


@tool
def verify_facts(statement: str) -> dict:
    """Verify factual accuracy of a statement."""
    return {"statement": statement[:100], "verified": True, "confidence": 0.85}


@tool
async def search_knowledge(query: str) -> list:
    """Search the knowledge base."""
    return [{"title": f"Result for: {query}", "relevance": 0.9}]


@tool
def store_finding(key: str, value: str) -> dict:
    """Store a finding for later retrieval."""
    return {"stored": True, "key": key}


# Register tools globally for auto-discovery
register_tool(research_topic, category="research", keywords=["research", "topic", "find"])
register_tool(analyze_data, category="analysis", keywords=["analyze", "data", "insight"])
register_tool(write_report, category="writing", keywords=["write", "report", "document"])
register_tool(verify_facts, category="verification", keywords=["verify", "fact", "check"])
register_tool(search_knowledge, category="search", keywords=["search", "knowledge", "query"])
register_tool(store_finding, category="storage", keywords=["store", "save", "finding"])


# =============================================================================
# Main Showcase
# =============================================================================

async def run_showcase(provider_name: str, model: Optional[str] = None, skip_llm: bool = False):
    """Run the complete SDK showcase."""
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print(f"║   AGENTIC SWARM — COMPLETE SDK SHOWCASE ({provider_name.upper():^12})      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    # --- 1. SDK Configuration ---
    print("\n[1] SDK Configuration")
    config = SDKConfig(
        llm={"default_model": model or PROVIDER_CONFIGS[provider_name]["default_model"]},
        agent={"max_iterations": 10, "default_temperature": 0.7},
        rag={"chunk_size": 300, "chunk_overlap": 50},
    )
    print(f"    Model: {config.llm.default_model}")
    print(f"    Max iterations: {config.agent.max_iterations}")
    print(f"    RAG chunk size: {config.rag.chunk_size}")
    
    # --- 2. LLM Router + Provider ---
    print("\n[2] LLM Router + Provider")
    router = None
    if not skip_llm:
        try:
            router = create_router(provider_name, model)
            print(f"    Provider: {provider_name}")
            print(f"    Cache: enabled (max=200, ttl=1800s)")
        except Exception as e:
            print(f"    ⚠ Provider setup failed: {e}")
            print("    Running in demo mode (no LLM calls)")
    else:
        print("    Skipped (--skip-llm flag)")
    
    # --- 3. Security Features ---
    print("\n[3] Security Features")
    audit = AuditLogger()
    access = AccessController()
    
    access.set_policy("researcher", AccessPolicy(
        agent_id="researcher",
        permissions={Permission.READ, Permission.EXECUTE},
        allowed_tools=["research_topic", "search_knowledge"],
        denied_tools=["write_report"],
    ))
    access.set_policy("writer", AccessPolicy(
        agent_id="writer",
        permissions={Permission.READ, Permission.WRITE, Permission.EXECUTE},
        allowed_tools=["write_report", "store_finding"],
    ))
    
    audit.log(AuditEventType.AGENT_CREATED, agent_id="coordinator", data={"name": "coordinator"})
    print("    Audit logger: active")
    print("    Encryption: AES-256")
    print("    Access policies: researcher (read-only), writer (read+write)")
    
    # --- 4. RAG Pipeline ---
    print("\n[4] RAG Pipeline — Ingesting Knowledge Base")
    embedder = MockEmbedder(dimensions=384)
    vectordb = InMemoryVectorDB()
    chunker = Chunker(chunk_size=300, overlap=50, strategy="recursive")
    rag = RAGPipeline(embedder=embedder, vectordb=vectordb, chunker=chunker)
    
    docs = [
        "Multi-agent AI systems coordinate multiple autonomous agents to solve complex problems.",
        "Prompt caching reduces latency and cost by reusing previous LLM responses.",
        "RAG combines retrieval with generation for more accurate and grounded responses.",
    ]
    for doc in docs:
        await rag.ingest(doc)
    print(f"    Ingested {len(docs)} documents into vector DB")
    
    # --- 5. Memory System ---
    print("\n[5] Tiered Memory System")
    memory = MemoryController(agent_id="showcase", name="Showcase Agent", persona="AI research assistant")
    archival = ArchivalMemory(agent_id="showcase", embedder=embedder, vectordb=vectordb)
    
    memory.push_recall("User asked about multi-agent systems", role="user")
    memory.push_recall("I explained the architecture", role="assistant")
    
    await archival.store("Multi-agent systems use message passing for coordination")
    await archival.store("Bedrock provides access to multiple foundation models")
    
    search_results = await archival.search("multi-agent", limit=2)
    print(f"    Core: {memory._core.name} ({memory._core.persona})")
    print(f"    Recall: {memory._recall.size} entries")
    print(f"    Archival: stored 2 facts, search 'multi-agent' → {len(search_results)} results")
    
    # --- 6. Agent Spawning + Registry ---
    print("\n[6] Agent Spawning + Registry")
    spawner = Spawner(max_depth=3, max_children=10)
    registry = AgentRegistry()
    
    coordinator = Agent(
        name="coordinator",
        role="Research team coordinator",
        tools=[write_report, store_finding],
        llm_router=router,
        max_iterations=10,
        spawner=spawner,
    )
    registry.register(coordinator.id, coordinator)
    
    researcher = await coordinator.create_agent(
        name="researcher",
        role="Research specialist",
        tools=[research_topic, search_knowledge],
        max_iterations=8,
    )
    registry.register(researcher.id, researcher)
    
    analyst = await coordinator.create_agent(
        name="analyst",
        role="Data analyst",
        tools=[analyze_data, verify_facts],
        max_iterations=8,
    )
    registry.register(analyst.id, analyst)
    
    access.set_policy(researcher.id, AccessPolicy(
        agent_id=researcher.id,
        permissions={Permission.READ, Permission.EXECUTE},
        allowed_tools=["research_topic", "search_knowledge"],
    ))
    access.set_policy(coordinator.id, AccessPolicy(
        agent_id=coordinator.id,
        permissions={Permission.READ, Permission.WRITE, Permission.EXECUTE},
        allowed_tools=["write_report", "store_finding"],
    ))
    
    print(f"    Coordinator: {coordinator.name} (parent)")
    print(f"    Researcher: {researcher.name} (child, depth=1)")
    print(f"    Analyst: {analyst.name} (child, depth=1)")
    print(f"    Registry: {len(registry.list_agents())} agents tracked")
    print(f"    Access: researcher can 'read' → {access.check_permission(researcher.id, Permission.READ)}")
    
    # --- 7. Communication ---
    print("\n[7] Inter-Agent Communication")
    bus = MessageBus()
    
    await bus.publish(Message(
        type=MessageType.TASK,
        sender_id=coordinator.id,
        receiver_id=researcher.id,
        content="Research multi-agent architectures",
        priority=Priority.HIGH,
    ))
    await bus.publish(Message(
        type=MessageType.TASK,
        sender_id=coordinator.id,
        receiver_id=analyst.id,
        content="Analyze cost savings from caching",
        priority=Priority.NORMAL,
    ))
    
    print(f"    Coordinator delegated 2 tasks via message bus")
    print(f"    Messages in bus: {len(bus._history)}")
    
    # --- 8. Agent Execution ---
    print("\n[8] Agent Execution")
    
    if router:
        try:
            print("    Researcher working...")
            r1 = await researcher.run("Research multi-agent AI systems. Summarize in 2-3 sentences.")
            print(f"    ✓ Researcher: {str(r1)[:80]}...")
            
            print("    Analyst working...")
            r2 = await analyst.run("Analyze the benefits of prompt caching. Summarize briefly.")
            print(f"    ✓ Analyst: {str(r2)[:80]}...")
            
            print("    Coordinator synthesizing...")
            r3 = await coordinator.run(f"Summarize: Research={str(r1)[:100]}, Analysis={str(r2)[:100]}. Be brief.")
            print(f"    ✓ Coordinator: {str(r3)[:80]}...")
            
            await bus.publish(Message(
                type=MessageType.RESULT,
                sender_id=researcher.id,
                receiver_id=analyst.id,
                content=str(r1)[:200],
            ))
            await bus.publish(Message(
                type=MessageType.RESULT,
                sender_id=analyst.id,
                receiver_id=coordinator.id,
                content=str(r2)[:200],
            ))
            
        except Exception as e:
            print(f"    ⚠ LLM Error: {type(e).__name__}: {str(e)[:50]}")
            print("    (Running remaining features without LLM...)")
            r1, r2, r3 = "Demo research result", "Demo analysis result", "Demo synthesis"
    else:
        print("    Skipped (no LLM router)")
        r1, r2, r3 = "Demo research result", "Demo analysis result", "Demo synthesis"
    
    # --- 9. Lifecycle Management ---
    print("\n[9] Lifecycle (Supervisor + Healer)")
    supervisor = Supervisor()
    healer = Healer()
    
    supervisor.register(coordinator)
    healer.snapshot(researcher)
    researcher._state = researcher._state  # Simulate state change
    healer.snapshot(researcher)
    
    print(f"    Coordinator health: {supervisor.health_check(coordinator.id).status.value}")
    print(f"    Researcher health (after snapshot): {supervisor.health_check(researcher.id).status.value}")
    
    # --- 10. Sandbox ---
    print("\n[10] Sandbox (Isolated Execution)")
    sandbox = Sandbox(config=SandboxConfig(timeout_seconds=5))
    
    def compute_sum():
        result = sum(range(1000))
        return {"result": result, "status": "computed"}
    
    sandbox_result = await sandbox.execute(compute_sum)
    print(f"    Sandbox result: {sandbox_result}")
    
    # --- 11. Token Management ---
    print("\n[11] Token Management + Compression")
    token_mgr = TokenManager()
    compressor = ContextCompressor(token_mgr)
    
    system_tokens = token_mgr.count_tokens("You are a helpful AI assistant.")
    budget = token_mgr.calculate_budget(128000, reserved_output=4096)
    
    long_messages = [{"role": "user", "content": f"Message {i}: " + "x" * 100} for i in range(20)]
    compressed = compressor.compress(long_messages, budget=100)
    
    print(f"    System prompt: {system_tokens} tokens")
    print(f"    Available budget: {budget:,} tokens")
    print(f"    Compression: {len(long_messages)} messages → {len(compressed)} (budget=100 tokens)")
    
    # --- 12. Cache Statistics ---
    print("\n[12] Prompt Cache Statistics")
    if router:
        stats = router.cache.stats
        print(f"    Hits: {stats.hits}")
        print(f"    Misses: {stats.misses}")
        print(f"    Hit rate: {stats.hit_rate:.1%}")
        print(f"    Cached entries: {stats.entries}")
    else:
        print("    Skipped (no router)")
    
    # --- 13. Storage ---
    print("\n[13] Persistent Storage")
    storage = LocalStorage(base_dir="/tmp/agentic_swarm_showcase")
    await storage.set("session:results", {
        "researcher": str(r1)[:100],
        "analyst": str(r2)[:100],
        "coordinator": str(r3)[:100],
    })
    keys = await storage.list_keys()
    print(f"    Saved session results to local storage")
    print(f"    Keys: {keys}")
    
    # --- 14. Encryption ---
    print("\n[14] Data Encryption")
    key = Encryption.generate_key()
    crypto = Encryption(key=key)
    sensitive = '{"api_key": "sk-secret-123", "agent_data": "' + str(r1)[:50] + '"}'
    encrypted = crypto.encrypt(sensitive)
    decrypted = crypto.decrypt_string(encrypted)
    print(f"    Original: {sensitive[:60]}...")
    print(f"    Encrypted: {str(encrypted)[:60]}...")
    print(f"    Decrypted matches: {decrypted == sensitive}")
    
    # --- 15. Utilities ---
    print("\n[15] Utilities")
    agent_id = generate_id(prefix="agent")
    token = generate_token(length=16)
    content_hash = hash_string(str(r1) + str(r2))
    name_valid = validate_agent_name("my_agent_1")
    temp_valid = validate_temperature(0.7)
    
    print(f"    Generated ID: {agent_id}")
    print(f"    Secure token: {token}")
    print(f"    Content hash: {content_hash[:40]}...")
    print(f"    Name valid: {name_valid is None}")
    print(f"    Temp valid: {temp_valid is None}")
    
    # --- 16. Audit Trail ---
    print("\n[16] Audit Trail")
    audit.log(AuditEventType.TASK_COMPLETED, agent_id=coordinator.id, data={"task": "showcase"})
    
    print(f"    Total audit entries: {len(audit._entries)}")
    print(f"    Integrity valid: {audit.verify_integrity()}")
    
    coord_events = [e for e in audit._entries if e.agent_id == coordinator.id or e.agent_id == "coordinator"]
    print(f"    Coordinator events: {len(coord_events)}")
    for e in coord_events[:2]:
        print(f"      [{e.event_type.value}] {e.data}")
    
    # --- 17. Swarm ---
    print("\n[17] Swarm Orchestration")
    swarm = Swarm()
    swarm.add_agent(researcher)
    swarm.add_agent(analyst)
    
    if router:
        try:
            swarm_results = await swarm.run("Briefly describe your role.")
            print(f"    Strategy: parallel")
            print(f"    Results: {len(swarm_results.results)} agents completed")
            print(f"    Success: {swarm_results.success}")
        except Exception as e:
            print(f"    ⚠ Swarm error: {e}")
            print(f"    Strategy: parallel (demo mode)")
    else:
        print(f"    Strategy: parallel (demo mode)")
        print(f"    Results: 2 agents (simulated)")
    
    # --- 18. Auto Tool Discovery ---
    print("\n[18] Auto Tool Discovery")
    
    auto_agent = Agent(
        name="auto_agent",
        role="Agent with auto-discovered tools",
        auto_tools="research and analyze data",
        tool_retry=2,
    )
    print(f"    Query: 'research and analyze data'")
    print(f"    Tools found: {list(auto_agent.tools.keys())}")
    print(f"    Tool retry: {auto_agent._tool_retry}")
    
    # --- 19. Communication Log ---
    print("\n[19] Communication Log")
    for i, msg in enumerate(bus._history[:4], 1):
        sender = "coordinator" if msg.sender_id == coordinator.id else (
            "researcher" if msg.sender_id == researcher.id else "analyst"
        )
        receiver = "coordinator" if msg.receiver_id == coordinator.id else (
            "researcher" if msg.receiver_id == researcher.id else "analyst"
        )
        print(f"    {i}. [{msg.type.value}] {sender} → {receiver}: {str(msg.content)[:50]}...")
    
    # --- Cleanup ---
    await coordinator.terminate()
    await storage.delete("session:results")
    
    # --- Summary ---
    print("\n" + "═" * 65)
    print("  SHOWCASE COMPLETE — ALL 19 FEATURES DEMONSTRATED")
    print("═" * 65)
    print(f"""
    ✓ SDKConfig (custom model, temperature, chunk size)
    ✓ {provider_name.upper()} LLM Provider
    ✓ Prompt Cache ({router.cache.stats.entries if router else 0} entries)
    ✓ Agent Spawning (1 parent + 2 children, depth-limited)
    ✓ Tool Calling (6 tools: research, analyze, write, verify, search, store)
    ✓ Memory (Core + Recall + Archival vector store)
    ✓ RAG Pipeline ({len(docs)} docs ingested, recursive chunking)
    ✓ Communication ({len(bus._history)} messages via bus)
    ✓ Swarm (parallel execution)
    ✓ Lifecycle (supervisor, healer, sandbox)
    ✓ Security Features (audit, encryption, access control)
    ✓ Storage (LocalStorage with persistence)
    ✓ Token Management (budget={budget:,}, compression active)
    ✓ Utilities (crypto, validation, serialization)
    ✓ Registry ({len(registry.list_agents())} agents tracked)
    ✓ Auto Tool Discovery (dynamic loading + retry)
    
    Cleanup complete. All agents terminated.
    """)


def main():
    parser = argparse.ArgumentParser(
        description="Agentic Swarm SDK Showcase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python examples/full_showcase.py --provider openai
  python examples/full_showcase.py --provider anthropic --model claude-3-5-sonnet-latest
  python examples/full_showcase.py --provider bedrock --model us.anthropic.claude-sonnet-4-6
  python examples/full_showcase.py --provider groq --model llama-3.1-70b-versatile
  python examples/full_showcase.py --provider ollama --model llama3.2
  python examples/full_showcase.py --provider gemini --model gemini-1.5-pro
  python examples/full_showcase.py --skip-llm  # Run without LLM calls
        """
    )
    parser.add_argument(
        "--provider", "-p",
        choices=list(PROVIDER_CONFIGS.keys()),
        default="openai",
        help="LLM provider to use (default: openai)"
    )
    parser.add_argument(
        "--model", "-m",
        help="Model to use (default: provider's default model)"
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip LLM calls (demo mode)"
    )
    
    args = parser.parse_args()
    
    print(f"\nUsing provider: {args.provider}")
    if args.model:
        print(f"Using model: {args.model}")
    print()
    
    asyncio.run(run_showcase(args.provider, args.model, args.skip_llm))


if __name__ == "__main__":
    main()
