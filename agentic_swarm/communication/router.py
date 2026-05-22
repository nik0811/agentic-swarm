"""Message routing for directing messages between agents."""

from .bus import MessageBus
from .channel import Channel
from .protocols import Message


class MessageRouter:
    """Routes messages between agents using channels or the bus."""

    def __init__(self, bus: MessageBus | None = None):
        self._bus = bus or MessageBus()
        self._channels: dict[str, Channel] = {}
        self._routes: dict[str, str] = {}

    @property
    def bus(self) -> MessageBus:
        return self._bus

    def create_channel(self, agent_a_id: str, agent_b_id: str, buffer_size: int = 100) -> Channel:
        """Create a dedicated channel between two agents."""
        key = self._channel_key(agent_a_id, agent_b_id)
        if key not in self._channels:
            self._channels[key] = Channel(agent_a_id, agent_b_id, buffer_size)
        return self._channels[key]

    def get_channel(self, agent_a_id: str, agent_b_id: str) -> Channel | None:
        """Get existing channel between two agents."""
        key = self._channel_key(agent_a_id, agent_b_id)
        return self._channels.get(key)

    def close_channel(self, agent_a_id: str, agent_b_id: str) -> None:
        """Close and remove a channel."""
        key = self._channel_key(agent_a_id, agent_b_id)
        channel = self._channels.pop(key, None)
        if channel:
            channel.close()

    def set_route(self, from_agent: str, to_agent: str) -> None:
        """Set a default routing path from one agent to another."""
        self._routes[from_agent] = to_agent

    def get_route(self, from_agent: str) -> str | None:
        """Get the default route for an agent."""
        return self._routes.get(from_agent)

    async def send(self, message: Message) -> None:
        """Route a message to its destination."""
        if message.receiver_id:
            key = self._channel_key(message.sender_id, message.receiver_id)
            channel = self._channels.get(key)
            if channel and not channel.is_closed:
                await channel.send(message.sender_id, message.content, message.type)
                return

        await self._bus.publish(message)

    async def broadcast(self, sender_id: str, content, topic: str = "global") -> None:
        """Broadcast via the message bus."""
        await self._bus.broadcast(sender_id, content, topic)

    def list_channels(self) -> list[str]:
        """List all active channel keys."""
        return [k for k, ch in self._channels.items() if not ch.is_closed]

    def _channel_key(self, a: str, b: str) -> str:
        return f"{min(a, b)}:{max(a, b)}"

    def clear(self) -> None:
        """Close all channels and clear routes."""
        for channel in self._channels.values():
            channel.close()
        self._channels.clear()
        self._routes.clear()
        self._bus.clear()
