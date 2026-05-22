from typing import List, Optional
from pydantic import BaseModel
import uuid
import time

from ..vectordb.base import BaseVectorDB
from ..rag.embedder import Embedder


class ArchivalEntry(BaseModel):
    id: str
    content: str
    agent_id: str
    created_at: float
    metadata: dict = {}


class ArchivalMemory:
    """Long-term vector-indexed memory for agents."""
    
    def __init__(
        self,
        agent_id: str,
        vectordb: BaseVectorDB,
        embedder: Embedder = None,
        collection_prefix: str = "archival",
    ):
        self.agent_id = agent_id
        self.vectordb = vectordb
        self.embedder = embedder or Embedder()
        self.collection = f"{collection_prefix}_{agent_id}"
        self._initialized = False
    
    async def _ensure_collection(self):
        if not self._initialized:
            await self.vectordb.create_collection(
                self.collection,
                self.embedder.dimensions,
            )
            self._initialized = True
    
    async def store(self, content: str, metadata: dict = None) -> str:
        """Store content in archival memory."""
        await self._ensure_collection()
        
        memory_id = str(uuid.uuid4())
        
        vector = await self.embedder.embed(content)
        
        payload = {
            "content": content,
            "agent_id": self.agent_id,
            "created_at": time.time(),
            **(metadata or {}),
        }
        
        await self.vectordb.upsert(
            self.collection,
            ids=[memory_id],
            vectors=[vector],
            payloads=[payload],
        )
        
        return memory_id
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        filters: dict = None,
    ) -> List[ArchivalEntry]:
        """Search archival memory."""
        await self._ensure_collection()
        
        query_vector = await self.embedder.embed_query(query)
        
        search_filters = {"agent_id": self.agent_id}
        if filters:
            search_filters.update(filters)
        
        results = await self.vectordb.search(
            self.collection,
            query_vector,
            limit=limit,
            filters=search_filters,
        )
        
        return [
            ArchivalEntry(
                id=r.id,
                content=r.payload.get("content", ""),
                agent_id=r.payload.get("agent_id", self.agent_id),
                created_at=r.payload.get("created_at", 0),
                metadata={k: v for k, v in r.payload.items() 
                         if k not in ["content", "agent_id", "created_at"]},
            )
            for r in results
        ]
    
    async def delete(self, memory_id: str) -> None:
        """Delete a memory by ID."""
        await self._ensure_collection()
        await self.vectordb.delete(self.collection, [memory_id])
    
    async def list_all(self, limit: int = 100) -> List[ArchivalEntry]:
        """List all memories (expensive operation)."""
        await self._ensure_collection()
        
        dummy_vector = [0.0] * self.embedder.dimensions
        
        results = await self.vectordb.search(
            self.collection,
            dummy_vector,
            limit=limit,
            filters={"agent_id": self.agent_id},
        )
        
        return [
            ArchivalEntry(
                id=r.id,
                content=r.payload.get("content", ""),
                agent_id=r.payload.get("agent_id", self.agent_id),
                created_at=r.payload.get("created_at", 0),
                metadata={k: v for k, v in r.payload.items() 
                         if k not in ["content", "agent_id", "created_at"]},
            )
            for r in results
        ]
    
    async def clear(self) -> None:
        """Clear all archival memory for this agent."""
        try:
            await self.vectordb.delete_collection(self.collection)
            self._initialized = False
        except Exception:
            pass
