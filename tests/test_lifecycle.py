import pytest
from agentic_swarm.lifecycle.supervisor import Supervisor, HealthStatus
from agentic_swarm.lifecycle.healer import Healer
from agentic_swarm.lifecycle.spawner import Spawner
from agentic_swarm.lifecycle.sandbox import Sandbox, SandboxConfig
from agentic_swarm import Agent
from agentic_swarm.core.types import AgentState


def test_supervisor_register():
    supervisor = Supervisor()
    agent = Agent(name="test", role="Test")
    
    supervisor.register(agent)
    
    assert agent.id in supervisor._agents
    assert agent.id in supervisor._health


def test_supervisor_health_check():
    supervisor = Supervisor()
    agent = Agent(name="test", role="Test")
    supervisor.register(agent)
    
    health = supervisor.health_check(agent.id)
    
    assert health.status == HealthStatus.HEALTHY


def test_supervisor_record_error():
    supervisor = Supervisor(max_errors=2)
    agent = Agent(name="test", role="Test")
    supervisor.register(agent)
    
    supervisor.record_error(agent.id, "Error 1")
    supervisor.record_error(agent.id, "Error 2")
    
    health = supervisor.health_check(agent.id)
    assert health.status == HealthStatus.UNHEALTHY


def test_healer_snapshot():
    healer = Healer()
    agent = Agent(name="test", role="Test")
    agent._recall_memory.push("Hello", role="user")
    
    snapshot = healer.snapshot(agent)
    
    assert snapshot.agent_id == agent.id
    assert len(snapshot.recall_messages) == 1


@pytest.mark.asyncio
async def test_healer_recover():
    healer = Healer(max_retries=3)
    agent = Agent(name="test", role="Test")
    agent._state = AgentState.RECOVERING
    
    healer.snapshot(agent)
    success = await healer.recover(agent, Exception("Test error"))
    
    assert success is True
    assert agent.state == AgentState.RUNNING


def test_spawner_can_spawn():
    spawner = Spawner(max_depth=2, max_children=3)
    spawner.register_root("parent-1")
    
    assert spawner.can_spawn("parent-1") is True


@pytest.mark.asyncio
async def test_spawner_spawn():
    spawner = Spawner()
    parent = Agent(name="parent", role="Parent")
    spawner.register_root(parent.id)
    
    child = await spawner.spawn(parent, "child", "Child agent")
    
    assert child.name == "child"
    assert child.parent == parent
    assert spawner.get_depth(child.id) == 1


def test_spawner_max_depth():
    spawner = Spawner(max_depth=1)
    spawner._agent_depth["deep-agent"] = 1
    
    assert spawner.can_spawn("deep-agent") is False


@pytest.mark.asyncio
async def test_sandbox_execute():
    sandbox = Sandbox(SandboxConfig(timeout_seconds=5))
    
    async def simple_task():
        return 42
    
    result = await sandbox.execute(simple_task)
    
    assert result == 42


@pytest.mark.asyncio
async def test_sandbox_timeout():
    import asyncio
    sandbox = Sandbox(SandboxConfig(timeout_seconds=1))
    
    async def slow_task():
        await asyncio.sleep(10)
        return "done"
    
    with pytest.raises(TimeoutError):
        await sandbox.execute(slow_task)
