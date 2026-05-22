"""
Agentic Swarm on iii — Integration Example
============================================

This shows how Agentic Swarm agents can run as iii workers,
making them discoverable, composable, and observable in the iii runtime.

Architecture:
  iii Engine (Rust)
    └── Worker: "research-agent"
          ├── Function: "research::search"      → Agent tool
          ├── Function: "research::summarize"   → Agent tool
          └── Trigger: HTTP POST /research      → Agent.run()

Prerequisites:
  pip install iii-sdk agentic-swarm

Usage:
  # Start iii engine first
  iii

  # Then run this worker
  python examples/iii_integration.py
"""

import asyncio
from typing import Any, Dict

# --- iii SDK (Python) ---
# pip install iii-sdk
try:
    from iii import Worker, Function, trigger
    III_AVAILABLE = True
except ImportError:
    III_AVAILABLE = False
    print("[INFO] iii-sdk not installed. Showing integration pattern only.")
    print("       Install with: pip install iii-sdk\n")

# --- Agentic Swarm ---
from agentic_swarm import Agent, Swarm, tool
from agentic_swarm.lifecycle.sandbox import SandboxConfig


# =============================================================================
# Step 1: Define your Agentic Swarm tools (these become iii functions)
# =============================================================================

@tool
def search_knowledge(query: str) -> str:
    """Search the knowledge base for relevant information."""
    return f"Found 3 results for: {query}"


@tool
def summarize_text(text: str, max_length: int = 100) -> str:
    """Summarize text to a specified length."""
    return text[:max_length] + "..." if len(text) > max_length else text


@tool
def classify_intent(message: str) -> dict:
    """Classify the intent of a user message."""
    intents = ["question", "command", "feedback"]
    return {"message": message, "intent": intents[0], "confidence": 0.92}


# =============================================================================
# Step 2: Create your Agentic Swarm agents
# =============================================================================

def create_research_agent() -> Agent:
    """Create a research agent with sandbox isolation."""
    return Agent(
        name="researcher",
        role="Research and analyze information from the knowledge base",
        tools=[search_knowledge, summarize_text],
        sandbox_config=SandboxConfig(
            timeout_seconds=30,
            memory_limit_mb=256,
            allow_network=True,
        ),
        enable_isolation=True,
    )


def create_classifier_agent() -> Agent:
    """Create an intent classification agent."""
    return Agent(
        name="classifier",
        role="Classify user intents and route to appropriate handlers",
        tools=[classify_intent],
        sandbox_config=SandboxConfig(
            timeout_seconds=10,
            memory_limit_mb=128,
        ),
        enable_isolation=True,
    )


# =============================================================================
# Step 3: Bridge — Wrap agents as iii workers
# =============================================================================

class AgenticSwarmWorker:
    """
    Bridge between Agentic Swarm and iii.
    
    Maps:
      - Agent       → iii Worker
      - Agent.run() → iii Function
      - Tools       → iii Functions (individually callable)
      - Triggers    → HTTP / Cron / Queue → Agent.run()
    """
    
    def __init__(self, agent: Agent, worker_name: str = None):
        self.agent = agent
        self.worker_name = worker_name or f"swarm-{agent.name}"
    
    def get_function_schemas(self) -> list:
        """Get all agent tools as iii function definitions."""
        functions = []
        
        # Main agent entry point
        functions.append({
            "id": f"{self.agent.name}::run",
            "description": f"Run the {self.agent.name} agent with a task",
            "input": {"task": "string"},
            "output": "any",
        })
        
        # Individual tools as functions
        for tool_obj in self.agent.tools.values():
            functions.append({
                "id": f"{self.agent.name}::{tool_obj.name}",
                "description": tool_obj.description,
                "input": tool_obj.to_openai_schema()["function"]["parameters"],
                "output": "any",
            })
        
        return functions
    
    async def handle_request(self, function_id: str, input_data: dict) -> Any:
        """Handle an iii function call routed to this agent."""
        parts = function_id.split("::")
        fn_name = parts[1] if len(parts) > 1 else "run"
        
        if fn_name == "run":
            # Full agent execution (ReAct loop)
            return await self.agent.run(input_data.get("task", ""))
        else:
            # Direct tool execution (bypasses LLM)
            return await self.agent.execute_isolated(
                self.agent.tools[fn_name].execute,
                **input_data
            )
    
    def register_with_iii(self):
        """Register this agent as an iii worker (requires iii-sdk)."""
        if not III_AVAILABLE:
            return None
        
        worker = Worker(name=self.worker_name)
        
        # Register agent.run as main function
        @worker.function(f"{self.agent.name}::run")
        async def run_agent(task: str) -> Any:
            return await self.agent.run(task)
        
        # Register each tool as a separate iii function
        for tool_name, tool_obj in self.agent.tools.items():
            @worker.function(f"{self.agent.name}::{tool_name}")
            async def call_tool(input_data: dict, _tool=tool_obj) -> Any:
                return await self.agent.execute_isolated(
                    _tool.execute, **input_data
                )
        
        # Add HTTP trigger
        @worker.trigger("http", path=f"/{self.agent.name}")
        async def http_trigger(request: dict) -> Any:
            task = request.get("body", {}).get("task", "")
            return await self.agent.run(task)
        
        return worker


