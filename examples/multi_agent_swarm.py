"""
Multi-Agent Swarm Example

This example shows how to create a swarm of agents that work together.
"""
import asyncio
from agentic_swarm import Agent, Swarm, tool


@tool
def research(topic: str) -> str:
    """Research a topic.
    
    Args:
        topic: Topic to research
    
    Returns:
        Research findings
    """
    return f"Research findings about {topic}: This is a fascinating subject with many aspects to explore."


@tool
def write_content(topic: str, research: str) -> str:
    """Write content based on research.
    
    Args:
        topic: Topic to write about
        research: Research to base the content on
    
    Returns:
        Written content
    """
    return f"# Article about {topic}\n\nBased on our research: {research}\n\nThis is a well-written article."


@tool
def review_content(content: str) -> str:
    """Review and improve content.
    
    Args:
        content: Content to review
    
    Returns:
        Review feedback
    """
    return f"Review: The content is good. Suggested improvements: Add more examples."


async def main():
    researcher = Agent(
        name="researcher",
        role="You research topics thoroughly and provide detailed findings.",
        tools=[research],
    )
    
    writer = Agent(
        name="writer",
        role="You write engaging content based on research.",
        tools=[write_content],
    )
    
    reviewer = Agent(
        name="reviewer",
        role="You review content and suggest improvements.",
        tools=[review_content],
    )
    
    swarm = Swarm(agents=[researcher, writer, reviewer])
    
    print(f"Created swarm with {len(swarm.agents)} agents:")
    for agent in swarm.agents:
        print(f"  - {agent.name}: {agent.role[:50]}...")
    
    print("\nRunning swarm sequentially...")
    result = await swarm.run("Write an article about AI agents", strategy="sequential")
    
    print(f"\nSwarm completed with {len(result.results)} results")
    print(f"Success: {result.success}")


if __name__ == "__main__":
    asyncio.run(main())
