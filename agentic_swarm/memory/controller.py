from typing import List, Optional, Any

from .core_memory import CoreMemory
from .recall_memory import RecallMemory, RecallEntry
from .archival_memory import ArchivalMemory, ArchivalEntry
from ..vectordb.base import BaseVectorDB
from ..rag.embedder import Embedder


class MemoryController:
    """Unified interface for all memory types."""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        persona: str,
        capabilities: List[str] = None,
        vectordb: BaseVectorDB = None,
        embedder: Embedder = None,
        recall_max_size: int = 100,
        recall_max_tokens: int = 8000,
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
    
    @property
    def core(self) -> CoreMemory:
        """Access core memory (read-only identity)."""
        return self._core
    
    @property
    def recall(self) -> RecallMemory:
        """Access recall memory (working context)."""
        return self._recall
    
    @property
    def archival(self) -> Optional[ArchivalMemory]:
        """Access archival memory (long-term storage)."""
        return self._archival
    
    def push_recall(
        self,
        content: Any,
        role: str = "user",
        metadata: dict = None,
        token_count: int = 0,
    ) -> None:
        """Add entry to recall memory."""
        self._recall.push(content, role, metadata, token_count)
    
    def get_recall_messages(self) -> List[dict]:
        """Get recall memory as LLM messages."""
        return self._recall.to_messages()
    
    def search_recall(self, query: str, limit: int = 5) -> List[RecallEntry]:
        """Search recall memory."""
        return self._recall.search(query, limit)
    
    async def store_archival(self, content: str, metadata: dict = None) -> Optional[str]:
        """Store to archival memory."""
        if self._archival:
            return await self._archival.store(content, metadata)
        return None
    
    async def search_archival(self, query: str, limit: int = 5) -> List[ArchivalEntry]:
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
    
    def get_context_for_llm(self) -> dict:
        """Get formatted context for LLM."""
        return {
            "system_prompt": self._core.to_prompt(),
            "messages": self._recall.to_messages(),
        }
    
    def clear_recall(self) -> None:
        """Clear recall memory."""
        self._recall.clear()
    
    async def clear_archival(self) -> None:
        """Clear archival memory."""
        if self._archival:
            await self._archival.clear()
    
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
            },
        }
        return stats
