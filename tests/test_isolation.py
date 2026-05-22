"""Tests for Agent sandbox and data isolation features."""

import pytest
from agentic_swarm import Agent
from agentic_swarm.lifecycle.sandbox import SandboxConfig
from agentic_swarm.core.exceptions import SandboxTimeoutError


class TestAgentIsolation:
    """Test data isolation between agents."""
    
    def test_agent_has_namespace(self):
        """Each agent should have a unique namespace."""
        agent = Agent(name="test", role="tester")
        assert agent.namespace.startswith("agent:")
        assert agent.id in agent.namespace
    
    def test_agents_have_different_namespaces(self):
        """Different agents should have different namespaces."""
        agent1 = Agent(name="agent1", role="tester")
        agent2 = Agent(name="agent2", role="tester")
        assert agent1.namespace != agent2.namespace
    
    def test_agent_can_access_own_namespace(self):
        """Agent should be able to access its own namespace."""
        agent = Agent(name="test", role="tester")
        assert agent.can_access(agent.namespace)
    
    def test_agent_cannot_access_other_namespace(self):
        """Agent should not be able to access another agent's namespace."""
        agent1 = Agent(name="agent1", role="tester")
        agent2 = Agent(name="agent2", role="tester")
        assert not agent1.can_access(agent2.namespace)
        assert not agent2.can_access(agent1.namespace)
    
    def test_isolate_data_adds_metadata(self):
        """isolate_data should add namespace metadata."""
        agent = Agent(name="test", role="tester")
        data = {"key": "value"}
        isolated = agent.isolate_data(data)
        
        assert "_namespace" in isolated
        assert "_agent_id" in isolated
        assert isolated["_namespace"] == agent.namespace
        assert isolated["_agent_id"] == agent.id
        assert isolated["key"] == "value"
    
    def test_grant_access(self):
        """grant_access_to should allow another agent to access namespace."""
        agent1 = Agent(name="agent1", role="tester")
        agent2 = Agent(name="agent2", role="tester")
        
        assert not agent2.can_access(agent1.namespace)
        agent1.grant_access_to(agent2)
        assert agent2.can_access(agent1.namespace)
    
    def test_revoke_access(self):
        """revoke_access_from should remove access."""
        agent1 = Agent(name="agent1", role="tester")
        agent2 = Agent(name="agent2", role="tester")
        
        agent1.grant_access_to(agent2)
        assert agent2.can_access(agent1.namespace)
        
        agent1.revoke_access_from(agent2)
        assert not agent2.can_access(agent1.namespace)
    
    def test_tenant_isolation(self):
        """Agents in different tenants should be isolated."""
        agent1 = Agent(name="agent1", role="tester", tenant_id="tenant_a")
        agent2 = Agent(name="agent2", role="tester", tenant_id="tenant_b")
        
        assert "tenant_a" in agent1.namespace
        assert "tenant_b" in agent2.namespace
        assert not agent1.can_access(agent2.namespace)
        assert not agent2.can_access(agent1.namespace)
    
    def test_isolation_disabled(self):
        """With isolation disabled, agent can access any resource."""
        agent = Agent(name="test", role="tester", enable_isolation=False)
        assert agent.can_access("any:resource:path")
        assert agent.can_access("another:namespace")
    
    def test_isolate_data_noop_when_disabled(self):
        """isolate_data should return original data when isolation disabled."""
        agent = Agent(name="test", role="tester", enable_isolation=False)
        data = {"key": "value"}
        isolated = agent.isolate_data(data)
        assert isolated == data
        assert "_namespace" not in isolated


class TestAgentSandbox:
    """Test sandbox execution."""
    
    def test_agent_has_sandbox(self):
        """Agent should have a sandbox."""
        agent = Agent(name="test", role="tester")
        assert agent.sandbox is not None
    
    def test_custom_sandbox_config(self):
        """Agent should accept custom sandbox config."""
        config = SandboxConfig(
            cpu_limit=0.5,
            memory_limit_mb=128,
            timeout_seconds=10,
        )
        agent = Agent(name="test", role="tester", sandbox_config=config)
        assert agent._sandbox.config.cpu_limit == 0.5
        assert agent._sandbox.config.memory_limit_mb == 128
        assert agent._sandbox.config.timeout_seconds == 10
    
    @pytest.mark.asyncio
    async def test_execute_isolated_sync_function(self):
        """execute_isolated should run sync functions."""
        agent = Agent(name="test", role="tester")
        
        def add(a, b):
            return a + b
        
        result = await agent.execute_isolated(add, 2, 3)
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_execute_isolated_async_function(self):
        """execute_isolated should run async functions."""
        agent = Agent(name="test", role="tester")
        
        async def async_add(a, b):
            return a + b
        
        result = await agent.execute_isolated(async_add, 2, 3)
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_execute_isolated_timeout(self):
        """execute_isolated should timeout long-running functions."""
        import asyncio
        
        config = SandboxConfig(timeout_seconds=1)
        agent = Agent(name="test", role="tester", sandbox_config=config)
        
        async def slow_function():
            await asyncio.sleep(10)
            return "done"
        
        with pytest.raises(SandboxTimeoutError):
            await agent.execute_isolated(slow_function)


class TestChildAgentIsolation:
    """Test isolation inheritance for child agents."""
    
    @pytest.mark.asyncio
    async def test_child_inherits_tenant_id(self):
        """Child agent should inherit parent's tenant_id."""
        parent = Agent(name="parent", role="parent", tenant_id="company_xyz")
        child = await parent.create_agent(name="child", role="child")
        
        assert child._tenant_id == "company_xyz"
        assert "company_xyz" in child.namespace
    
    @pytest.mark.asyncio
    async def test_child_has_separate_namespace(self):
        """Child should have different namespace than parent."""
        parent = Agent(name="parent", role="parent")
        child = await parent.create_agent(name="child", role="child")
        
        assert parent.namespace != child.namespace
    
    @pytest.mark.asyncio
    async def test_parent_child_isolated_by_default(self):
        """Parent and child should be isolated by default."""
        parent = Agent(name="parent", role="parent")
        child = await parent.create_agent(name="child", role="child")
        
        assert not parent.can_access(child.namespace)
        assert not child.can_access(parent.namespace)
    
    @pytest.mark.asyncio
    async def test_parent_can_grant_child_access(self):
        """Parent can grant child access to its namespace."""
        parent = Agent(name="parent", role="parent")
        child = await parent.create_agent(name="child", role="child")
        
        parent.grant_access_to(child)
        assert child.can_access(parent.namespace)


class TestTerminateCleanup:
    """Test that terminate cleans up isolation."""
    
    @pytest.mark.asyncio
    async def test_terminate_unregisters_from_isolation(self):
        """Terminate should unregister agent from isolation."""
        from agentic_swarm.agent import _global_isolation
        
        agent = Agent(name="test", role="tester")
        agent_id = agent.id
        
        # Agent should be registered
        assert agent_id in _global_isolation._namespaces
        
        await agent.terminate()
        
        # Agent should be unregistered
        assert agent_id not in _global_isolation._namespaces
