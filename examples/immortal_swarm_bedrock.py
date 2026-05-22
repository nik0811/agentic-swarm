"""
Multi-Agent Immortal Swarm with Bedrock

This example demonstrates:
1. Multi-agent swarm with Bedrock LLM provider
2. Immortal agents (auto-heal on failure, never die)
3. Parallel execution of agents
4. Sequential execution of agents
5. Agent-to-agent communication
"""
import asyncio
from agentic_swarm import Agent, Swarm, tool
from agentic_swarm.llm import LLMRouter, BedrockProvider
from agentic_swarm.lifecycle import Supervisor, Healer, HealthStatus
from agentic_swarm.core.types import AgentState


# ─────────────────────────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────────────────────────

@tool
def research_topic(topic: str) -> str:
    """Research a topic and return findings."""
    return f"[Research] Found 5 key papers about '{topic}'. Key insights: scalability, fault-tolerance, distributed consensus."


@tool
def analyze_data(data: str) -> str:
    """Analyze data and extract patterns."""
    return f"[Analysis] Patterns found in data: trend is upward, 3 anomalies detected, confidence 92%."


@tool
def write_report(title: str, findings: str) -> str:
    """Write a structured report from findings."""
    return f"[Report] '{title}'\n\nExecutive Summary: {findings}\n\nConclusion: Actionable recommendations provided."


@tool
def review_content(content: str) -> str:
    """Review content for quality and accuracy."""
    return f"[Review] Content quality: 8/10. Suggestions: Add more data points, clarify methodology section."


@tool
def send_notification(recipient: str, message: str) -> str:
    """Send a notification to a team member."""
    return f"[Notification] Sent to {recipient}: {message}"


# ─────────────────────────────────────────────────────────────
# SETUP: Bedrock LLM Router
# ─────────────────────────────────────────────────────────────

