from abc import ABC, abstractmethod
from typing import Any, List, Optional
from pydantic import BaseModel


class VectorSearchResult(BaseModel):
    id: str
    score: float
    payload: dict
    vector: Optional[List[float]] = None


class BaseVectorDB(ABC):
    """Base interface for vector databases."""
    
    @abstractmethod
    async def create_collection(self, name: str, vector_size: int) -> None:
        """Create a new collection."""
        pass
    
    @abstractmethod
    async def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        pass
    
    @abstractmethod
    async def upsert(
        self,
        collection: str,
        ids: List[str],
        vectors: List[List[float]],
        payloads: List[dict] = None,
    ) -> None:
        """Insert or update vectors."""
        pass
    
    @abstractmethod
    async def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filters: dict = None,
    ) -> List[VectorSearchResult]:
        """Search for similar vectors."""
        pass
    
    @abstractmethod
    async def delete(self, collection: str, ids: List[str]) -> None:
        """Delete vectors by ID."""
        pass
    
    @abstractmethod
    async def get(self, collection: str, ids: List[str]) -> List[dict]:
        """Get vectors by ID."""
        pass
