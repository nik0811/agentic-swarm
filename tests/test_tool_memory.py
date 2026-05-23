"""Tests for ToolMemory - Tool Usage Pattern Storage."""

import pytest

from agentic_swarm.memory.tool_memory import ToolMemory, ToolStats, ToolUsageRecord


class TestToolMemory:
    """Test ToolMemory functionality."""

    def test_create_tool_memory(self):
        """Test creating a tool memory instance."""
        mem = ToolMemory(agent_id="test-agent")
        assert mem.agent_id == "test-agent"
        assert len(mem._history) == 0
        assert len(mem._stats) == 0

    def test_record_usage_success(self):
        """Test recording successful tool usage."""
        mem = ToolMemory(agent_id="test")
        
        record = mem.record_usage(
            tool_name="web_search",
            task_description="Search for Python tutorials",
            success=True,
            duration_ms=150.0,
        )
        
        assert record.tool_name == "web_search"
        assert record.success is True
        assert record.duration_ms == 150.0
        assert len(record.task_keywords) > 0
        assert "python" in record.task_keywords or "tutorials" in record.task_keywords

    def test_record_usage_failure(self):
        """Test recording failed tool usage."""
        mem = ToolMemory(agent_id="test")
        
        record = mem.record_usage(
            tool_name="api_call",
            task_description="Call external API",
            success=False,
            error_message="Connection timeout",
        )
        
        assert record.success is False
        assert record.error_message == "Connection timeout"

    def test_get_tool_stats(self):
        """Test getting tool statistics."""
        mem = ToolMemory(agent_id="test")
        
        # Record multiple usages
        mem.record_usage("tool_a", "task 1", success=True, duration_ms=100)
        mem.record_usage("tool_a", "task 2", success=True, duration_ms=200)
        mem.record_usage("tool_a", "task 3", success=False, duration_ms=50)
        
        stats = mem.get_tool_stats("tool_a")
        
        assert stats is not None
        assert stats.total_uses == 3
        assert stats.successes == 2
        assert stats.failures == 1
        assert stats.success_rate == pytest.approx(2/3)
        assert stats.avg_duration_ms == pytest.approx(350/3)

    def test_get_tool_stats_missing(self):
        """Test getting stats for unknown tool."""
        mem = ToolMemory(agent_id="test")
        stats = mem.get_tool_stats("nonexistent")
        assert stats is None

    def test_get_all_stats(self):
        """Test getting all tool statistics."""
        mem = ToolMemory(agent_id="test")
        
        mem.record_usage("tool_a", "task", success=True)
        mem.record_usage("tool_b", "task", success=True)
        mem.record_usage("tool_b", "task", success=False)
        
        all_stats = mem.get_all_stats()
        
        assert len(all_stats) == 2
        assert "tool_a" in all_stats
        assert "tool_b" in all_stats

    def test_get_success_rate(self):
        """Test getting success rate for a tool."""
        mem = ToolMemory(agent_id="test")
        
        mem.record_usage("tool", "task", success=True)
        mem.record_usage("tool", "task", success=True)
        mem.record_usage("tool", "task", success=False)
        mem.record_usage("tool", "task", success=True)
        
        rate = mem.get_success_rate("tool")
        assert rate == pytest.approx(0.75)

    def test_get_best_tool_for_task(self):
        """Test getting best tool for a task."""
        mem = ToolMemory(agent_id="test")
        
        # web_search is good for search tasks
        mem.record_usage("web_search", "search for information", success=True)
        mem.record_usage("web_search", "search the web", success=True)
        mem.record_usage("web_search", "find data online", success=True)
        
        # calculator is good for math
        mem.record_usage("calculator", "calculate sum", success=True)
        mem.record_usage("calculator", "math operation", success=True)
        
        # web_search fails for math
        mem.record_usage("web_search", "calculate numbers", success=False)
        
        # Should recommend web_search for search tasks
        best = mem.get_best_tool_for("search for Python docs")
        assert best == "web_search"
        
        # Should recommend calculator for math
        best = mem.get_best_tool_for("calculate the total")
        assert best == "calculator"

    def test_get_best_tool_with_available_filter(self):
        """Test getting best tool with available tools filter."""
        mem = ToolMemory(agent_id="test")
        
        mem.record_usage("tool_a", "task type x", success=True)
        mem.record_usage("tool_a", "task type x", success=True)
        mem.record_usage("tool_b", "task type x", success=True)
        
        # Without filter, tool_a should be best (more successes)
        best = mem.get_best_tool_for("task type x")
        assert best == "tool_a"
        
        # With filter excluding tool_a
        best = mem.get_best_tool_for("task type x", available_tools=["tool_b", "tool_c"])
        assert best == "tool_b"

    def test_get_tools_for_task_type(self):
        """Test getting tools for a task type."""
        mem = ToolMemory(agent_id="test")
        
        mem.record_usage("search", "find information", success=True)
        mem.record_usage("search", "search data", success=True)
        mem.record_usage("api", "fetch data", success=True)
        mem.record_usage("api", "search api", success=False)
        
        tools = mem.get_tools_for_task_type(["search", "data"])
        
        assert len(tools) > 0
        # search should rank higher (more successes with these keywords)

    def test_get_recent_failures(self):
        """Test getting recent failures."""
        mem = ToolMemory(agent_id="test")
        
        mem.record_usage("tool", "task 1", success=True)
        mem.record_usage("tool", "task 2", success=False, error_message="Error 1")
        mem.record_usage("tool", "task 3", success=True)
        mem.record_usage("tool", "task 4", success=False, error_message="Error 2")
        
        failures = mem.get_recent_failures()
        
        assert len(failures) == 2
        assert failures[0].error_message == "Error 1"
        assert failures[1].error_message == "Error 2"

    def test_get_recent_failures_by_tool(self):
        """Test getting recent failures for specific tool."""
        mem = ToolMemory(agent_id="test")
        
        mem.record_usage("tool_a", "task", success=False)
        mem.record_usage("tool_b", "task", success=False)
        mem.record_usage("tool_a", "task", success=False)
        
        failures = mem.get_recent_failures(tool_name="tool_a")
        
        assert len(failures) == 2
        assert all(f.tool_name == "tool_a" for f in failures)

    def test_get_history(self):
        """Test getting usage history."""
        mem = ToolMemory(agent_id="test")
        
        mem.record_usage("tool", "task 1", success=True)
        mem.record_usage("tool", "task 2", success=False)
        mem.record_usage("tool", "task 3", success=True)
        
        # All history
        history = mem.get_history()
        assert len(history) == 3
        
        # Success only
        success_history = mem.get_history(success_only=True)
        assert len(success_history) == 2

    def test_max_history_limit(self):
        """Test that history is limited to max_history."""
        mem = ToolMemory(agent_id="test", max_history=5)
        
        for i in range(10):
            mem.record_usage("tool", f"task {i}", success=True)
        
        assert len(mem._history) == 5
        # Should keep the most recent
        assert mem._history[-1].task_description == "task 9"

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        mem = ToolMemory(agent_id="test")
        
        mem.record_usage("tool_a", "task 1", success=True, duration_ms=100)
        mem.record_usage("tool_a", "task 2", success=False, error_message="Error")
        mem.record_usage("tool_b", "task 3", success=True)
        
        # Serialize
        data = mem.to_dict()
        assert data["agent_id"] == "test"
        assert len(data["history"]) == 3
        assert len(data["stats"]) == 2
        
        # Deserialize
        restored = ToolMemory.from_dict(data)
        assert restored.agent_id == "test"
        assert len(restored._history) == 3
        
        stats = restored.get_tool_stats("tool_a")
        assert stats.total_uses == 2
        assert stats.successes == 1

    def test_clear(self):
        """Test clearing tool memory."""
        mem = ToolMemory(agent_id="test")
        
        mem.record_usage("tool", "task", success=True)
        mem.record_usage("tool", "task", success=True)
        
        mem.clear()
        
        assert len(mem._history) == 0
        assert len(mem._stats) == 0

    def test_get_summary(self):
        """Test getting memory summary."""
        mem = ToolMemory(agent_id="test")
        
        mem.record_usage("tool_a", "task", success=True)
        mem.record_usage("tool_a", "task", success=True)
        mem.record_usage("tool_b", "task", success=False)
        
        summary = mem.get_summary()
        
        assert summary["agent_id"] == "test"
        assert summary["total_tools_tracked"] == 2
        assert summary["total_executions"] == 3
        assert summary["overall_success_rate"] == pytest.approx(2/3)
        assert summary["history_size"] == 3

    def test_keyword_extraction(self):
        """Test keyword extraction from task descriptions."""
        mem = ToolMemory(agent_id="test")
        
        record = mem.record_usage(
            "tool",
            "Search the web for Python programming tutorials and examples",
            success=True,
        )
        
        # Should extract meaningful keywords, not stop words
        assert "search" in record.task_keywords
        assert "python" in record.task_keywords
        assert "programming" in record.task_keywords
        # Stop words should be excluded
        assert "the" not in record.task_keywords
        assert "for" not in record.task_keywords
        assert "and" not in record.task_keywords
