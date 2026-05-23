"""
Tool Memory - Tool Usage Pattern Storage

Tracks tool usage history, success/failure rates, and learns from past executions.
Helps agents select the best tool for a task based on historical performance.

Features:
- Record tool executions with outcomes
- Track success rates per tool
- Learn which tools work best for which task types
- Suggest best tool for a given task description
- Persist usage history for cross-session learning
"""

from __future__ import annotations

import time
from collections import defaultdict

from pydantic import BaseModel


class ToolUsageRecord(BaseModel):
    """Record of a single tool execution."""

    tool_name: str
    task_description: str
    task_keywords: list[str] = []
    success: bool
    duration_ms: float = 0.0
    error_message: str | None = None
    input_summary: str = ""
    output_summary: str = ""
    timestamp: float = 0.0

    def __init__(self, **data):
        if "timestamp" not in data or data["timestamp"] == 0.0:
            data["timestamp"] = time.time()
        super().__init__(**data)


class ToolStats(BaseModel):
    """Aggregated statistics for a tool."""

    tool_name: str
    total_uses: int = 0
    successes: int = 0
    failures: int = 0
    total_duration_ms: float = 0.0
    last_used: float = 0.0
    task_keywords: dict[str, int] = {}

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        if self.total_uses == 0:
            return 0.0
        return self.successes / self.total_uses

    @property
    def avg_duration_ms(self) -> float:
        """Calculate average execution duration."""
        if self.total_uses == 0:
            return 0.0
        return self.total_duration_ms / self.total_uses


