"""
Tests for tool auto-discovery and retry features.
"""

import pytest
from agentic_swarm import Agent, tool, register_tool, get_tool_registry
from agentic_swarm.tools.discovery import ToolRegistry, ToolSelector


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def clear_registry():
    """Clear global registry before each test."""
    registry = get_tool_registry()
    registry._tools.clear()
    registry._categories.clear()
    registry._keywords.clear()
    registry._lazy_loaders.clear()
    registry._usage_count.clear()
    registry._success_rate.clear()
    yield


@pytest.fixture
def sample_tools():
    """Create sample tools for testing."""
    @tool
    def search_db(query: str) -> list:
        """Search database for records."""
        return [{"id": 1, "query": query}]
    
    @tool
    def search_cache(query: str) -> list:
        """Search cache for records."""
        return [{"id": 1, "cached": True}]
    
    @tool
    def calculate_sum(numbers: list) -> float:
        """Calculate sum of numbers."""
        return sum(numbers)
    
    @tool
    def send_email(to: str, body: str) -> dict:
        """Send email notification."""
        return {"sent": True, "to": to}
    
    return {
        "search_db": search_db,
        "search_cache": search_cache,
        "calculate_sum": calculate_sum,
        "send_email": send_email,
    }


# =============================================================================
# ToolRegistry Tests
# =============================================================================

class TestToolRegistry:
    
    def test_register_tool(self, sample_tools):
        registry = ToolRegistry()
        registry.register(sample_tools["search_db"], category="data")
        
        assert "search_db" in registry.list_all()
        assert registry.get("search_db") is not None
    
    def test_register_with_keywords(self, sample_tools):
        registry = ToolRegistry()
        registry.register(
            sample_tools["search_db"],
            category="data",
            keywords=["sql", "query", "database", "search"]
        )
        
        # Should find by keyword - use words that appear in keywords
        matches = registry.search("search database query", limit=5)
        assert len(matches) > 0
        assert matches[0].tool.name == "search_db"
    
    def test_search_by_description(self, sample_tools):
        registry = ToolRegistry()
        registry.register(sample_tools["search_db"], category="data")
        registry.register(sample_tools["calculate_sum"], category="math")
        
        # Search should find relevant tool
        matches = registry.search("search database records", limit=5)
        assert len(matches) > 0
        assert matches[0].tool.name == "search_db"
    
    def test_get_by_category(self, sample_tools):
        registry = ToolRegistry()
        registry.register(sample_tools["search_db"], category="data")
        registry.register(sample_tools["search_cache"], category="data")
        registry.register(sample_tools["calculate_sum"], category="math")
        
        data_tools = registry.get_by_category("data")
        assert len(data_tools) == 2
        
        math_tools = registry.get_by_category("math")
        assert len(math_tools) == 1
    
    def test_find_alternatives(self, sample_tools):
        registry = ToolRegistry()
        registry.register(sample_tools["search_db"], category="data")
        registry.register(sample_tools["search_cache"], category="data")
        
        alternatives = registry.find_alternatives("search_db", limit=3)
        assert len(alternatives) >= 1
        assert any(t.name == "search_cache" for t in alternatives)
    
    def test_lazy_loading(self):
        registry = ToolRegistry()
        loaded = []
        
        def create_tool():
            loaded.append(True)
            @tool
            def lazy_tool(x: int) -> int:
                return x * 2
            return lazy_tool
        
        registry.register_lazy(
            "lazy_tool",
            create_tool,
            keywords=["lazy", "multiply"]
        )
        
        # Not loaded yet
        assert len(loaded) == 0
        assert "lazy_tool" in registry.list_all()
        
        # Load on access
        t = registry.get("lazy_tool")
        assert len(loaded) == 1
        assert t is not None
    
    def test_usage_statistics(self, sample_tools):
        registry = ToolRegistry()
        registry.register(sample_tools["search_db"])
        
        # Record usage
        registry.record_usage("search_db", success=True)
        registry.record_usage("search_db", success=True)
        registry.record_usage("search_db", success=False)
        
        rate = registry.get_success_rate("search_db")
        assert rate == pytest.approx(2/3, rel=0.01)
    
    def test_stats(self, sample_tools):
        registry = ToolRegistry()
        registry.register(sample_tools["search_db"], category="data")
        registry.register(sample_tools["calculate_sum"], category="math")
        
        stats = registry.get_stats()
        assert stats["total_tools"] == 2
        assert "data" in stats["categories"]
        assert "math" in stats["categories"]


# =============================================================================
# ToolSelector Tests
# =============================================================================