# =============================================================================
# Step 4: Multi-agent swarm as iii worker group
# =============================================================================

class SwarmWorkerGroup:
    """
    Register an entire Agentic Swarm as a group of iii workers.
    
    Each agent in the swarm becomes a discoverable iii worker.
    The swarm coordinator becomes the entry point.
    """
    
    def __init__(self, name: str, agents: list):
        self.name = name
        self.workers = [AgenticSwarmWorker(agent) for agent in agents]
        self.swarm = Swarm(agents=agents)
    
    def get_catalog(self) -> dict:
        """Get the full function catalog for this swarm."""
        catalog = {
            "swarm": self.name,
            "workers": [],
        }
        
        for w in self.workers:
            catalog["workers"].append({
                "name": w.worker_name,
                "agent": w.agent.name,
                "role": w.agent.role,
                "functions": w.get_function_schemas(),
                "isolation": {
                    "namespace": w.agent.namespace,
                    "sandbox_timeout": w.agent._sandbox.config.timeout_seconds,
                    "sandbox_memory_mb": w.agent._sandbox.config.memory_limit_mb,
                },
            })
        
        return catalog
    
    async def route(self, task: str) -> Any:
        """Route a task through the swarm (iii calls this)."""
        return await self.swarm.run(task)


# =============================================================================
# Step 5: Demo — Show how it works
# =============================================================================

