"""
Simple Agent Example

This example shows how to create a basic agent with tools.
"""
import asyncio
from agentic_swarm import Agent, tool


@tool
def calculator(expression: str) -> float:
    """Evaluate a math expression.
    
    Args:
        expression: Math expression to evaluate (e.g., "2 + 2")
    
    Returns:
        Result of the calculation
    """
    return eval(expression)


@tool
def greet(name: str) -> str:
    """Greet someone by name.
    
    Args:
        name: Name of the person to greet
    
    Returns:
        Greeting message
    """
    return f"Hello, {name}! Nice to meet you."


async def main():
    agent = Agent(
        name="assistant",
        role="You are a helpful assistant that can do math and greet people.",
        tools=[calculator, greet],
    )
    
    print(f"Created agent: {agent.name}")
    print(f"Agent ID: {agent.id}")
    print(f"Available tools: {list(agent.tools.keys())}")
    
    result = await agent._execute_tool("calculator", {"expression": "2 + 2 * 3"})
    print(f"\nCalculator result: {result}")
    
    result = await agent._execute_tool("greet", {"name": "World"})
    print(f"Greeting: {result}")


if __name__ == "__main__":
    asyncio.run(main())
