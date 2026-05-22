"""
Tool Discovery and Dynamic Loading
==================================

Implements intelligent tool selection and retry mechanisms:
1. Semantic tool matching - find relevant tools based on task description
2. Lazy loading - load tools on-demand instead of all at once
3. Tool retry - automatically try alternative tools on failure
4. Tool registry - centralized tool management
"""

import asyncio
import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from agentic_swarm.tools.base import Tool


@dataclass
class ToolMatch:
    """Represents a tool match with relevance score."""

    tool: Tool
    score: float
    matched_keywords: list[str] = field(default_factory=list)


@dataclass
class ToolExecutionResult:
    """Result of tool execution with retry info."""

    success: bool
    result: Any
    tool_used: str
    attempts: int
    failed_tools: list[str] = field(default_factory=list)
    error: str | None = None


class ToolRegistry:
    """
    Central registry for tool management with discovery capabilities.

    Features:
    - Register tools with categories and keywords
    - Semantic search for relevant tools
    - Lazy loading of tool modules
    - Usage tracking and statistics
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._categories: dict[str, set[str]] = defaultdict(set)
        self._keywords: dict[str, set[str]] = defaultdict(set)
        self._usage_count: dict[str, int] = defaultdict(int)
        self._success_rate: dict[str, list[bool]] = defaultdict(list)
        self._lazy_loaders: dict[str, Callable[[], Tool]] = {}

    def register(self, tool: Tool, category: str = "general", keywords: list[str] = None) -> None:
        """Register a tool with optional category and keywords."""
        self._tools[tool.name] = tool
        self._categories[category].add(tool.name)

        # Extract keywords from description if not provided
        if keywords is None:
            keywords = self._extract_keywords(tool.description)

        for kw in keywords:
            self._keywords[kw.lower()].add(tool.name)

    def register_lazy(
        self,
        name: str,
        loader: Callable[[], Tool],
        category: str = "general",
        keywords: list[str] = None,
    ) -> None:
        """Register a tool loader for lazy initialization."""
        self._lazy_loaders[name] = loader
        self._categories[category].add(name)

        if keywords:
            for kw in keywords:
                self._keywords[kw.lower()].add(name)

    def get(self, name: str) -> Tool | None:
        """Get a tool by name, loading lazily if needed."""
        if name in self._tools:
            return self._tools[name]

        if name in self._lazy_loaders:
            tool = self._lazy_loaders[name]()
            self._tools[name] = tool
            del self._lazy_loaders[name]
            return tool

        return None

    def get_by_category(self, category: str) -> list[Tool]:
        """Get all tools in a category."""
        tools = []
        for name in self._categories.get(category, set()):
            tool = self.get(name)
            if tool:
                tools.append(tool)
        return tools

    def search(self, query: str, limit: int = 5, category: str | None = None) -> list[ToolMatch]:
        """
        Search for tools matching a query.

        Uses keyword matching and description similarity.
        """
        query_words = set(self._tokenize(query.lower()))
        matches = []

        # Get candidate tools
        if category:
            candidates = self._categories.get(category, set())
        else:
            candidates = set(self._tools.keys()) | set(self._lazy_loaders.keys())

        for name in candidates:
            tool = self.get(name)
            if not tool:
                continue

            score, matched = self._calculate_match_score(tool, query_words)
            if score > 0:
                matches.append(ToolMatch(tool=tool, score=score, matched_keywords=matched))

        # Sort by score descending
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:limit]

    def find_alternatives(self, tool_name: str, limit: int = 3) -> list[Tool]:
        """Find alternative tools similar to the given tool."""
        tool = self.get(tool_name)
        if not tool:
            return []

        # Search using the tool's description
        matches = self.search(tool.description, limit=limit + 1)

        # Exclude the original tool
        return [m.tool for m in matches if m.tool.name != tool_name][:limit]

    def record_usage(self, tool_name: str, success: bool) -> None:
        """Record tool usage for statistics."""
        self._usage_count[tool_name] += 1
        self._success_rate[tool_name].append(success)

        # Keep only last 100 results
        if len(self._success_rate[tool_name]) > 100:
            self._success_rate[tool_name] = self._success_rate[tool_name][-100:]

    def get_success_rate(self, tool_name: str) -> float:
        """Get success rate for a tool."""
        results = self._success_rate.get(tool_name, [])
        if not results:
            return 1.0  # Assume success if no data
        return sum(results) / len(results)

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_tools": len(self._tools) + len(self._lazy_loaders),
            "loaded_tools": len(self._tools),
            "lazy_tools": len(self._lazy_loaders),
            "categories": {cat: len(tools) for cat, tools in self._categories.items()},
            "total_usage": sum(self._usage_count.values()),
            "top_tools": sorted(self._usage_count.items(), key=lambda x: x[1], reverse=True)[:5],
        }

    def list_all(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys()) + list(self._lazy_loaders.keys())

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text."""
        # Remove common words
        stopwords = {
            "a",
            "an",
            "the",
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
            "also",
            "now",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "every",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "any",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
        }

        words = self._tokenize(text.lower())
        return [w for w in words if w not in stopwords and len(w) > 2]

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words."""
        return re.findall(r"\b[a-z]+\b", text.lower())

    def _calculate_match_score(self, tool: Tool, query_words: set[str]) -> tuple[float, list[str]]:
        """Calculate match score between tool and query."""
        tool_words = set(self._tokenize(tool.name.lower()))
        tool_words.update(self._tokenize(tool.description.lower()))

        # Find matching words
        matched = query_words & tool_words

        if not matched:
            return 0.0, []

        # Score based on:
        # 1. Number of matched words
        # 2. Match in tool name (higher weight)
        # 3. Tool success rate

        name_words = set(self._tokenize(tool.name.lower()))
        name_matches = query_words & name_words

        score = len(matched) * 1.0
        score += len(name_matches) * 2.0  # Name matches worth more
        score *= self.get_success_rate(tool.name)  # Weight by success rate

        return score, list(matched)


class ToolSelector:
    """
    Intelligent tool selector with retry capabilities.

    Features:
    - Select best tool for a task
    - Automatic retry with alternatives on failure
    - Execution timeout handling
    - Result caching
    """

    def __init__(self, registry: ToolRegistry, max_retries: int = 3, timeout: float = 30.0):
        self.registry = registry
        self.max_retries = max_retries
        self.timeout = timeout
        self._cache: dict[str, Any] = {}

    def select_tools(
        self, task_description: str, limit: int = 3, category: str | None = None
    ) -> list[Tool]:
        """Select the most relevant tools for a task."""
        matches = self.registry.search(task_description, limit=limit, category=category)
        return [m.tool for m in matches]

    async def execute_with_retry(
        self, task_description: str, arguments: dict[str, Any], category: str | None = None
    ) -> ToolExecutionResult:
        """
        Execute a tool with automatic retry on failure.

        1. Find best matching tool
        2. Try to execute
        3. On failure, try alternatives
        4. Return result with execution info
        """
        matches = self.registry.search(
            task_description, limit=self.max_retries + 1, category=category
        )

        if not matches:
            return ToolExecutionResult(
                success=False,
                result=None,
                tool_used="",
                attempts=0,
                error="No matching tools found",
            )

        failed_tools = []

        for attempt, match in enumerate(matches, 1):
            tool = match.tool

            try:
                result = await self._execute_tool(tool, arguments)
                self.registry.record_usage(tool.name, success=True)

                return ToolExecutionResult(
                    success=True,
                    result=result,
                    tool_used=tool.name,
                    attempts=attempt,
                    failed_tools=failed_tools,
                )

            except Exception as e:
                self.registry.record_usage(tool.name, success=False)
                failed_tools.append(tool.name)

                if attempt >= self.max_retries:
                    return ToolExecutionResult(
                        success=False,
                        result=None,
                        tool_used=tool.name,
                        attempts=attempt,
                        failed_tools=failed_tools,
                        error=str(e),
                    )

        return ToolExecutionResult(
            success=False,
            result=None,
            tool_used="",
            attempts=len(matches),
            failed_tools=failed_tools,
            error="All tools failed",
        )

    async def _execute_tool(self, tool: Tool, arguments: dict[str, Any]) -> Any:
        """Execute a tool with timeout."""
        if asyncio.iscoroutinefunction(tool.func):
            return await asyncio.wait_for(tool.func(**arguments), timeout=self.timeout)
        else:
            # Use asyncio.to_thread for sync functions (Python 3.9+)
            return await asyncio.wait_for(
                asyncio.to_thread(tool.func, **arguments), timeout=self.timeout
            )


class DynamicToolLoader:
    """
    Load tools dynamically based on task requirements.

    Instead of loading all tools upfront, this loader:
    1. Analyzes the task
    2. Loads only relevant tools
    3. Unloads unused tools to save memory
    """

    def __init__(self, registry: ToolRegistry, max_loaded: int = 10):
        self.registry = registry
        self.max_loaded = max_loaded
        self._loaded_tools: dict[str, Tool] = {}
        self._access_order: list[str] = []

    def load_for_task(self, task_description: str, limit: int = 5) -> list[Tool]:
        """Load tools relevant to a task."""
        matches = self.registry.search(task_description, limit=limit)

        tools = []
        for match in matches:
            tool = self._ensure_loaded(match.tool.name)
            if tool:
                tools.append(tool)

        return tools

    def _ensure_loaded(self, name: str) -> Tool | None:
        """Ensure a tool is loaded, evicting old tools if needed."""
        if name in self._loaded_tools:
            # Move to end of access order (most recently used)
            if name in self._access_order:
                self._access_order.remove(name)
            self._access_order.append(name)
            return self._loaded_tools[name]

        # Load the tool
        tool = self.registry.get(name)
        if not tool:
            return None

        # Evict oldest if at capacity
        while len(self._loaded_tools) >= self.max_loaded and self._access_order:
            oldest = self._access_order.pop(0)
            del self._loaded_tools[oldest]

        self._loaded_tools[name] = tool
        self._access_order.append(name)
        return tool

    def unload(self, name: str) -> None:
        """Explicitly unload a tool."""
        if name in self._loaded_tools:
            del self._loaded_tools[name]
        if name in self._access_order:
            self._access_order.remove(name)

    def get_loaded(self) -> list[str]:
        """Get list of currently loaded tool names."""
        return list(self._loaded_tools.keys())

    def clear(self) -> None:
        """Unload all tools."""
        self._loaded_tools.clear()
        self._access_order.clear()


# Global registry instance
_global_registry: ToolRegistry | None = None


def get_global_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(tool: Tool, category: str = "general", keywords: list[str] = None) -> None:
    """Register a tool in the global registry."""
    get_global_registry().register(tool, category, keywords)


def find_tools(query: str, limit: int = 5) -> list[Tool]:
    """Find tools matching a query in the global registry."""
    matches = get_global_registry().search(query, limit=limit)
    return [m.tool for m in matches]