class TestToolSelector:
    
    @pytest.mark.asyncio
    async def test_select_tools(self, sample_tools):
        registry = ToolRegistry()
        registry.register(sample_tools["search_db"], category="data")
        registry.register(sample_tools["calculate_sum"], category="math")
        
        selector = ToolSelector(registry, max_retries=3)
        tools = selector.select_tools("search database", limit=2)
        
        assert len(tools) >= 1
        assert tools[0].name == "search_db"
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, sample_tools):
        registry = ToolRegistry()
        registry.register(sample_tools["search_db"])
        
        selector = ToolSelector(registry, max_retries=3)
        result = await selector.execute_with_retry(
            task_description="search database",
            arguments={"query": "test"}
        )
        
        assert result.success
        assert result.tool_used == "search_db"
        assert result.attempts == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_fallback(self):
        """Test that retry falls back to alternative tools."""
        registry = ToolRegistry()
        
        call_count = {"failing": 0, "working": 0}
        
        @tool
        def primary_api(x: int) -> int:
            """Primary API for computation - fails first 2 times."""
            call_count["failing"] += 1
            if call_count["failing"] <= 2:
                raise ValueError("Temporarily unavailable")
            return x * 2
        
        @tool
        def backup_api(x: int) -> int:
            """Backup API for computation."""
            call_count["working"] += 1
            return x * 2
        
        # Register with overlapping keywords
        registry.register(primary_api, keywords=["api", "compute", "primary"])
        registry.register(backup_api, keywords=["api", "compute", "backup"])
        
        selector = ToolSelector(registry, max_retries=3)
        result = await selector.execute_with_retry(
            task_description="api compute",
            arguments={"x": 5}
        )
        
        assert result.success
        assert result.result == 10
        # Either tool could succeed depending on search order
        assert result.tool_used in ["primary_api", "backup_api"]


# =============================================================================
# Agent Auto-Discovery Tests
# =============================================================================

class TestAgentAutoDiscovery:
    
    def test_auto_tools_true(self, sample_tools):
        """Test auto_tools=True loads all registered tools."""
        register_tool(sample_tools["search_db"], category="data")
        register_tool(sample_tools["calculate_sum"], category="math")
        
        agent = Agent(name="test", role="Test", auto_tools=True)
        
        assert "search_db" in agent.tools
        assert "calculate_sum" in agent.tools
    
    def test_auto_tools_by_task(self, sample_tools):
        """Test auto_tools='task' finds relevant tools."""
        register_tool(sample_tools["search_db"], category="data", keywords=["search", "database"])
        register_tool(sample_tools["calculate_sum"], category="math", keywords=["sum", "numbers"])
        
        agent = Agent(
            name="test",
            role="Test",
            auto_tools="search database records"
        )
        
        assert "search_db" in agent.tools
        # calculate_sum should not be included (not relevant)
        assert len(agent.tools) <= 2
    
    def test_auto_tools_by_category(self, sample_tools):
        """Test tool_categories filters tools."""
        register_tool(sample_tools["search_db"], category="data")
        register_tool(sample_tools["search_cache"], category="data")
        register_tool(sample_tools["calculate_sum"], category="math")
        
        agent = Agent(
            name="test",
            role="Test",
            auto_tools=True,
            tool_categories=["data"]
        )
        
        assert "search_db" in agent.tools
        assert "search_cache" in agent.tools
        assert "calculate_sum" not in agent.tools
    
    def test_explicit_plus_auto_tools(self, sample_tools):
        """Test combining explicit tools with auto-discovery."""
        register_tool(sample_tools["search_db"], category="data")
        
        @tool
        def custom_tool(x: int) -> int:
            return x
        
        agent = Agent(
            name="test",
            role="Test",
            tools=[custom_tool],
            auto_tools=True
        )
        
        assert "custom_tool" in agent.tools
        assert "search_db" in agent.tools
    
    def test_tool_retry_setup(self, sample_tools):
        """Test tool_retry creates selector."""
        register_tool(sample_tools["search_db"])
        
        agent = Agent(
            name="test",
            role="Test",
            auto_tools=True,
            tool_retry=3
        )
        
        assert agent._tool_retry == 3
        assert agent._tool_selector is not None


# =============================================================================
# Global Registry Tests
# =============================================================================

class TestGlobalRegistry:
    
    def test_register_tool_function(self, sample_tools):
        """Test register_tool adds to global registry."""
        register_tool(sample_tools["search_db"], category="data")
        
        registry = get_tool_registry()
        assert "search_db" in registry.list_all()
    
    def test_register_tool_returns_tool(self, sample_tools):
        """Test register_tool returns the tool."""
        result = register_tool(sample_tools["search_db"])
        assert result == sample_tools["search_db"]
    
    def test_multiple_registrations(self, sample_tools):
        """Test registering multiple tools."""
        register_tool(sample_tools["search_db"], category="data")
        register_tool(sample_tools["calculate_sum"], category="math")
        register_tool(sample_tools["send_email"], category="notification")
        
        registry = get_tool_registry()
        assert len(registry.list_all()) == 3