async def main():
    print("=" * 70)
    print("  AGENTIC SWARM on iii — Integration Pattern")
    print("=" * 70)
    
    # Create agents
    researcher = create_research_agent()
    classifier = create_classifier_agent()
    
    # Wrap as iii workers
    research_worker = AgenticSwarmWorker(researcher)
    classifier_worker = AgenticSwarmWorker(classifier)
    
    # Create swarm worker group
    swarm_group = SwarmWorkerGroup(
        name="ai-swarm",
        agents=[researcher, classifier],
    )
    
    # =========================================================================
    # Show function catalog (what iii would see)
    # =========================================================================
    print("\n[1] iii FUNCTION CATALOG")
    print("-" * 50)
    
    catalog = swarm_group.get_catalog()
    print(f"    Swarm: {catalog['swarm']}")
    print(f"    Workers: {len(catalog['workers'])}")
    
    for worker_info in catalog["workers"]:
        print(f"\n    Worker: {worker_info['name']}")
        print(f"      Role: {worker_info['role']}")
        print(f"      Namespace: {worker_info['isolation']['namespace']}")
        print(f"      Sandbox: {worker_info['isolation']['sandbox_timeout']}s timeout, "
              f"{worker_info['isolation']['sandbox_memory_mb']}MB memory")
        print(f"      Functions:")
        for fn in worker_info["functions"]:
            print(f"        - {fn['id']}: {fn['description'][:60]}")
    
    # =========================================================================
    # IMMORTAL AGENTS — Self-healing with state recovery
    # =========================================================================
    print("\n\n[2] IMMORTAL AGENTS — Self-Healing")
    print("-" * 50)
    
    from agentic_swarm.lifecycle.supervisor import Supervisor, HealthStatus
    from agentic_swarm.lifecycle.healer import Healer
    
    # Setup immortality for the researcher agent
    healer = Healer(max_retries=3, backoff_factor=2.0)
    supervisor = Supervisor(check_interval=5.0, max_errors=3)
    
    # Register agent for monitoring
    supervisor.register(researcher)
    
    # Take initial snapshot (for recovery)
    snapshot = healer.snapshot(researcher)
    print(f"    Agent: {researcher.name}")
    print(f"    Snapshot taken at: {snapshot.timestamp}")
    print(f"    State: {snapshot.state.value}")
    print(f"    Recall messages: {len(snapshot.recall_messages)}")
    
    # Check health
    health = supervisor.health_check(researcher.id)
    print(f"\n    Health Status: {health.status.value}")
    print(f"    Error Count: {health.error_count}")
    
    # Simulate an error
    print("\n    Simulating agent failure...")
    supervisor.record_error(researcher.id, "Connection timeout")
    supervisor.record_error(researcher.id, "LLM rate limit")
    
    health = supervisor.health_check(researcher.id)
    print(f"    Health Status after errors: {health.status.value}")
    print(f"    Error Count: {health.error_count}")
    print(f"    Last Error: {health.last_error}")
    
    # Recovery would happen automatically, but let's show manual recovery
    print("\n    Recovering from snapshot...")
    await healer.restore(researcher, snapshot)
    supervisor.reset_errors(researcher.id)
    
    health = supervisor.health_check(researcher.id)
    print(f"    Health Status after recovery: {health.status.value}")
    print(f"    Agent state preserved: {researcher.state.value}")
    
    print("""
    How Immortal Agents work with iii:
    
    ┌─────────────────────────────────────────────────────────┐
    │                    iii Engine                            │
    │                                                          │
    │  HTTP Request → researcher::run                          │
    │       │                                                  │
    └───────┼──────────────────────────────────────────────────┘
            │
            ▼
    ┌─────────────────────────────────────────────────────────┐
    │              Agentic Swarm Worker                        │
    │                                                          │
    │  1. Take snapshot (memory state)                         │
    │  2. Execute task                                         │
    │  3. On failure:                                          │
    │     - Supervisor detects unhealthy                       │
    │     - Healer restores from snapshot                      │
    │     - Retry task automatically                           │
    │  4. Return result to iii                                 │
    │                                                          │
    │  iii Functions exposed:                                  │
    │    - researcher::run      (auto-recovers)                │
    │    - researcher::health   (check status)                 │
    │    - researcher::snapshot (manual backup)                │
    │    - researcher::recover  (manual restore)               │
    └─────────────────────────────────────────────────────────┘
    """)
    
    # =========================================================================
    # Simulate iii calling our functions
    # =========================================================================
    print("\n[3] SIMULATED iii FUNCTION CALLS")
    print("-" * 50)
    
    # iii calls researcher::search_knowledge
    print("\n    iii → researcher::search_knowledge")
    result = await research_worker.handle_request(
        "researcher::search_knowledge",
        {"query": "machine learning best practices"}
    )
    print(f"    Result: {result}")
    
    # iii calls classifier::classify_intent
    print("\n    iii → classifier::classify_intent")
    result = await classifier_worker.handle_request(
        "classifier::classify_intent",
        {"message": "How do I reset my password?"}
    )
    print(f"    Result: {result}")
    
    # iii calls researcher::run (full agent execution)
    print("\n    iii → researcher::run (full ReAct loop)")
    result = await research_worker.handle_request(
        "researcher::run",
        {"task": "Find information about quantum computing"}
    )
    print(f"    Result: {result}")
    
    # =========================================================================
    # Show iii worker registration pattern
    # =========================================================================
    print("\n\n[4] iii WORKER REGISTRATION (requires iii-sdk)")
    print("-" * 50)
    
    if III_AVAILABLE:
        worker = research_worker.register_with_iii()
        print("    Worker registered with iii engine!")
    else:
        print("""
    # What this would look like with iii-sdk installed:
    
    from iii import Worker, trigger
    
    worker = Worker(name="swarm-researcher")
    
    @worker.function("researcher::run")
    async def run_agent(task: str):
        return await researcher.run(task)
    
    @worker.function("researcher::search_knowledge")  
    async def search(query: str):
        return await researcher.execute_isolated(
            search_knowledge.func, query
        )
    
    @worker.trigger("http", path="/researcher")
    async def http_handler(request):
        return await researcher.run(request.body.task)
    
    @worker.trigger("cron", schedule="*/5 * * * *")
    async def scheduled_check():
        return await researcher.run("Check for new articles")
    
    @worker.trigger("queue", topic="research-tasks")
    async def queue_handler(message):
        return await researcher.run(message.task)
    
    # Start worker (connects to iii engine)
    worker.start()
    """)
    
    # =========================================================================
    # Show data isolation between workers
    # =========================================================================
    print("\n[5] DATA ISOLATION IN iii CONTEXT")
    print("-" * 50)
    
    print(f"    Researcher namespace: {researcher.namespace}")
    print(f"    Classifier namespace: {classifier.namespace}")
    print(f"    Cross-access blocked: {not researcher.can_access(classifier.namespace)}")
    print(f"    Each worker's data is isolated within iii runtime")
    
    # =========================================================================
    # Architecture diagram
    # =========================================================================
    print("\n\n[6] ARCHITECTURE")
    print("-" * 50)
    print("""
    ┌─────────────────────────────────────────────────────────┐
    │                    iii Engine (Rust)                      │
    │                                                          │
    │  ┌──────────────────────────────────────────────────┐   │
    │  │              Live Worker Catalog                   │   │
    │  └──────────────────────────────────────────────────┘   │
    │       │                    │                    │        │
    │       ▼                    ▼                    ▼        │
    │  ┌──────────┐      ┌──────────────┐     ┌──────────┐   │
    │  │ HTTP     │      │ Queue        │     │ Cron     │   │
    │  │ Trigger  │      │ Trigger      │     │ Trigger  │   │
    │  └────┬─────┘      └──────┬───────┘     └────┬─────┘   │
    │       │                    │                    │        │
    └───────┼────────────────────┼────────────────────┼────────┘
            │                    │                    │
            ▼                    ▼                    ▼
    ┌─────────────────────────────────────────────────────────┐
    │              Agentic Swarm (Python Workers)              │
    │                                                          │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
    │  │ Researcher  │  │ Classifier  │  │ Summarizer  │    │
    │  │   Agent     │  │   Agent     │  │   Agent     │    │
    │  ├─────────────┤  ├─────────────┤  ├─────────────┤    │
    │  │ Sandbox     │  │ Sandbox     │  │ Sandbox     │    │
    │  │ Memory      │  │ Memory      │  │ Memory      │    │
    │  │ Tools       │  │ Tools       │  │ Tools       │    │
    │  │ LLM Router  │  │ LLM Router  │  │ LLM Router  │    │
    │  └─────────────┘  └─────────────┘  └─────────────┘    │
    │                                                          │
    │  ┌──────────────────────────────────────────────────┐   │
    │  │  Shared: RAG Pipeline │ Vector DB │ Compliance    │   │
    │  └──────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────┘
    """)
    
    # Cleanup
    await researcher.terminate()
    await classifier.terminate()
    
    print("\n" + "=" * 70)
    print("  INTEGRATION COMPLETE")
    print("=" * 70)
    print("""
    To run on iii:
    
    1. Install:  pip install iii-sdk agentic-swarm
    2. Start:    iii
    3. Run:      python examples/iii_integration.py
    
    Benefits of running on iii:
    ✓ Auto-discovery — other services find your agents instantly
    ✓ Observability  — full tracing of agent decisions in iii console
    ✓ Triggers       — HTTP, cron, queue invoke agents automatically
    ✓ Multi-language — TypeScript/Rust services call Python agents
    ✓ Scalability    — iii handles load balancing across workers
    
    What Agentic Swarm adds to iii:
    ✓ LLM Intelligence — 7 providers with smart routing
    ✓ Memory           — Agents remember across invocations
    ✓ RAG              — Knowledge retrieval with reranking
    ✓ Self-healing     — Agents recover from failures
    ✓ Compliance       — Security audit trail built in
    """)


if __name__ == "__main__":
    asyncio.run(main())