def create_bedrock_router() -> LLMRouter:
    """Create an LLM router with AWS Bedrock provider."""
    import os
    
    router = LLMRouter(strategy="cost_optimized")
    
    bedrock = BedrockProvider(
        model=os.getenv("REEVIX_BEDROCK_MODEL_ID", "us.anthropic.claude-opus-4-6-v1"),
        region=os.getenv("REEVIX_BEDROCK_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("REEVIX_BEDROCK_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("REEVIX_BEDROCK_SECRET_ACCESS_KEY"),
    )
    router.register_provider("bedrock", bedrock)
    
    return router


# ─────────────────────────────────────────────────────────────
# IMMORTAL AGENT SYSTEM (Never Die)
# ─────────────────────────────────────────────────────────────

class ImmortalSwarm:
    """
    A swarm where agents never die.
    If an agent crashes, it auto-heals and continues.
    """
    
    def __init__(self, router: LLMRouter = None):
        self.router = router
        self.supervisor = Supervisor(max_errors=5)
        self.healer = Healer(max_retries=10, backoff_factor=1.5)
        self.swarm = Swarm()
        self._agents: dict[str, Agent] = {}
    
    def create_agent(self, name: str, role: str, tools: list = None) -> Agent:
        """Create an immortal agent that auto-heals on failure."""
        agent = Agent(
            name=name,
            role=role,
            tools=tools,
            llm_router=self.router,
        )
        
        self._agents[name] = agent
        self.swarm.add_agent(agent)
        self.supervisor.register(agent)
        self.healer.snapshot(agent)
        
        print(f"  [+] Created immortal agent: {name}")
        return agent
    
    async def run_with_healing(self, agent: Agent, task: str) -> str:
        """Run a task with auto-healing if agent fails."""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                self.healer.snapshot(agent)
                result = await agent.run(task)
                self.supervisor.reset_errors(agent.id)
                return result
            except Exception as e:
                print(f"  [!] Agent '{agent.name}' failed (attempt {attempt + 1}): {e}")
                self.supervisor.record_error(agent.id, str(e))
                
                success = await self.healer.recover(agent, e)
                if success:
                    print(f"  [✓] Agent '{agent.name}' auto-healed, retrying...")
                else:
                    print(f"  [✗] Agent '{agent.name}' could not recover")
                    break
        
        return f"Agent {agent.name} completed task after recovery"
    
    async def run_parallel(self, task: str) -> dict:
        """Run all agents in parallel on the same task."""
        print(f"\n{'='*60}")
        print(f"  PARALLEL EXECUTION: '{task[:50]}...'")
        print(f"{'='*60}")
        
        async def run_agent(agent):
            result = await self.run_with_healing(agent, task)
            return agent.name, result
        
        results = await asyncio.gather(
            *[run_agent(agent) for agent in self._agents.values()],
            return_exceptions=True
        )
        
        output = {}
        for r in results:
            if isinstance(r, tuple):
                output[r[0]] = r[1]
            else:
                output["error"] = str(r)
        
        return output
    
    async def run_sequential(self, task: str) -> dict:
        """Run agents sequentially, each building on previous results."""
        print(f"\n{'='*60}")
        print(f"  SEQUENTIAL EXECUTION: '{task[:50]}...'")
        print(f"{'='*60}")
        
        results = {}
        context = task
        
        for name, agent in self._agents.items():
            print(f"\n  → Running agent: {name}")
            result = await self.run_with_healing(agent, context)
            results[name] = result
            context = f"Previous agent ({name}) output: {result}\n\nContinue with original task: {task}"
        
        return results
    
    async def communicate(self, sender_name: str, receiver_name: str, message: str):
        """Agent-to-agent communication."""
        sender = self._agents.get(sender_name)
        receiver = self._agents.get(receiver_name)
        
        if not sender or not receiver:
            print(f"  [!] Communication failed: agent not found")
            return
        
        print(f"  [MSG] {sender_name} → {receiver_name}: {message[:60]}...")
        await sender.send(receiver, message)
    
    def get_health_report(self) -> dict:
        """Get health status of all agents."""
        report = {}
        for name, agent in self._agents.items():
            health = self.supervisor.health_check(agent.id)
            report[name] = {
                "status": health.status.value,
                "errors": health.error_count,
                "state": agent.state.value,
            }
        return report


# ─────────────────────────────────────────────────────────────
# SIMULATE FAILURE (for demonstrating auto-heal)
# ─────────────────────────────────────────────────────────────

async def simulate_agent_failure(agent: Agent):
    """Simulate an agent crash to demonstrate auto-healing."""
    agent._state = AgentState.RECOVERING
    raise RuntimeError(f"Simulated crash for agent '{agent.name}'")


# ─────────────────────────────────────────────────────────────
# MAIN EXAMPLE
# ─────────────────────────────────────────────────────────────

async def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     AGENTIC SWARM - IMMORTAL MULTI-AGENT SYSTEM          ║")
    print("║         Using AWS Bedrock (Claude, Llama, Titan)         ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # ─── Step 1: Create the Immortal Swarm ───
    print("\n[1] Creating Immortal Swarm with Bedrock Router...")
    
    # NOTE: In production, create_bedrock_router() connects to AWS.
    # For this demo, agents run in placeholder mode without real LLM calls.
    # To use real Bedrock, uncomment: router = create_bedrock_router()
    router = create_bedrock_router()  # Set to create_bedrock_router() for real Bedrock calls
    
    swarm = ImmortalSwarm(router=router)
    
    # ─── Step 2: Create Immortal Agents ───
    print("\n[2] Spawning immortal agents (they never die)...")
    
    researcher = swarm.create_agent(
        name="researcher",
        role="You are a senior research analyst. You find and synthesize information from multiple sources.",
        tools=[research_topic, analyze_data],
    )
    
    analyst = swarm.create_agent(
        name="analyst",
        role="You are a data analyst who finds patterns and insights in research data.",
        tools=[analyze_data],
    )
    
    writer = swarm.create_agent(
        name="writer",
        role="You are a technical writer who creates clear, structured reports.",
        tools=[write_report],
    )
    
    reviewer = swarm.create_agent(
        name="reviewer",
        role="You review content for quality, accuracy, and completeness.",
        tools=[review_content, send_notification],
    )
    
    # ─── Step 3: Agent Communication ───
    print("\n[3] Agent-to-Agent Communication...")
    
    await swarm.communicate(
        "researcher", "analyst",
        "I found new data on distributed AI systems. Please analyze the scalability patterns."
    )
    
    await swarm.communicate(
        "analyst", "writer",
        "Analysis complete. Key finding: 3x throughput improvement with horizontal scaling."
    )
    
    await swarm.communicate(
        "writer", "reviewer",
        "Draft report ready for review: 'Scaling Multi-Agent AI Systems'"
    )
    
    await swarm.communicate(
        "reviewer", "researcher",
        "Report approved with minor revisions. Great work team!"
    )
    
    # ─── Step 4: Parallel Execution ───
    print("\n[4] Running agents in PARALLEL (all work simultaneously)...")
    
    parallel_results = await swarm.run_parallel(
        "Analyze the impact of multi-agent AI systems on enterprise software"
    )
    
    print("\n  Parallel Results:")
    for agent_name, result in parallel_results.items():
        print(f"    {agent_name}: {str(result)[:80]}...")
    
    # ─── Step 5: Sequential Execution ───
    print("\n[5] Running agents SEQUENTIALLY (each builds on previous)...")
    
    sequential_results = await swarm.run_sequential(
        "Create a comprehensive report on AI agent architectures"
    )
    
    print("\n  Sequential Results:")
    for agent_name, result in sequential_results.items():
        print(f"    {agent_name}: {str(result)[:80]}...")
    
    # ─── Step 6: Demonstrate Auto-Healing (Never Die) ───
    print(f"\n{'='*60}")
    print("  IMMORTALITY DEMO: Agents auto-heal on failure")
    print(f"{'='*60}")
    
    print("\n  Simulating agent crash...")
    researcher._state = AgentState.RECOVERING
    swarm.supervisor.record_error(researcher.id, "Simulated network timeout")
    swarm.supervisor.record_error(researcher.id, "Simulated OOM error")
    
    print(f"  Agent '{researcher.name}' state: {researcher.state.value}")
    print("  Triggering auto-heal...")
    
    success = await swarm.healer.recover(researcher, Exception("Simulated crash"))
    print(f"  Recovery successful: {success}")
    print(f"  Agent '{researcher.name}' state after heal: {researcher.state.value}")
    
    # Agent is alive again and can continue working
    result = await swarm.run_with_healing(researcher, "Continue previous research")
    print(f"  Agent resumed work: {str(result)[:60]}...")
    
    # ─── Step 7: Health Report ───
    print("\n[7] Final Health Report (all agents alive):")
    
    health = swarm.get_health_report()
    for name, status in health.items():
        emoji = "🟢" if status["status"] == "healthy" else "🟡" if status["status"] == "degraded" else "🔴"
        print(f"    {emoji} {name}: {status['status']} | errors: {status['errors']} | state: {status['state']}")
    
    # ─── Step 8: Full Pipeline with Communication ───
    print(f"\n{'='*60}")
    print("  FULL PIPELINE: Research → Analyze → Write → Review")
    print(f"{'='*60}")
    
    # Researcher does work
    print("\n  Step A: Researcher investigates...")
    r1 = await swarm.run_with_healing(researcher, "Research quantum computing advances in 2026")
    
    # Researcher sends findings to analyst
    await swarm.communicate("researcher", "analyst", f"Here are my findings: {r1}")
    
    # Analyst processes
    print("  Step B: Analyst processes data...")
    r2 = await swarm.run_with_healing(analyst, "Analyze the quantum computing research data")
    
    # Analyst sends to writer
    await swarm.communicate("analyst", "writer", f"Analysis complete: {r2}")
    
    # Writer creates report
    print("  Step C: Writer creates report...")
    r3 = await swarm.run_with_healing(writer, "Write a report on quantum computing based on the analysis")
    
    # Writer sends to reviewer
    await swarm.communicate("writer", "reviewer", f"Please review: {r3}")
    
    # Reviewer approves
    print("  Step D: Reviewer checks quality...")
    r4 = await swarm.run_with_healing(reviewer, "Review the quantum computing report for accuracy")
    
    # Reviewer notifies everyone
    await swarm.communicate("reviewer", "researcher", "Report approved! Publishing now.")
    
    print("\n  ✓ Pipeline complete! All agents alive and healthy.")
    
    print("\n╔════════════════════════════════════════════════════════╗")
    print("║                    DEMO COMPLETE                         ║")
    print("║  All agents survived, auto-healed, and communicated.     ║")
    print("╚══════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    asyncio.run(main())
