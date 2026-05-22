"""Abstract base class for RAG data sources."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from pydantic import BaseModel


class Document(BaseModel):
    """A document retrieved from a source."""

    content: str
    source: str
    metadata: dict = {}


class BaseSource(ABC):
    """Interface for RAG data sources."""

    @abstractmethod
    async def load(self) -> list[Document]:
        """Load all documents from this source."""
        ...

    @abstractmethod
    async def load_lazy(self) -> AsyncIterator[Document]:
        """Lazily load documents one at a time."""
        ...

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return the type identifier for this source."""
        ...
