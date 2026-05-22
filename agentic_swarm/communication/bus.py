"""Central message bus for agent communication."""

import asyncio
from collections import defaultdict
from collections.abc import Callable

from .protocols import Message, MessageType


class MessageBus:
    """Pub/sub message bus for decoupled agent communication."""

    def __init__(self, max_queue_size: int = 1000):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._topic_subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._running = False
        self._history: list[Message] = []
        self._max_history = 1000

    def subscribe(self, agent_id: str, handler: Callable) -> None:
        """Subscribe an agent to receive direct messages."""
        self._subscribers[agent_id].append(handler)

    def unsubscribe(self, agent_id: str) -> None:
        """Remove all subscriptions for an agent."""
        self._subscribers.pop(agent_id, None)

    def subscribe_topic(self, topic: str, handler: Callable) -> None:
        """Subscribe to a topic for broadcast messages."""
        self._topic_subscribers[topic].append(handler)

    def unsubscribe_topic(self, topic: str, handler: Callable) -> None:
        """Remove a handler from a topic."""
        if topic in self._topic_subscribers:
            self._topic_subscribers[topic] = [
                h for h in self._topic_subscribers[topic] if h != handler
            ]

    async def publish(self, message: Message) -> None:
        """Publish a message to the bus."""
        self._history.append(message)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        if message.receiver_id:
            handlers = self._subscribers.get(message.receiver_id, [])
            for handler in handlers:
                await self._invoke(handler, message)

        if message.type == MessageType.BROADCAST:
            for handlers in self._topic_subscribers.values():
                for handler in handlers:
                    await self._invoke(handler, message)

    async def _invoke(self, handler: Callable, message: Message) -> None:
        """Invoke a handler safely."""
        try:
            result = handler(message)
            if asyncio.iscoroutine(result):
                await result
        except Exception:
            pass

    async def broadcast(self, sender_id: str, content: any, topic: str = "global") -> None:
        """Broadcast a message to all topic subscribers."""
        msg = Message(
            type=MessageType.BROADCAST,
            sender_id=sender_id,
            content=content,
            metadata={"topic": topic},
        )
        await self.publish(msg)

    def get_history(self, agent_id: str | None = None, limit: int = 50) -> list[Message]:
        """Get message history, optionally filtered by agent."""
        if agent_id:
            filtered = [
                m for m in self._history if m.sender_id == agent_id or m.receiver_id == agent_id
            ]
            return filtered[-limit:]
        return self._history[-limit:]

    def clear(self) -> None:
        """Clear all subscriptions and history."""
        self._subscribers.clear()
        self._topic_subscribers.clear()
        self._history.clear()
