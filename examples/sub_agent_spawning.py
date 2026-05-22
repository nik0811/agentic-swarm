"""
Sub-Agent Spawning Example

This example shows how agents can dynamically create sub-agents.
"""
import asyncio
from agentic_swarm import Agent, tool
from agentic_swarm.lifecycle import Spawner


@tool
def analyze(data: str) -> str:
    """Analyze data.
    
    Args:
        data: Data to analyze
    
    Returns:
        Analysis results
    """
    return f"Analysis of '{data}': Found 3 key insights."


async def main():
    spawner = Spawner(max_depth=3, max_children=5)
    
    coordinator = Agent(
        name="coordinator",
        role="You coordinate complex tasks by delegating to specialists.",
        tools=[analyze],
    )
    spawner.register_root(coordinator.id)
    
    print(f"Created coordinator: {coordinator.name}")
    print(f"Max spawn depth: {spawner._max_depth}")
    
    specialist1 = await spawner.spawn(
        coordinator,
        name="data_analyst",
        role="You specialize in data analysis.",
        tools=[analyze],
    )
    print(f"\nSpawned specialist: {specialist1.name}")
    print(f"  Parent: {specialist1.parent.name}")
    print(f"  Depth: {spawner.get_depth(specialist1.id)}")
    
    specialist2 = await spawner.spawn(
        coordinator,
        name="report_writer",
        role="You specialize in writing reports.",
        tools=[],
    )
    print(f"\nSpawned specialist: {specialist2.name}")
    
    print(f"\nCoordinator's children: {[c.name for c in coordinator._children]}")
    
    sub_specialist = await spawner.spawn(
        specialist1,
        name="deep_analyst",
        role="You do deep analysis.",
        tools=[analyze],
    )
    print(f"\nSpawned sub-specialist: {sub_specialist.name}")
    print(f"  Depth: {spawner.get_depth(sub_specialist.id)}")


if __name__ == "__main__":
    asyncio.run(main())
