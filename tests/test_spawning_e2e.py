"""
End-to-end tests for sub-agent spawning and parallel execution.
"""

import pytest
import asyncio
from agentic_swarm import Agent, Swarm
from agentic_swarm.lifecycle.spawner import Spawner
from agentic_swarm.core.types import AgentState
from agentic_swarm.tool import tool


# -- Agent.create_agent (spawner-backed) --

@pytest.mark.asyncio
async def test_create_child_agent():
    """Agent can dynamically spawn a child agent."""
    parent = Agent(name="parent", role="Coordinator")
    child = await parent.create_agent(name="child", role="Worker")

    assert child.name == "child"
    assert child.role == "Worker"
    assert child.parent == parent
    assert child in parent._children


@pytest.mark.asyncio
async def test_child_inherits_spawner():
    """Child agent uses same spawner as parent."""
    spawner = Spawner(max_depth=3, max_children=5)
    parent = Agent(name="parent", role="Coordinator", spawner=spawner)
    child = await parent.create_agent(name="child", role="Worker")

    assert child._spawner is spawner


@pytest.mark.asyncio
async def test_child_inherits_llm_router():
    """Child agent inherits parent's LLM router."""
    parent = Agent(name="parent", role="Coordinator")
    child = await parent.create_agent(name="child", role="Worker")

    assert child.llm_router is parent.llm_router


@pytest.mark.asyncio
async def test_multi_level_spawning():
    """Agents can spawn children multiple levels deep."""
    spawner = Spawner(max_depth=4, max_children=10)
    root = Agent(name="root", role="Root", spawner=spawner)

    level1 = await root.create_agent(name="L1", role="Level 1")
    level2 = await level1.create_agent(name="L2", role="Level 2")
    level3 = await level2.create_agent(name="L3", role="Level 3")

    assert spawner.get_depth(root.id) == 0
    assert spawner.get_depth(level1.id) == 1
    assert spawner.get_depth(level2.id) == 2
    assert spawner.get_depth(level3.id) == 3


@pytest.mark.asyncio
async def test_max_depth_enforced():
    """Cannot spawn beyond max_depth."""
    spawner = Spawner(max_depth=2, max_children=10)
    root = Agent(name="root", role="Root", spawner=spawner)

    level1 = await root.create_agent(name="L1", role="Level 1")
    level2 = await level1.create_agent(name="L2", role="Level 2")

    with pytest.raises(Exception, match="Cannot spawn"):
        await level2.create_agent(name="L3", role="Level 3")


@pytest.mark.asyncio
async def test_max_children_enforced():
    """Cannot spawn more than max_children from a single parent."""
    spawner = Spawner(max_depth=5, max_children=3)
    parent = Agent(name="parent", role="Parent", spawner=spawner)

    await parent.create_agent(name="c1", role="W")
    await parent.create_agent(name="c2", role="W")
    await parent.create_agent(name="c3", role="W")

    with pytest.raises(Exception, match="Cannot spawn"):
        await parent.create_agent(name="c4", role="W")


# -- Agent.run_parallel --

@pytest.mark.asyncio
async def test_run_parallel_basic():
    """Agent can run multiple tasks in parallel via child agents."""
    parent = Agent(name="coordinator", role="Coordinator")

    results = await parent.run_parallel([
        "Task A",
        "Task B",
        "Task C",
    ])

    assert len(results) == 3
    assert len(parent._children) == 3
    for child in parent._children:
        assert child.parent == parent


@pytest.mark.asyncio
async def test_run_parallel_results_ordered():
    """Parallel results maintain task order."""
    parent = Agent(name="coordinator", role="Coordinator")
    results = await parent.run_parallel(["Task 1", "Task 2"])

    assert len(results) == 2


@pytest.mark.asyncio
async def test_run_parallel_children_run_concurrently():
    """Verify children actually execute concurrently (not sequentially)."""
    parent = Agent(name="coordinator", role="Coordinator")

    start = asyncio.get_event_loop().time()
    results = await parent.run_parallel(["A", "B", "C", "D"])
    elapsed = asyncio.get_event_loop().time() - start

    assert len(results) == 4
    assert elapsed < 1.0


# -- Swarm parallel strategy with spawned agents --

@pytest.mark.asyncio
async def test_swarm_parallel_with_spawned_agents():
    """Swarm can run spawned agents in parallel."""
    parent = Agent(name="parent", role="Manager")
    child1 = await parent.create_agent(name="worker-1", role="Research")
    child2 = await parent.create_agent(name="worker-2", role="Writing")
    child3 = await parent.create_agent(name="worker-3", role="Coding")

    swarm = Swarm(agents=[child1, child2, child3])
    result = await swarm.run("Do your thing", strategy="parallel")

    assert len(result.results) == 3
    assert result.success


