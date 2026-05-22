"""
Example: Parent-Child Agent Collaboration

Demonstrates a real workflow where:
1. Parent agent spawns specialized child agents
2. Children execute their tasks
3. Agents communicate results to each other
4. Parent reads all outputs and produces a final result

Scenario: A research coordinator delegates subtasks to a researcher
and a writer, who share findings and produce a final report.
"""

import asyncio
from agentic_swarm import Agent, Swarm
from agentic_swarm.tool import tool
from agentic_swarm.communication import MessageBus, Message, MessageType


# -- Define tools that simulate real work --

@tool
def research_topic(topic: str) -> str:
    """Research a given topic and return findings."""
    findings = {
        "quantum computing": "Quantum computers use qubits that can exist in superposition. "
                            "Recent breakthroughs include Google's 70-qubit processor achieving "
                            "quantum supremacy on optimization problems. Error correction rates "
                            "improved 10x in 2025 using surface codes.",
        "ai agents": "AI agents are autonomous systems that perceive, decide, and act. "
                    "Multi-agent systems enable specialization and parallel task execution. "
                    "Key challenges: coordination, memory management, and tool use.",
    }
    return findings.get(topic.lower(), f"Research findings on: {topic}")


@tool
def write_section(title: str, content: str) -> str:
    """Write a polished section given raw content."""
    return f"## {title}\n\n{content}\n\n---\n"


@tool
def compile_report(sections: str) -> str:
    """Compile multiple sections into a final report."""
    return f"# Final Report\n\n{sections}\n\n*Report compiled successfully.*"


