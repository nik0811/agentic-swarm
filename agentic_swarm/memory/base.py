from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class MemoryEntry(BaseModel):
    key: str
    value: Any
    timestamp: float
    metadata: dict = {}


class BaseMemory(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass
