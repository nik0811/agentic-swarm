import pytest
from unittest.mock import MagicMock

from agentic_swarm.core.registry import AgentRegistry


class TestAgentRegistry:
    def setup_method(self):
        AgentRegistry.reset()

    def teardown_method(self):
        AgentRegistry.reset()

    def test_singleton(self):
        r1 = AgentRegistry()
        r2 = AgentRegistry()
        assert r1 is r2

    def test_register_and_get(self):
        registry = AgentRegistry()
        agent = MagicMock()
        registry.register("agent-1", agent)
        assert registry.get("agent-1") is agent

    def test_get_nonexistent(self):
        registry = AgentRegistry()
        assert registry.get("ghost") is None

    def test_unregister(self):
        registry = AgentRegistry()
        registry.register("agent-1", MagicMock())
        registry.unregister("agent-1")
        assert registry.get("agent-1") is None

    def test_unregister_nonexistent(self):
        registry = AgentRegistry()
        registry.unregister("nope")  # should not raise

    def test_count(self):
        registry = AgentRegistry()
        assert registry.count() == 0
        registry.register("a1", MagicMock())
        registry.register("a2", MagicMock())
        assert registry.count() == 2

    def test_list_agents(self):
        registry = AgentRegistry()
        registry.register("alpha", MagicMock())
        registry.register("beta", MagicMock())
        agents = registry.list_agents()
        assert "alpha" in agents
        assert "beta" in agents
        assert len(agents) == 2

    def test_clear(self):
        registry = AgentRegistry()
        registry.register("a", MagicMock())
        registry.register_swarm("s1", MagicMock())
        registry.clear()
        assert registry.count() == 0
        assert registry.get_swarm("s1") is None

    def test_reset_creates_new_instance(self):
        r1 = AgentRegistry()
        r1.register("x", MagicMock())
        AgentRegistry.reset()
        r2 = AgentRegistry()
        assert r2.count() == 0
        assert r1 is not r2

    def test_register_swarm(self):
        registry = AgentRegistry()
        swarm = MagicMock()
        registry.register_swarm("swarm-1", swarm)
        assert registry.get_swarm("swarm-1") is swarm

    def test_unregister_swarm(self):
        registry = AgentRegistry()
        registry.register_swarm("swarm-1", MagicMock())
        registry.unregister_swarm("swarm-1")
        assert registry.get_swarm("swarm-1") is None

    def test_list_by_state(self):
        registry = AgentRegistry()
        agent_running = MagicMock()
        agent_running.state = "RUNNING"
        agent_done = MagicMock()
        agent_done.state = "DONE"

        registry.register("r1", agent_running)
        registry.register("d1", agent_done)

        running = registry.list_by_state("RUNNING")
        assert "r1" in running
        assert "d1" not in running
