"""Abstract base class for persistent storage backends."""

from abc import ABC, abstractmethod
from typing import Any


class BaseStorage(ABC):
    """Interface for agent state persistence."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Retrieve a value by key."""
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value with optional TTL in seconds."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True if key existed."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        ...

    @abstractmethod
    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys with optional prefix filter."""
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Delete all stored data."""
        ...

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Retrieve multiple values. Default implementation calls get() per key."""
        result = {}
        for key in keys:
            val = await self.get(key)
            if val is not None:
                result[key] = val
        return result

    async def set_many(self, items: dict[str, Any], ttl: int | None = None) -> None:
        """Store multiple values. Default implementation calls set() per item."""
        for key, value in items.items():
            await self.set(key, value, ttl=ttl)
