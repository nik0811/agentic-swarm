import time
from collections import deque
from typing import Any

from pydantic import BaseModel


class RecallEntry(BaseModel):
    content: Any
    role: str
    timestamp: float
    metadata: dict = {}
    token_count: int = 0


class RecallMemory:
    """
    Sliding window memory for working context.
    Auto-evicts oldest entries when max_size reached.
    """

    def __init__(self, max_size: int = 100, max_tokens: int = 8000):
        self._entries: deque[RecallEntry] = deque(maxlen=max_size)
        self._max_tokens = max_tokens
        self._current_tokens = 0

    def push(self, content: Any, role: str = "user", metadata: dict = None, token_count: int = 0):
        """Add entry to recall memory. Returns evicted entries if any."""
        entry = RecallEntry(
            content=content,
            role=role,
            timestamp=time.time(),
            metadata=metadata or {},
            token_count=token_count,
        )

        evicted = []
        while self._current_tokens + token_count > self._max_tokens and self._entries:
            removed = self._entries.popleft()
            self._current_tokens -= removed.token_count
            evicted.append(removed)

        if len(self._entries) == self._entries.maxlen:
            overflow = self._entries.popleft()
            self._current_tokens -= overflow.token_count
            evicted.append(overflow)

        self._entries.append(entry)
        self._current_tokens += token_count

        return evicted if evicted else None

    def get_recent(self, n: int = 10) -> list[RecallEntry]:
        """Get n most recent entries."""
        return list(self._entries)[-n:]

    def get_all(self) -> list[RecallEntry]:
        """Get all entries."""
        return list(self._entries)

    def search(self, query: str, limit: int = 5) -> list[RecallEntry]:
        """Simple keyword search in recall memory."""
        results = []
        query_lower = query.lower()
        for entry in reversed(list(self._entries)):
            content_str = str(entry.content).lower()
            if query_lower in content_str:
                results.append(entry)
                if len(results) >= limit:
                    break
        return results

    def to_messages(self) -> list[dict]:
        """Convert to LLM message format."""
        return [{"role": e.role, "content": str(e.content)} for e in self._entries]

    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()
        self._current_tokens = 0

    @property
    def size(self) -> int:
        return len(self._entries)

    @property
    def token_count(self) -> int:
        return self._current_tokens