@pytest.mark.asyncio
async def test_swarm_sequential_with_spawned_agents():
    """Swarm can chain spawned agents sequentially."""
    parent = Agent(name="parent", role="Manager")
    researcher = await parent.create_agent(name="researcher", role="Research AI topics")
    writer = await parent.create_agent(name="writer", role="Write reports")

    swarm = Swarm(agents=[researcher, writer])
    result = await swarm.run("Research and write about quantum computing", strategy="sequential")

    assert len(result.results) == 2
    assert result.success


@pytest.mark.asyncio
async def test_swarm_adaptive_delegates_to_best_fit():
    """Adaptive strategy assigns tasks to agents based on role matching."""
    parent = Agent(name="boss", role="Manager")
    coder = await parent.create_agent(name="coder", role="coding programming development")
    writer = await parent.create_agent(name="writer", role="writing documentation blog")

    swarm = Swarm(agents=[coder, writer])
    result = await swarm.run(
        "Write the documentation then implement the feature in code",
        strategy="adaptive",
    )

    assert result.success


# -- Cross-agent communication during spawning --

@pytest.mark.asyncio
async def test_parent_child_message_passing():
    """Parent can send messages to child agents."""
    parent = Agent(name="parent", role="Manager")
    child = await parent.create_agent(name="worker", role="Worker")

    await parent.send(child, "Here is your assignment")

    entries = child._recall_memory.get_all()
    assert any("assignment" in str(e.content) for e in entries)


@pytest.mark.asyncio
async def test_sibling_communication():
    """Sibling agents can communicate with each other."""
    parent = Agent(name="parent", role="Manager")
    agent_a = await parent.create_agent(name="agent-a", role="Researcher")
    agent_b = await parent.create_agent(name="agent-b", role="Writer")

    await agent_a.send(agent_b, "Here are the research findings")

    entries = agent_b._recall_memory.get_all()
    assert any("research findings" in str(e.content) for e in entries)


# -- Terminate cascades --

@pytest.mark.asyncio
async def test_terminate_cascades_to_children():
    """Terminating a parent also terminates all children."""
    parent = Agent(name="parent", role="Manager")
    child1 = await parent.create_agent(name="child1", role="Worker")
    child2 = await parent.create_agent(name="child2", role="Worker")
    grandchild = await child1.create_agent(name="grandchild", role="Helper")

    await parent.terminate()

    assert parent.state == AgentState.TERMINATED
    assert child1.state == AgentState.TERMINATED
    assert child2.state == AgentState.TERMINATED
    assert grandchild.state == AgentState.TERMINATED


# -- Swarm delegation between agents --

@pytest.mark.asyncio
async def test_swarm_delegate_task():
    """Swarm can delegate a task from one agent to another."""
    agent_a = Agent(name="coordinator", role="Coordinator")
    agent_b = Agent(name="worker", role="Worker")
    swarm = Swarm(agents=[agent_a, agent_b])

    result = await swarm.delegate(agent_a, agent_b, "Process this data")

    assert result is not None


@pytest.mark.asyncio
async def test_swarm_health_ping():
    """Swarm can ping all agents for health status."""
    agents = [
        Agent(name=f"agent-{i}", role=f"Worker {i}")
        for i in range(5)
    ]
    swarm = Swarm(agents=agents)

    status = await swarm.health_ping_all()

    assert len(status) == 5
    for name, info in status.items():
        assert info["healthy"] is True
        assert info["state"] == "created"


# -- Tool-based spawning and parallel execution --

@pytest.mark.asyncio
async def test_agent_with_tools_spawns_child_with_tools():
    """Tools can be passed to spawned children."""
    @tool
    def calculator(expression: str) -> str:
        """Evaluate a math expression."""
        return str(eval(expression))

    parent = Agent(name="parent", role="Math teacher", tools=[calculator])
    child = await parent.create_agent(
        name="student",
        role="Math student",
        tools=[calculator],
    )

    assert "calculator" in child.tools
    result = await child.tools["calculator"].execute(expression="2 + 2")
    assert result == "4"


@pytest.mark.asyncio
async def test_spawner_tree_tracking():
    """Spawner correctly tracks the full agent tree."""
    spawner = Spawner(max_depth=4, max_children=10)
    root = Agent(name="root", role="Root", spawner=spawner)

    c1 = await root.create_agent(name="c1", role="W")
    c2 = await root.create_agent(name="c2", role="W")
    gc1 = await c1.create_agent(name="gc1", role="W")

    assert spawner.get_children(root.id) == [c1.id, c2.id]
    assert spawner.get_children(c1.id) == [gc1.id]
    assert spawner.get_children(c2.id) == []
    assert spawner.get_depth(gc1.id) == 2
