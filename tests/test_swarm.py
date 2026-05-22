import pytest
from agentic_swarm import Agent, Swarm
from agentic_swarm.swarm import SwarmResult


def test_swarm_creation():
    swarm = Swarm()
    assert len(swarm.agents) == 0


def test_swarm_with_agents():
    agent1 = Agent(name="a1", role="Agent 1")
    agent2 = Agent(name="a2", role="Agent 2")
    swarm = Swarm(agents=[agent1, agent2])
    
    assert len(swarm.agents) == 2


def test_swarm_add_agent():
    swarm = Swarm()
    agent = Agent(name="test", role="Test")
    swarm.add_agent(agent)
    
    assert len(swarm.agents) == 1
    assert swarm.get_agent(agent.id) == agent


def test_swarm_remove_agent():
    agent = Agent(name="test", role="Test")
    swarm = Swarm(agents=[agent])
    
    swarm.remove_agent(agent.id)
    assert len(swarm.agents) == 0


@pytest.mark.asyncio
async def test_swarm_run_sequential():
    agent1 = Agent(name="a1", role="Agent 1")
    agent2 = Agent(name="a2", role="Agent 2")
    swarm = Swarm(agents=[agent1, agent2])
    
    result = await swarm.run("Test task", strategy="sequential")
    
    assert isinstance(result, SwarmResult)
    assert len(result.results) == 2


@pytest.mark.asyncio
async def test_swarm_run_parallel():
    agent1 = Agent(name="a1", role="Agent 1")
    agent2 = Agent(name="a2", role="Agent 2")
    swarm = Swarm(agents=[agent1, agent2])
    
    result = await swarm.run("Test task", strategy="parallel")
    
    assert isinstance(result, SwarmResult)
    assert len(result.results) == 2


@pytest.mark.asyncio
async def test_swarm_broadcast():
    agent1 = Agent(name="a1", role="Agent 1")
    agent2 = Agent(name="a2", role="Agent 2")
    swarm = Swarm(agents=[agent1, agent2])
    
    await swarm.broadcast("Hello everyone!")
    
    for agent in swarm.agents:
        entries = agent._recall_memory.get_all()
        assert any("Hello everyone!" in str(e.content) for e in entries)


@pytest.mark.asyncio
async def test_swarm_terminate_all():
    from agentic_swarm.core.types import AgentState
    
    agent1 = Agent(name="a1", role="Agent 1")
    agent2 = Agent(name="a2", role="Agent 2")
    swarm = Swarm(agents=[agent1, agent2])
    
    await swarm.terminate_all()
    
    assert agent1.state == AgentState.TERMINATED
    assert agent2.state == AgentState.TERMINATED
    assert len(swarm.agents) == 0


def test_swarm_result():
    result = SwarmResult()
    assert result.success is True
    
    result.errors.append(Exception("test"))
    assert result.success is False