async def main():
    print("=" * 60)
    print("  PARENT-CHILD AGENT COLLABORATION EXAMPLE")
    print("=" * 60)

    # -- Step 1: Create parent coordinator --
    print("\n[Step 1] Creating parent coordinator agent...")
    coordinator = Agent(
        name="coordinator",
        role="Research coordinator who delegates and synthesizes",
        tools=[compile_report],
    )
    print(f"  Created: {coordinator.name} (id={coordinator.id[:8]}...)")

    # -- Step 2: Spawn specialized child agents --
    print("\n[Step 2] Spawning child agents...")
    researcher = await coordinator.create_agent(
        name="researcher",
        role="Deep research specialist",
        tools=[research_topic],
    )
    writer = await coordinator.create_agent(
        name="writer",
        role="Technical writer who polishes content",
        tools=[write_section],
    )
    print(f"  Spawned: {researcher.name} (child of {coordinator.name})")
    print(f"  Spawned: {writer.name} (child of {coordinator.name})")
    print(f"  Coordinator now has {len(coordinator._children)} children")

    # -- Step 3: Set up communication bus --
    print("\n[Step 3] Setting up communication bus...")
    bus = MessageBus()
    received_messages = {}

    async def track_messages(agent_name):
        def handler(msg):
            if agent_name not in received_messages:
                received_messages[agent_name] = []
            received_messages[agent_name].append(msg)
            print(f"  📨 {agent_name} received from {msg.sender_id}: {str(msg.content)[:60]}...")
        return handler

    bus.subscribe(researcher.id, await track_messages("researcher"))
    bus.subscribe(writer.id, await track_messages("writer"))
    bus.subscribe(coordinator.id, await track_messages("coordinator"))

    # -- Step 4: Coordinator delegates tasks --
    print("\n[Step 4] Coordinator delegating tasks...")

    await bus.publish(Message(
        type=MessageType.TASK_DELEGATE,
        sender_id=coordinator.id,
        receiver_id=researcher.id,
        content="Research quantum computing - focus on recent breakthroughs",
    ))

    await bus.publish(Message(
        type=MessageType.TASK_DELEGATE,
        sender_id=coordinator.id,
        receiver_id=researcher.id,
        content="Research AI agents - focus on multi-agent systems",
    ))

    # -- Step 5: Researcher executes tasks and shares results --
    print("\n[Step 5] Researcher executing tasks...")

    research_result_1 = await researcher.tools["research_topic"].execute(topic="quantum computing")
    print(f"  Research output 1: {research_result_1[:80]}...")

    research_result_2 = await researcher.tools["research_topic"].execute(topic="ai agents")
    print(f"  Research output 2: {research_result_2[:80]}...")

    # Researcher sends findings to writer
    await bus.publish(Message(
        type=MessageType.TASK_RESULT,
        sender_id=researcher.id,
        receiver_id=writer.id,
        content={"topic": "quantum computing", "findings": research_result_1},
    ))

    await bus.publish(Message(
        type=MessageType.TASK_RESULT,
        sender_id=researcher.id,
        receiver_id=writer.id,
        content={"topic": "ai agents", "findings": research_result_2},
    ))

    # Also push to researcher's memory for context
    researcher._recall_memory.push(f"Completed research: {research_result_1}", role="assistant")
    researcher._recall_memory.push(f"Completed research: {research_result_2}", role="assistant")

    # -- Step 6: Writer reads research and produces polished sections --
    print("\n[Step 6] Writer reading research and writing sections...")

    section_1 = await writer.tools["write_section"].execute(
        title="Quantum Computing Breakthroughs",
        content=research_result_1,
    )
    print(f"  Written section 1: {section_1[:60]}...")

    section_2 = await writer.tools["write_section"].execute(
        title="AI Agent Systems",
        content=research_result_2,
    )
    print(f"  Written section 2: {section_2[:60]}...")

    # Writer sends completed sections to coordinator
    await bus.publish(Message(
        type=MessageType.TASK_RESULT,
        sender_id=writer.id,
        receiver_id=coordinator.id,
        content={"sections": [section_1, section_2], "status": "complete"},
    ))

    writer._recall_memory.push(f"Delivered 2 sections to coordinator", role="assistant")

    # -- Step 7: Coordinator reads all results and compiles final report --
    print("\n[Step 7] Coordinator compiling final report...")

    # Coordinator reads the message from writer
    coordinator_msgs = received_messages.get("coordinator", [])
    all_sections = ""
    for msg in coordinator_msgs:
        if isinstance(msg.content, dict) and "sections" in msg.content:
            all_sections = "\n".join(msg.content["sections"])

    final_report = await coordinator.tools["compile_report"].execute(sections=all_sections)
    coordinator._recall_memory.push(f"Final report compiled", role="assistant")

    # -- Step 8: Coordinator broadcasts completion --
    print("\n[Step 8] Broadcasting completion to all agents...")
    await bus.broadcast(
        sender_id=coordinator.id,
        content="All tasks complete. Report finalized.",
        topic="status",
    )

    # -- Final output --
    print("\n" + "=" * 60)
    print("  FINAL REPORT OUTPUT")
    print("=" * 60)
    print(final_report)

    # -- Show communication log --
    print("\n" + "=" * 60)
    print("  COMMUNICATION LOG")
    print("=" * 60)
    history = bus.get_history(limit=20)
    for i, msg in enumerate(history, 1):
        sender = "coordinator" if msg.sender_id == coordinator.id else \
                 "researcher" if msg.sender_id == researcher.id else \
                 "writer" if msg.sender_id == writer.id else msg.sender_id
        receiver = "coordinator" if msg.receiver_id == coordinator.id else \
                   "researcher" if msg.receiver_id == researcher.id else \
                   "writer" if msg.receiver_id == writer.id else (msg.receiver_id or "all")
        content_preview = str(msg.content)[:50]
        print(f"  {i}. [{msg.type.value}] {sender} → {receiver}: {content_preview}")

    # -- Show agent memory state --
    print("\n" + "=" * 60)
    print("  AGENT MEMORY STATE")
    print("=" * 60)
    for agent in [coordinator, researcher, writer]:
        entries = agent._recall_memory.get_all()
        print(f"\n  {agent.name} ({len(entries)} memories):")
        for e in entries[-3:]:
            print(f"    [{e.role}] {str(e.content)[:70]}")

    # -- Cleanup --
    print("\n\n[Cleanup] Terminating all agents...")
    await coordinator.terminate()
    print(f"  Coordinator state: {coordinator.state.value}")
    print(f"  Researcher state: {researcher.state.value}")
    print(f"  Writer state: {writer.state.value}")
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
