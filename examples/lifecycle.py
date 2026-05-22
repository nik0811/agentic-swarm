"""
Example: Lifecycle Management

Demonstrates supervisor health monitoring, healer auto-recovery,
spawner depth/children limits, and sandbox isolated execution.
"""

import asyncio
from agentic_swarm import Agent
from agentic_swarm.lifecycle.supervisor import Supervisor, HealthStatus
from agentic_swarm.lifecycle.healer import Healer
from agentic_swarm.lifecycle.spawner import Spawner
from agentic_swarm.lifecycle.sandbox import Sandbox, SandboxConfig
from agentic_swarm.core.types import AgentState


def demonstrate_supervisor():
    """Health monitoring with error tracking."""
    print("=== Supervisor ===")
    supervisor = Supervisor(max_errors=3)

    agent = Agent(name="worker", role="Data processor")
    supervisor.register(agent)

    health = supervisor.health_check(agent.id)
    print(f"  Initial health: {health.status.value}")

    supervisor.record_error(agent.id, "Connection timeout")
    supervisor.record_error(agent.id, "API rate limit")
    health = supervisor.health_check(agent.id)
    print(f"  After 2 errors: {health.status.value}")

    supervisor.record_error(agent.id, "Out of memory")
    health = supervisor.health_check(agent.id)
    print(f"  After 3 errors (max): {health.status.value}")


async def demonstrate_healer():
    """State snapshot and auto-recovery."""
    print("\n=== Healer ===")
    healer = Healer(max_retries=3)

    agent = Agent(name="recoverable", role="Worker")
    agent._recall_memory.push("Important context", role="user")
    agent._recall_memory.push("Working on task X", role="assistant")

    snapshot = healer.snapshot(agent)
    print(f"  Snapshot taken: {len(snapshot.recall_messages)} messages preserved")

    agent._state = AgentState.RECOVERING
    success = await healer.recover(agent, Exception("Network failure"))
    print(f"  Recovery successful: {success}")
    print(f"  Agent state after recovery: {agent.state.value}")


async def demonstrate_spawner():
    """Dynamic spawning with depth and children limits."""
    print("\n=== Spawner ===")
    spawner = Spawner(max_depth=3, max_children=4)

    root = Agent(name="root", role="Manager", spawner=spawner)
    print(f"  Root depth: {spawner.get_depth(root.id)}")

    child1 = await root.create_agent(name="researcher", role="Research")
    child2 = await root.create_agent(name="writer", role="Writing")
    print(f"  Children spawned: {len(root._children)}")
    print(f"  Child depth: {spawner.get_depth(child1.id)}")

    grandchild = await child1.create_agent(name="sub-researcher", role="Deep research")
    print(f"  Grandchild depth: {spawner.get_depth(grandchild.id)}")
    print(f"  Tree: root → [{child1.name}, {child2.name}] → [{grandchild.name}]")

    print(f"\n  Children of root: {spawner.get_children(root.id)}")
    print(f"  Children of {child1.name}: {spawner.get_children(child1.id)}")


async def demonstrate_sandbox():
    """Isolated execution with timeout."""
    print("\n=== Sandbox ===")
    sandbox = Sandbox(SandboxConfig(timeout_seconds=3))

    async def safe_task():
        await asyncio.sleep(0.1)
        return {"result": "computation complete", "value": 42}

    result = await sandbox.execute(safe_task)
    print(f"  Safe task result: {result}")

    async def slow_task():
        await asyncio.sleep(10)
        return "never reaches here"

    try:
        await sandbox.execute(slow_task)
    except TimeoutError:
        print(f"  Slow task: timed out (as expected)")


async def demonstrate_parallel_spawning():
    """Spawn multiple children and run tasks in parallel."""
    print("\n=== Parallel Spawning ===")
    coordinator = Agent(name="coordinator", role="Task coordinator")

    results = await coordinator.run_parallel([
        "Research quantum computing",
        "Summarize findings",
        "Write conclusion",
    ])

    print(f"  Tasks submitted: 3")
    print(f"  Workers spawned: {len(coordinator._children)}")
    print(f"  Results collected: {len(results)}")
    for i, child in enumerate(coordinator._children):
        print(f"    Worker {i}: {child.name} (state={child.state.value})")


async def main():
    demonstrate_supervisor()
    await demonstrate_healer()
    await demonstrate_spawner()
    await demonstrate_sandbox()
    await demonstrate_parallel_spawning()


if __name__ == "__main__":
    asyncio.run(main())