class ToolMemory:
    """
    Memory for tracking tool usage patterns and learning from history.

    Helps agents:
    - Know which tools have worked well in the past
    - Avoid tools that frequently fail
    - Select the best tool for a given task type
    - Learn from execution patterns over time

    Usage:
        tool_mem = ToolMemory(agent_id="agent-123")

        # Record usage
        tool_mem.record_usage(
            tool_name="web_search",
            task_description="Find information about Python",
            success=True,
            duration_ms=150.0
        )

        # Get stats
        stats = tool_mem.get_tool_stats("web_search")
        print(f"Success rate: {stats.success_rate:.1%}")

        # Get best tool for task
        best = tool_mem.get_best_tool_for("search the web for data")
        print(f"Recommended: {best}")
    """

    def __init__(self, agent_id: str, max_history: int = 1000):
        """
        Initialize tool memory.

        Args:
            agent_id: Owner agent ID for isolation
            max_history: Maximum number of usage records to keep
        """
        self.agent_id = agent_id
        self._max_history = max_history
        self._history: list[ToolUsageRecord] = []
        self._stats: dict[str, ToolStats] = {}
        self._keyword_tool_map: dict[str, dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )

    def record_usage(
        self,
        tool_name: str,
        task_description: str,
        success: bool,
        duration_ms: float = 0.0,
        error_message: str = None,
        input_summary: str = "",
        output_summary: str = "",
        task_keywords: list[str] = None,
    ) -> ToolUsageRecord:
        """
        Record a tool execution.

        Args:
            tool_name: Name of the tool used
            task_description: Description of the task
            success: Whether execution succeeded
            duration_ms: Execution time in milliseconds
            error_message: Error message if failed
            input_summary: Summary of input (for learning)
            output_summary: Summary of output (for learning)
            task_keywords: Keywords describing the task type

        Returns:
            The created usage record
        """
        keywords = task_keywords or self._extract_keywords(task_description)

        record = ToolUsageRecord(
            tool_name=tool_name,
            task_description=task_description,
            task_keywords=keywords,
            success=success,
            duration_ms=duration_ms,
            error_message=error_message,
            input_summary=input_summary,
            output_summary=output_summary,
        )

        self._history.append(record)

        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        self._update_stats(record)

        return record

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from task description."""
        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "dare",
            "ought",
            "used",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
            "and",
            "but",
            "or",
            "nor",
            "so",
            "yet",
            "both",
            "either",
            "neither",
            "not",
            "only",
            "own",
            "same",
            "than",
            "too",
            "very",
            "just",
            "i",
            "me",
            "my",
            "myself",
            "we",
            "our",
            "ours",
            "you",
            "your",
            "he",
            "him",
            "his",
            "she",
            "her",
            "it",
            "its",
            "they",
            "them",
            "their",
            "what",
            "which",
            "who",
            "whom",
            "this",
            "that",
            "these",
            "those",
            "am",
        }

        words = text.lower().split()
        keywords = [w.strip(".,!?;:'\"()[]{}") for w in words if len(w) > 2 and w not in stop_words]
        return keywords[:10]

    def _update_stats(self, record: ToolUsageRecord) -> None:
        """Update aggregated stats from a usage record."""
        tool_name = record.tool_name

        if tool_name not in self._stats:
            self._stats[tool_name] = ToolStats(tool_name=tool_name)

        stats = self._stats[tool_name]
        stats.total_uses += 1
        stats.total_duration_ms += record.duration_ms
        stats.last_used = record.timestamp

        if record.success:
            stats.successes += 1
        else:
            stats.failures += 1

        for keyword in record.task_keywords:
            stats.task_keywords[keyword] = stats.task_keywords.get(keyword, 0) + 1

            score = 1.0 if record.success else -0.5
            self._keyword_tool_map[keyword][tool_name] += score

    def get_tool_stats(self, tool_name: str) -> ToolStats | None:
        """Get aggregated statistics for a tool."""
        return self._stats.get(tool_name)

    def get_all_stats(self) -> dict[str, ToolStats]:
        """Get statistics for all tools."""
        return dict(self._stats)

    def get_success_rate(self, tool_name: str) -> float:
        """Get success rate for a tool (0.0 to 1.0)."""
        stats = self._stats.get(tool_name)
        return stats.success_rate if stats else 0.0

    def get_best_tool_for(
        self,
        task_description: str,
        available_tools: list[str] = None,
        min_uses: int = 1,
    ) -> str | None:
        """
        Get the best tool for a task based on historical performance.

        Args:
            task_description: Description of the task
            available_tools: List of available tool names (optional filter)
            min_uses: Minimum uses required to consider a tool

        Returns:
            Name of the best tool, or None if no suitable tool found
        """
        keywords = self._extract_keywords(task_description)

        tool_scores: dict[str, float] = defaultdict(float)

        for keyword in keywords:
            if keyword in self._keyword_tool_map:
                for tool_name, score in self._keyword_tool_map[keyword].items():
                    if available_tools is None or tool_name in available_tools:
                        stats = self._stats.get(tool_name)
                        if stats and stats.total_uses >= min_uses:
                            tool_scores[tool_name] += score * stats.success_rate

        if not tool_scores:
            if available_tools:
                best_available = None
                best_rate = -1.0
                for tool_name in available_tools:
                    stats = self._stats.get(tool_name)
                    if stats and stats.total_uses >= min_uses and stats.success_rate > best_rate:
                        best_rate = stats.success_rate
                        best_available = tool_name
                return best_available
            return None

        return max(tool_scores.keys(), key=lambda t: tool_scores[t])

    def get_tools_for_task_type(
        self, keywords: list[str], min_success_rate: float = 0.5
    ) -> list[tuple[str, float]]:
        """
        Get tools that have worked well for tasks with given keywords.

        Returns list of (tool_name, score) tuples sorted by score.
        """
        tool_scores: dict[str, float] = defaultdict(float)

        for keyword in keywords:
            if keyword in self._keyword_tool_map:
                for tool_name, score in self._keyword_tool_map[keyword].items():
                    stats = self._stats.get(tool_name)
                    if stats and stats.success_rate >= min_success_rate:
                        tool_scores[tool_name] += score

        sorted_tools = sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_tools

    def get_recent_failures(self, tool_name: str = None, limit: int = 10) -> list[ToolUsageRecord]:
        """Get recent failed executions for analysis."""
        failures = [r for r in self._history if not r.success]

        if tool_name:
            failures = [r for r in failures if r.tool_name == tool_name]

        return failures[-limit:]

    def get_history(
        self,
        tool_name: str = None,
        success_only: bool = False,
        limit: int = 100,
    ) -> list[ToolUsageRecord]:
        """Get usage history with optional filters."""
        history = self._history

        if tool_name:
            history = [r for r in history if r.tool_name == tool_name]

        if success_only:
            history = [r for r in history if r.success]

        return history[-limit:]

    def to_dict(self) -> dict:
        """Export tool memory to dictionary for persistence."""
        return {
            "agent_id": self.agent_id,
            "history": [r.model_dump() for r in self._history],
            "stats": {name: s.model_dump() for name, s in self._stats.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> ToolMemory:
        """Load tool memory from dictionary."""
        mem = cls(agent_id=data.get("agent_id", "unknown"))

        for record_data in data.get("history", []):
            record = ToolUsageRecord(**record_data)
            mem._history.append(record)
            mem._update_stats(record)

        return mem

    def clear(self) -> None:
        """Clear all usage history and stats."""
        self._history.clear()
        self._stats.clear()
        self._keyword_tool_map.clear()

    def get_summary(self) -> dict:
        """Get summary of tool memory state."""
        total_uses = sum(s.total_uses for s in self._stats.values())
        total_successes = sum(s.successes for s in self._stats.values())

        return {
            "agent_id": self.agent_id,
            "total_tools_tracked": len(self._stats),
            "total_executions": total_uses,
            "overall_success_rate": total_successes / max(total_uses, 1),
            "history_size": len(self._history),
            "top_tools": sorted(
                [(name, s.success_rate, s.total_uses) for name, s in self._stats.items()],
                key=lambda x: (x[1], x[2]),
                reverse=True,
            )[:5],
        }
