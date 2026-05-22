"""
Example: Agent Registry

Demonstrates the global singleton registry for tracking agents and swarms.
"""

from agentic_swarm import Agent, Swarm
from agentic_swarm.core.registry import AgentRegistry


def main():
    print("=== Agent Registry (Singleton) ===")

    registry = AgentRegistry()
    registry.clear()

    agent1 = Agent(name="researcher", role="Research AI topics")
    agent2 = Agent(name="writer", role="Write documentation")
    agent3 = Agent(name="reviewer", role="Review code")

    registry.register(agent1.id, agent1)
    registry.register(agent2.id, agent2)
    registry.register(agent3.id, agent3)
    print(f"  Registered {registry.count()} agents")

    print("\n=== Querying Registry ===")
    found = registry.get(agent1.id)
    print(f"  Found agent: {found.name}")

    all_agents = registry.list_agents()
    print(f"  All agent IDs: {all_agents}")

    print("\n=== Singleton Behavior ===")
    another_ref = AgentRegistry()
    print(f"  Same instance: {registry is another_ref}")
    print(f"  Count from new ref: {another_ref.count()}")

    print("\n=== Register a Swarm ===")
    swarm = Swarm(agents=[agent1, agent2])
    registry.register("swarm-main", swarm)
    print(f"  Total registered: {registry.count()}")

    print("\n=== Unregister ===")
    registry.unregister(agent3.id)
    print(f"  After removing reviewer: {registry.count()}")
    print(f"  Remaining: {registry.list_agents()}")

    print("\n=== Cleanup ===")
    registry.clear()
    print(f"  After clear: {registry.count()}")


if __name__ == "__main__":
    main()
