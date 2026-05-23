import re
from typing import Any

from ..rag.embedder import Embedder
from ..vectordb.base import BaseVectorDB
from .archival_memory import ArchivalEntry, ArchivalMemory
from .core_memory import CoreMemory
from .graph_memory import Entity, GraphMemory, Relationship
from .planning_memory import Goal, Plan, PlanningMemory, PlanTask, Priority
from .recall_memory import RecallEntry, RecallMemory
from .tool_memory import ToolMemory, ToolStats, ToolUsageRecord


class MemoryController:
    """Unified interface for all memory types with auto-archiving and fact extraction.

    Implements the full cognitive memory architecture:
    - Core Memory: Immutable identity (always available)
    - Recall Memory: Working context (sliding window, auto-evicts oldest)
    - Archival Memory: Long-term vector-indexed storage (persistent)
    - Graph Memory: Entity-relationship knowledge graph (optional)
    - Tool Memory: Tool usage patterns and learning (optional)
    - Planning Memory: Goals, plans, and task tracking (optional)

    Features:
    - Auto-archive: When recall overflows, evicted entries are summarized and stored in archival
    - Fact extraction: Automatically extracts key facts from conversations
    - Deduplication: Prevents duplicate entries in archival memory
    - Context assembly: Builds optimized prompts respecting token budgets
    - Knowledge graph: Store and query entity relationships
    - Tool learning: Track tool success/failure patterns
    - Planning: Manage goals, plans, and task decomposition
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        persona: str,
        capabilities: list[str] = None,
        vectordb: BaseVectorDB = None,
        embedder: Embedder = None,
        recall_max_size: int = 100,
        recall_max_tokens: int = 8000,
        auto_archive: bool = True,
        auto_extract_facts: bool = True,
        # New cognitive memory options
        enable_graph_memory: bool = False,
        enable_tool_memory: bool = False,
        enable_planning_memory: bool = False,
        tool_memory_max_history: int = 1000,
    ):
        self._core = CoreMemory(
            agent_id=agent_id,
            name=name,
            persona=persona,
            capabilities=capabilities or [],
        )

        self._recall = RecallMemory(
            max_size=recall_max_size,
            max_tokens=recall_max_tokens,
        )

        self._archival = None
        if vectordb:
            self._archival = ArchivalMemory(
                agent_id=agent_id,
                vectordb=vectordb,
                embedder=embedder,
            )

        self._auto_archive = auto_archive and self._archival is not None
        self._auto_extract_facts = auto_extract_facts
        self._archived_hashes: set = set()
        self._fact_buffer: list[str] = []

        # Initialize optional cognitive memories
        self._graph: GraphMemory | None = None
        if enable_graph_memory:
            self._graph = GraphMemory(agent_id=agent_id)

        self._tool_memory: ToolMemory | None = None
        if enable_tool_memory:
            self._tool_memory = ToolMemory(agent_id=agent_id, max_history=tool_memory_max_history)

        self._planning: PlanningMemory | None = None
        if enable_planning_memory:
            self._planning = PlanningMemory(agent_id=agent_id)

    @property
    def core(self) -> CoreMemory:
        """Access core memory (read-only identity)."""
        return self._core

    @property
    def recall(self) -> RecallMemory:
        """Access recall memory (working context)."""
        return self._recall

    @property
    def archival(self) -> ArchivalMemory | None:
        """Access archival memory (long-term storage)."""
        return self._archival

    @property
    def graph(self) -> GraphMemory | None:
        """Access graph memory (entity-relationship storage)."""
        return self._graph

    @property
    def tool_memory(self) -> ToolMemory | None:
        """Access tool memory (usage patterns)."""
        return self._tool_memory

    @property
    def planning(self) -> PlanningMemory | None:
        """Access planning memory (goals, plans, tasks)."""
        return self._planning

    def push_recall(
        self,
        content: Any,
        role: str = "user",
        metadata: dict = None,
        token_count: int = 0,
    ) -> None:
        """Add entry to recall memory. Auto-archives evicted entries."""
        evicted = self._recall.push(content, role, metadata, token_count)

        if self._auto_archive and evicted:
            self._handle_evicted(evicted)

        if self._auto_extract_facts and role in ("user", "assistant"):
            self._extract_facts_from(str(content))

    def _handle_evicted(self, evicted) -> None:
        """Archive evicted recall entries."""
        if evicted is None:
            return

        entries = evicted if isinstance(evicted, list) else [evicted]
        for entry in entries:
            content = str(entry.content) if hasattr(entry, "content") else str(entry)
            content_hash = hash(content[:200])
            if content_hash not in self._archived_hashes and len(content.strip()) > 20:
                self._archived_hashes.add(content_hash)
                self._fact_buffer.append(content)

    def _extract_facts_from(self, content: str) -> None:
        """Extract key facts from content for potential archival."""
        if len(content) < 30:
            return

        fact_patterns = [
            r"(?:remember|note|important|key point|takeaway)[:\s]+(.+)",
            r"(?:the answer is|conclusion|result)[:\s]+(.+)",
            r"(?:user prefers|user wants|user likes)[:\s]+(.+)",
        ]

        for pattern in fact_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                fact = match.strip()
                if len(fact) > 15:
                    self._fact_buffer.append(f"[Fact] {fact}")

    async def flush_to_archival(self) -> int:
        """Flush buffered facts/evictions to archival memory."""
        if not self._archival or not self._fact_buffer:
            return 0

        stored = 0
        for content in self._fact_buffer:
            existing = await self._archival.search(content[:100], limit=1)
            if existing and self._is_duplicate(content, existing[0].content):
                continue
            await self._archival.store(content)
            stored += 1

        self._fact_buffer.clear()
        return stored

    @staticmethod
    def _is_duplicate(new_content: str, existing_content: str, threshold: float = 0.85) -> bool:
        """Check if content is a near-duplicate using Jaccard similarity."""
        new_words = set(new_content.lower().split())
        existing_words = set(existing_content.lower().split())

        if not new_words or not existing_words:
            return False

        intersection = len(new_words & existing_words)
        union = len(new_words | existing_words)
        similarity = intersection / max(union, 1)
        return similarity >= threshold

    def get_recall_messages(self) -> list[dict]:
        """Get recall memory as LLM messages."""
        return self._recall.to_messages()

    def search_recall(self, query: str, limit: int = 5) -> list[RecallEntry]:
        """Search recall memory."""
        return self._recall.search(query, limit)

    async def store_archival(self, content: str, metadata: dict = None) -> str | None:
        """Store to archival memory with deduplication."""
        if not self._archival:
            return None

        existing = await self._archival.search(content[:100], limit=1)
        if existing and self._is_duplicate(content, existing[0].content):
            return None

        return await self._archival.store(content, metadata)

    async def search_archival(self, query: str, limit: int = 5) -> list[ArchivalEntry]:
        """Search archival memory."""
        if self._archival:
            return await self._archival.search(query, limit)
        return []

    def get_context_for_llm(self, max_tokens: int = None) -> dict:
        """Get formatted context for LLM respecting token budget.

        Priority order (per Architecture.md):
        1. Core memory (agent identity) — always included
        2. Current task / recent recall — always included
        3. Relevant archival results — included if space
        """
        system_prompt = self._core.to_prompt()
        messages = self._recall.to_messages()

        return {
            "system_prompt": system_prompt,
            "messages": messages,
            "fact_buffer_size": len(self._fact_buffer),
        }

    def clear_recall(self) -> None:
        """Clear recall memory."""
        self._recall.clear()

    async def clear_archival(self) -> None:
        """Clear archival memory."""
        if self._archival:
            await self._archival.clear()
        self._archived_hashes.clear()
        self._fact_buffer.clear()

    def get_stats(self) -> dict:
        """Get memory statistics."""
        stats = {
            "core": {
                "agent_id": self._core.agent_id,
                "name": self._core.name,
                "capabilities": len(self._core.capabilities),
            },
            "recall": {
                "size": self._recall.size,
                "token_count": self._recall.token_count,
            },
            "archival": {
                "enabled": self._archival is not None,
                "pending_archives": len(self._fact_buffer),
                "archived_hashes": len(self._archived_hashes),
            },
            "graph": {
                "enabled": self._graph is not None,
                "entities": self._graph.entity_count if self._graph else 0,
                "relationships": self._graph.relationship_count if self._graph else 0,
            },
            "tool_memory": {
                "enabled": self._tool_memory is not None,
                "tools_tracked": len(self._tool_memory._stats) if self._tool_memory else 0,
                "history_size": len(self._tool_memory._history) if self._tool_memory else 0,
            },
            "planning": {
                "enabled": self._planning is not None,
                "goals": len(self._planning._goals) if self._planning else 0,
                "plans": len(self._planning._plans) if self._planning else 0,
            },
            "auto_archive": self._auto_archive,
            "auto_extract_facts": self._auto_extract_facts,
        }
        return stats

    # ==================== Graph Memory Methods ====================

    def add_entity(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        properties: dict[str, Any] = None,
    ) -> Entity | None:
        """Add an entity to graph memory."""
        if not self._graph:
            return None
        return self._graph.add_entity(entity_id, entity_type, name, properties)

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: dict[str, Any] = None,
    ) -> Relationship | None:
        """Add a relationship between entities."""
        if not self._graph:
            return None
        return self._graph.add_relationship(source_id, target_id, rel_type, properties)

    def get_related_entities(
        self, entity_id: str, rel_type: str = None, direction: str = "outgoing"
    ) -> list[str]:
        """Get entities related to the given entity."""
        if not self._graph:
            return []
        return self._graph.get_related(entity_id, rel_type, direction)

    def find_entity_path(self, source_id: str, target_id: str) -> list[str] | None:
        """Find path between two entities."""
        if not self._graph:
            return None
        return self._graph.find_path(source_id, target_id)

    # ==================== Tool Memory Methods ====================

    def record_tool_usage(
        self,
        tool_name: str,
        task_description: str,
        success: bool,
        duration_ms: float = 0.0,
        error_message: str = None,
    ) -> ToolUsageRecord | None:
        """Record a tool execution."""
        if not self._tool_memory:
            return None
        return self._tool_memory.record_usage(
            tool_name=tool_name,
            task_description=task_description,
            success=success,
            duration_ms=duration_ms,
            error_message=error_message,
        )

    def get_best_tool(self, task_description: str, available_tools: list[str] = None) -> str | None:
        """Get the best tool for a task based on history."""
        if not self._tool_memory:
            return None
        return self._tool_memory.get_best_tool_for(task_description, available_tools)

    def get_tool_stats(self, tool_name: str) -> ToolStats | None:
        """Get statistics for a tool."""
        if not self._tool_memory:
            return None
        return self._tool_memory.get_tool_stats(tool_name)

    # ==================== Planning Memory Methods ====================

    def add_goal(
        self,
        description: str,
        priority: Priority = Priority.MEDIUM,
        success_criteria: list[str] = None,
    ) -> Goal | None:
        """Add a new goal."""
        if not self._planning:
            return None
        return self._planning.add_goal(
            description=description,
            priority=priority,
            success_criteria=success_criteria,
        )

    def create_plan(
        self,
        goal_id: str,
        description: str,
        tasks: list[dict[str, Any]],
    ) -> Plan | None:
        """Create a plan for a goal."""
        if not self._planning:
            return None
        return self._planning.create_plan(goal_id, description, tasks)

    def get_next_task(self, plan_id: str) -> PlanTask | None:
        """Get the next task to work on."""
        if not self._planning:
            return None
        return self._planning.get_next_task(plan_id)

    def complete_task(self, plan_id: str, task_id: str, result: Any = None) -> PlanTask | None:
        """Mark a task as completed."""
        if not self._planning:
            return None
        return self._planning.complete_task(plan_id, task_id, result)

    def get_active_goals(self) -> list[Goal]:
        """Get all active goals."""
        if not self._planning:
            return []
        return self._planning.get_active_goals()

    # ==================== Unified Search ====================

    async def search_all(self, query: str, limit: int = 5) -> dict:
        """Search across all memory types."""
        results = {
            "recall": self.search_recall(query, limit),
            "archival": [],
            "graph": [],
        }

        if self._archival:
            results["archival"] = await self.search_archival(query, limit)

        if self._graph:
            # Search entities by name/type containing query
            results["graph"] = self._graph.query(properties=None)[:limit]

        return results
