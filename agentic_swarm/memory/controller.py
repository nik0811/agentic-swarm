import re
from typing import Any

from ..rag.embedder import Embedder
from ..vectordb.base import BaseVectorDB
from .archival_memory import ArchivalEntry, ArchivalMemory
from .core_memory import CoreMemory
from .recall_memory import RecallEntry, RecallMemory


class MemoryController:
    """Unified interface for all memory types with auto-archiving and fact extraction.

    Implements the full memory architecture:
    - Core Memory: Immutable identity (always available)
    - Recall Memory: Working context (sliding window, auto-evicts oldest)
    - Archival Memory: Long-term vector-indexed storage (persistent)

    Features:
    - Auto-archive: When recall overflows, evicted entries are summarized and stored in archival
    - Fact extraction: Automatically extracts key facts from conversations
    - Deduplication: Prevents duplicate entries in archival memory
    - Context assembly: Builds optimized prompts respecting token budgets
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

    async def search_all(self, query: str, limit: int = 5) -> dict:
        """Search across all memory types."""
        results = {
            "recall": self.search_recall(query, limit),
            "archival": [],
        }

        if self._archival:
            results["archival"] = await self.search_archival(query, limit)

        return results

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
            "auto_archive": self._auto_archive,
            "auto_extract_facts": self._auto_extract_facts,
        }
        return stats
