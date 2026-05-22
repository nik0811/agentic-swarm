import pytest
from agentic_swarm import Agent, tool
from agentic_swarm.core.types import AgentState


def test_agent_creation():
    agent = Agent(name="test", role="Test agent")
    assert agent.name == "test"
    assert agent.state == AgentState.CREATED
    assert agent.id is not None


def test_agent_with_tools():
    @tool
    def greet(name: str) -> str:
        return f"Hello {name}"
    
    agent = Agent(name="greeter", role="Greets people", tools=[greet])
    assert "greet" in agent.tools


def test_agent_core_memory():
    agent = Agent(name="test", role="Test persona")
    assert agent._core_memory.name == "test"
    assert agent._core_memory.persona == "Test persona"


def test_agent_role_property():
    agent = Agent(name="test", role="My role description")
    assert agent.role == "My role description"


@pytest.mark.asyncio
async def test_agent_create_child():
    parent = Agent(name="parent", role="Parent agent")
    child = await parent.create_agent(name="child", role="Child agent")
    
    assert child.parent == parent
    assert child in parent._children
    assert child.name == "child"


@pytest.mark.asyncio
async def test_agent_send_message():
    agent1 = Agent(name="sender", role="Sends messages")
    agent2 = Agent(name="receiver", role="Receives messages")
    
    await agent1.send(agent2, "Hello!")
    
    entries = agent2._recall_memory.get_all()
    assert any("Hello!" in str(e.content) for e in entries)


@pytest.mark.asyncio
async def test_agent_terminate():
    parent = Agent(name="parent", role="Parent")
    child = await parent.create_agent(name="child", role="Child")
    
    await parent.terminate()
    
    assert parent.state == AgentState.TERMINATED
    assert child.state == AgentState.TERMINATED


@pytest.mark.asyncio
async def test_agent_run_placeholder():
    agent = Agent(name="test", role="Test agent")
    result = await agent.run("Do something")
    
    assert agent.state == AgentState.DONE
    assert "Placeholder" in str(result)


def test_agent_equality():
    agent1 = Agent(name="test", role="Test")
    agent2 = Agent(name="test", role="Test")
    
    assert agent1 != agent2
    assert agent1 == agent1


@pytest.mark.asyncio
async def test_agent_execute_tool():
    @tool
    def add(a: int, b: int) -> int:
        return a + b
    
    agent = Agent(name="calc", role="Calculator", tools=[add])
    result = await agent._execute_tool("add", {"a": 2, "b": 3})
    assert result == 5


@pytest.mark.asyncio
async def test_agent_execute_tool_not_found():
    from agentic_swarm.core.exceptions import ToolNotFoundError
    
    agent = Agent(name="test", role="Test")
    with pytest.raises(ToolNotFoundError):
        await agent._execute_tool("nonexistent", {})
