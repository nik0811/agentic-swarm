from abc import ABC, abstractmethod

from pydantic import BaseModel


class VectorSearchResult(BaseModel):
    id: str
    score: float
    payload: dict
    vector: list[float] | None = None


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
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict] = None,
    ) -> None:
        """Insert or update vectors."""
        pass

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        filters: dict = None,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors."""
        pass

    @abstractmethod
    async def delete(self, collection: str, ids: list[str]) -> None:
        """Delete vectors by ID."""
        pass

    @abstractmethod
    async def get(self, collection: str, ids: list[str]) -> list[dict]:
        """Get vectors by ID."""
        pass
