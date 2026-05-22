"""Point-to-point communication channels between agents."""

import asyncio
from collections import deque
from typing import Any

from ..core.exceptions import ChannelClosedError
from .protocols import Message, MessageType


class Channel:
    """Bidirectional communication channel between two agents."""

    def __init__(self, agent_a_id: str, agent_b_id: str, buffer_size: int = 100):
        self.agent_a_id = agent_a_id
        self.agent_b_id = agent_b_id
        self._queue_a: asyncio.Queue = asyncio.Queue(maxsize=buffer_size)
        self._queue_b: asyncio.Queue = asyncio.Queue(maxsize=buffer_size)
        self._closed = False
        self._history: deque = deque(maxlen=buffer_size * 2)

    @property
    def is_closed(self) -> bool:
        return self._closed

    async def send(
        self, sender_id: str, content: Any, msg_type: MessageType = MessageType.DIRECT
    ) -> None:
        """Send a message through the channel."""
        if self._closed:
            raise ChannelClosedError("Channel is closed")

        message = Message(
            type=msg_type,
            sender_id=sender_id,
            receiver_id=self.agent_b_id if sender_id == self.agent_a_id else self.agent_a_id,
            content=content,
        )
        self._history.append(message)

        if sender_id == self.agent_a_id:
            await self._queue_b.put(message)
        else:
            await self._queue_a.put(message)

    async def receive(self, agent_id: str, timeout: float | None = None) -> Message | None:
        """Receive a message from the channel."""
        if self._closed:
            return None

        queue = self._queue_a if agent_id == self.agent_a_id else self._queue_b
        try:
            if timeout:
                return await asyncio.wait_for(queue.get(), timeout=timeout)
            return await queue.get()
        except asyncio.TimeoutError:
            return None

    def pending_count(self, agent_id: str) -> int:
        """Number of unread messages for an agent."""
        queue = self._queue_a if agent_id == self.agent_a_id else self._queue_b
        return queue.qsize()

    def close(self) -> None:
        """Close the channel."""
        self._closed = True

    def get_history(self, limit: int = 50) -> list:
        """Get recent messages in this channel."""
        return list(self._history)[-limit:]
