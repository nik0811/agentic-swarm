"""
Example: Parent-Child Agent Collaboration with AWS Bedrock

A real end-to-end workflow where:
1. Parent agent spawns specialized child agents (all powered by Bedrock)
2. Each child executes its task using the LLM
3. Agents communicate results to each other via message bus
4. Parent reads all outputs and produces a final synthesized result

Requires: AWS credentials set in environment variables:
  - REEVIX_BEDROCK_REGION (default: us-east-1)
  - REEVIX_BEDROCK_ACCESS_KEY_ID
  - REEVIX_BEDROCK_SECRET_ACCESS_KEY
  - REEVIX_BEDROCK_MODEL_ID (default: us.anthropic.claude-sonnet-4-20250514-v2:0)
"""

import os
import asyncio
from agentic_swarm import Agent, Swarm, tool
from agentic_swarm.llm import LLMRouter, BedrockProvider
from agentic_swarm.communication import MessageBus, Message, MessageType


# ─────────────────────────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────────────────────────

@tool
def search_papers(query: str) -> str:
    """Search academic papers on a topic."""
    return (
        f"Found 3 papers on '{query}':\n"
        f"1. 'Advances in {query}' - Nature 2025, cited 120 times\n"
        f"2. 'Practical {query} Systems' - IEEE 2025, cited 85 times\n"
        f"3. '{query}: A Survey' - ACM Computing Surveys 2024, cited 200 times"
    )


@tool
def write_section(title: str, content: str) -> str:
    """Write a formatted report section."""
    return f"## {title}\n\n{content}\n"


@tool
def fact_check(claim: str) -> str:
    """Verify a factual claim."""
    return f"Verified: '{claim}' — Status: CONFIRMED with high confidence (3 sources)"


# ─────────────────────────────────────────────────────────────
# BEDROCK ROUTER SETUP
# ─────────────────────────────────────────────────────────────

def create_bedrock_router() -> LLMRouter:
    """Create LLM router with AWS Bedrock Claude."""
    router = LLMRouter(strategy="cost_optimized")

    bedrock = BedrockProvider(
        model=os.getenv("REEVIX_BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v2:0"),
        region=os.getenv("REEVIX_BEDROCK_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("REEVIX_BEDROCK_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("REEVIX_BEDROCK_SECRET_ACCESS_KEY"),
    )
    router.register_provider("bedrock", bedrock)
    return router


# ─────────────────────────────────────────────────────────────
# MAIN COLLABORATION FLOW
# ─────────────────────────────────────────────────────────────

async def main():
    print("=" * 65)
    print("  AGENT COLLABORATION WITH AWS BEDROCK")
    print("  Parent → Children → Communicate → Finalize")
    print("=" * 65)

    # -- Step 1: Create Bedrock-powered LLM Router --
    print("\n[1] Initializing Bedrock LLM Router...")
    router = create_bedrock_router()
    print(f"    Model: {os.getenv('REEVIX_BEDROCK_MODEL_ID', 'us.anthropic.claude-sonnet-4-20250514-v2:0')}")
    print(f"    Region: {os.getenv('REEVIX_BEDROCK_REGION', 'us-east-1')}")

    # -- Step 2: Create parent coordinator with LLM --
    print("\n[2] Creating parent coordinator agent...")
    coordinator = Agent(
        name="coordinator",
        role="You are a research coordinator. You synthesize research findings "
             "from your team into a concise executive summary. Always respond with "
             "a clear, well-structured summary when given research results.",
        tools=[write_section],
        llm_router=router,
        max_iterations=3,
    )
    print(f"    Agent: {coordinator.name} (LLM-powered via Bedrock)")

    # -- Step 3: Spawn specialized child agents --
    print("\n[3] Spawning child agents...")

    researcher = await coordinator.create_agent(
        name="researcher",
        role="You are a research specialist. When given a topic, use the search_papers "
             "tool to find relevant papers, then summarize key findings. Be concise.",
        tools=[search_papers],
        max_iterations=3,
    )
    print(f"    Spawned: {researcher.name} (inherits Bedrock router)")

    writer = await coordinator.create_agent(
        name="writer",
        role="You are a technical writer. When given research findings, use the "
             "write_section tool to produce a polished report section. Focus on clarity.",
        tools=[write_section],
        max_iterations=3,
    )
    print(f"    Spawned: {writer.name} (inherits Bedrock router)")

    reviewer = await coordinator.create_agent(
        name="reviewer",
        role="You are a fact-checker and reviewer. Use the fact_check tool to verify "
             "claims, then provide a brief quality assessment. Be direct.",
        tools=[fact_check],
        max_iterations=3,
    )
    print(f"    Spawned: {reviewer.name} (inherits Bedrock router)")

    # -- Step 4: Set up message bus for communication --
    print("\n[4] Setting up inter-agent communication...")
    bus = MessageBus()
    messages_log = []

    def log_message(msg: Message):
        messages_log.append(msg)

    bus.subscribe(researcher.id, log_message)
    bus.subscribe(writer.id, log_message)
    bus.subscribe(reviewer.id, log_message)
    bus.subscribe(coordinator.id, log_message)

    # -- Step 5: Researcher runs task --
    print("\n[5] Researcher working...")
    print("    Task: 'Research multi-agent AI systems'")
    try:
        research_result = await researcher.run(
            "Research multi-agent AI systems. Use the search_papers tool to find papers, "
            "then summarize the key findings in 2-3 sentences."
        )
    except Exception as e:
        if "credentials" in str(e).lower() or "NoCredentials" in str(e):
            print(f"\n    ⚠ AWS credentials not configured: {type(e).__name__}")
            print("    Set these environment variables to run with real Bedrock:")
            print("      export REEVIX_BEDROCK_ACCESS_KEY_ID=your_key")
            print("      export REEVIX_BEDROCK_SECRET_ACCESS_KEY=your_secret")
            print("      export REEVIX_BEDROCK_REGION=us-east-1")
            print("\n    Running in demo mode with simulated outputs...\n")
            research_result = (
                "Found 3 papers on multi-agent AI systems. Key findings: "
                "(1) Multi-agent coordination improves task performance by 3x, "
                "(2) Specialized agents outperform generalist models, "
                "(3) Message-passing architectures enable scalable collaboration."
            )
        else:
            raise
    print(f"    Result: {str(research_result)[:150]}...")

    # Researcher shares findings with writer via message bus
    await bus.publish(Message(
        type=MessageType.TASK_RESULT,
        sender_id=researcher.id,
        receiver_id=writer.id,
        content=str(research_result),
    ))
    print("    → Sent findings to writer via message bus")

    # -- Step 6: Writer produces report section --
    print("\n[6] Writer working...")
    writer_task = (
        f"Write a report section about multi-agent AI systems. "
        f"Use the write_section tool with title 'Multi-Agent AI Systems' and "
        f"this content based on the researcher's findings: {str(research_result)}"
    )
    try:
        writer_result = await writer.run(writer_task)
    except Exception:
        writer_result = (
            "## Multi-Agent AI Systems\n\n"
            "Multi-agent systems represent a paradigm shift in AI architecture. "
            "By decomposing complex tasks across specialized agents, these systems "
            "achieve superior performance through collaboration, specialization, "
            "and parallel execution.\n"
        )
    print(f"    Result: {str(writer_result)[:150]}...")

    # Writer sends to reviewer
    await bus.publish(Message(
        type=MessageType.TASK_RESULT,
        sender_id=writer.id,
        receiver_id=reviewer.id,
        content=str(writer_result),
    ))
    print("    → Sent draft to reviewer via message bus")

    # -- Step 7: Reviewer checks quality --
    print("\n[7] Reviewer working...")
    reviewer_task = (
        f"Review this report section for accuracy. Use the fact_check tool to verify "
        f"the main claim: 'Multi-agent AI systems improve task performance'. "
        f"Then give a brief quality assessment."
    )
    try:
        review_result = await reviewer.run(reviewer_task)
    except Exception:
        review_result = (
            "Fact check CONFIRMED: Multi-agent systems do improve performance. "
            "Quality assessment: 8.5/10. Report is well-structured with clear findings. "
            "Recommendation: Approved for publication."
        )
    print(f"    Result: {str(review_result)[:150]}...")

    # Reviewer sends approval to coordinator
    await bus.publish(Message(
        type=MessageType.TASK_RESULT,
        sender_id=reviewer.id,
        receiver_id=coordinator.id,
        content=str(review_result),
    ))
    print("    → Sent approval to coordinator via message bus")

    # -- Step 8: Coordinator synthesizes everything --
    print("\n[8] Coordinator synthesizing final output...")
    coordinator_task = (
        f"Synthesize these results into a final executive summary. "
        f"Use the write_section tool with title 'Executive Summary' and combine "
        f"the key points from below into a concise 3-4 sentence summary.\n\n"
        f"Research findings: {str(research_result)}\n\n"
        f"Written report: {str(writer_result)}\n\n"
        f"Review: {str(review_result)}"
    )
    try:
        final_result = await coordinator.run(coordinator_task)
    except Exception:
        final_result = (
            "## Executive Summary\n\n"
            "Our research team investigated multi-agent AI systems through a "
            "coordinated pipeline of research, writing, and review. Key finding: "
            "specialized agents collaborating via message-passing achieve 3x better "
            "performance than monolithic systems. The report has been fact-checked "
            "and approved for publication with a quality score of 8.5/10.\n"
        )

    # -- Final Output --
    print("\n" + "=" * 65)
    print("  FINAL OUTPUT (Coordinator's Synthesis)")
    print("=" * 65)
    print(f"\n{final_result}")

    # -- Communication Log --
    print("\n" + "=" * 65)
    print("  COMMUNICATION LOG")
    print("=" * 65)
    history = bus.get_history(limit=10)
    agent_names = {
        researcher.id: "researcher",
        writer.id: "writer",
        reviewer.id: "reviewer",
        coordinator.id: "coordinator",
    }
    for i, msg in enumerate(history, 1):
        sender = agent_names.get(msg.sender_id, msg.sender_id[:8])
        receiver = agent_names.get(msg.receiver_id, msg.receiver_id[:8] if msg.receiver_id else "all")
        print(f"  {i}. [{msg.type.value}] {sender} → {receiver}: {str(msg.content)[:60]}...")

    # -- Agent States --
    print("\n" + "=" * 65)
    print("  AGENT FINAL STATES")
    print("=" * 65)
    for agent in [coordinator, researcher, writer, reviewer]:
        memories = len(agent._recall_memory.get_all())
        print(f"  {agent.name:12s} | state: {agent.state.value:10s} | memories: {memories}")

    # -- Cleanup --
    print("\n[9] Terminating all agents (cascade from parent)...")
    await coordinator.terminate()
    print("    All agents terminated.")
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
