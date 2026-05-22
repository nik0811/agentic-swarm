import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from agentic_swarm.communication.protocols import Message, MessageType, Priority, Protocol
from agentic_swarm.communication.bus import MessageBus
from agentic_swarm.communication.channel import Channel
from agentic_swarm.communication.router import MessageRouter


class TestMessageType:
    def test_task_delegate_exists(self):
        assert MessageType.TASK_DELEGATE == "task_delegate"

    def test_task_result_exists(self):
        assert MessageType.TASK_RESULT == "task_result"

    def test_context_share_exists(self):
        assert MessageType.CONTEXT_SHARE == "context_share"

    def test_health_ping_exists(self):
        assert MessageType.HEALTH_PING == "health_ping"

    def test_spawn_request_exists(self):
        assert MessageType.SPAWN_REQUEST == "spawn_request"

    def test_standard_types(self):
        assert MessageType.TASK == "task"
        assert MessageType.RESULT == "result"
        assert MessageType.ERROR == "error"
        assert MessageType.STATUS == "status"
        assert MessageType.BROADCAST == "broadcast"
        assert MessageType.DIRECT == "direct"
        assert MessageType.HANDOFF == "handoff"


class TestMessage:
    def test_message_creation_defaults(self):
        msg = Message(sender_id="agent-1")
        assert msg.sender_id == "agent-1"
        assert msg.type == MessageType.DIRECT
        assert msg.priority == Priority.NORMAL
        assert msg.receiver_id is None
        assert msg.content is None
        assert msg.id is not None
        assert msg.timestamp is not None

    def test_message_creation_full(self):
        msg = Message(
            sender_id="agent-1",
            receiver_id="agent-2",
            type=MessageType.TASK,
            content={"action": "summarize"},
            priority=Priority.HIGH,
            metadata={"key": "val"},
            ttl=60,
        )
        assert msg.receiver_id == "agent-2"
        assert msg.type == MessageType.TASK
        assert msg.content == {"action": "summarize"}
        assert msg.priority == Priority.HIGH
        assert msg.metadata == {"key": "val"}
        assert msg.ttl == 60

    def test_message_unique_ids(self):
        msg1 = Message(sender_id="a")
        msg2 = Message(sender_id="a")
        assert msg1.id != msg2.id

    def test_priority_ordering(self):
        assert Priority.LOW < Priority.NORMAL < Priority.HIGH < Priority.CRITICAL


class TestProtocol:
    def test_protocol_values(self):
        assert Protocol.REQUEST_RESPONSE == "request_response"
        assert Protocol.PUBLISH_SUBSCRIBE == "publish_subscribe"
        assert Protocol.FIRE_AND_FORGET == "fire_and_forget"
        assert Protocol.STREAMING == "streaming"


class TestMessageBus:
    def setup_method(self):
        self.bus = MessageBus()

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        received = []

        def handler(msg):
            received.append(msg)

        self.bus.subscribe("agent-1", handler)

        msg = Message(sender_id="agent-2", receiver_id="agent-1", content="hello")
        await self.bus.publish(msg)

        assert len(received) == 1
        assert received[0].content == "hello"

    @pytest.mark.asyncio
    async def test_publish_no_subscriber(self):
        msg = Message(sender_id="agent-1", receiver_id="nonexistent", content="lost")
        await self.bus.publish(msg)

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        received = []

        def handler(msg):
            received.append(msg)

        self.bus.subscribe("agent-1", handler)
        self.bus.unsubscribe("agent-1")

        msg = Message(sender_id="agent-2", receiver_id="agent-1", content="test")
        await self.bus.publish(msg)
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_broadcast(self):
        received = []

        def handler(msg):
            received.append(msg)

        self.bus.subscribe_topic("global", handler)
        await self.bus.broadcast("sender-1", "broadcast msg", topic="global")

        assert len(received) == 1
        assert received[0].content == "broadcast msg"
        assert received[0].type == MessageType.BROADCAST

    @pytest.mark.asyncio
    async def test_topic_subscribe_unsubscribe(self):
        received = []

        def handler(msg):
            received.append(msg)

        self.bus.subscribe_topic("events", handler)
        self.bus.unsubscribe_topic("events", handler)

        await self.bus.broadcast("sender", "data", topic="events")
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_history(self):
        msg = Message(sender_id="a", receiver_id="b", content="test")
        await self.bus.publish(msg)

        history = self.bus.get_history()
        assert len(history) == 1
        assert history[0].content == "test"

    @pytest.mark.asyncio
    async def test_history_filter_by_agent(self):
        await self.bus.publish(Message(sender_id="a", receiver_id="b", content="1"))
        await self.bus.publish(Message(sender_id="c", receiver_id="d", content="2"))

        history = self.bus.get_history(agent_id="a")
        assert len(history) == 1
        assert history[0].content == "1"

    @pytest.mark.asyncio
    async def test_async_handler(self):
        received = []

        async def handler(msg):
            received.append(msg)

        self.bus.subscribe("agent-1", handler)
        msg = Message(sender_id="x", receiver_id="agent-1", content="async")
        await self.bus.publish(msg)
        assert len(received) == 1

    def test_clear(self):
        self.bus.subscribe("a", lambda m: None)
        self.bus.subscribe_topic("t", lambda m: None)
        self.bus._history.append(Message(sender_id="x"))
        self.bus.clear()
        assert len(self.bus._subscribers) == 0
        assert len(self.bus._topic_subscribers) == 0
        assert len(self.bus._history) == 0


class TestChannel:
    def setup_method(self):
        self.channel = Channel("agent-a", "agent-b")

    @pytest.mark.asyncio
    async def test_send_and_receive(self):
        await self.channel.send("agent-a", "hello from A")
        msg = await self.channel.receive("agent-b", timeout=1.0)

        assert msg is not None
        assert msg.content == "hello from A"
        assert msg.sender_id == "agent-a"
        assert msg.receiver_id == "agent-b"

    @pytest.mark.asyncio
    async def test_bidirectional(self):
        await self.channel.send("agent-a", "msg1")
        await self.channel.send("agent-b", "msg2")

        msg_for_b = await self.channel.receive("agent-b", timeout=1.0)
        msg_for_a = await self.channel.receive("agent-a", timeout=1.0)

        assert msg_for_b.content == "msg1"
        assert msg_for_a.content == "msg2"

    @pytest.mark.asyncio
    async def test_receive_timeout(self):
        msg = await self.channel.receive("agent-a", timeout=0.05)
        assert msg is None

    @pytest.mark.asyncio
    async def test_send_on_closed_channel(self):
        self.channel.close()
        with pytest.raises(RuntimeError, match="Channel is closed"):
            await self.channel.send("agent-a", "fail")

    @pytest.mark.asyncio
    async def test_receive_on_closed_channel(self):
        self.channel.close()
        msg = await self.channel.receive("agent-a")
        assert msg is None

    def test_is_closed(self):
        assert self.channel.is_closed is False
        self.channel.close()
        assert self.channel.is_closed is True

    @pytest.mark.asyncio
    async def test_pending_count(self):
        assert self.channel.pending_count("agent-b") == 0
        await self.channel.send("agent-a", "msg")
        assert self.channel.pending_count("agent-b") == 1

    @pytest.mark.asyncio
    async def test_history(self):
        await self.channel.send("agent-a", "one")
        await self.channel.send("agent-b", "two")
        history = self.channel.get_history()
        assert len(history) == 2


class TestMessageRouter:
    def setup_method(self):
        self.router = MessageRouter()

    def test_create_channel(self):
        channel = self.router.create_channel("a", "b")
        assert isinstance(channel, Channel)

    def test_create_channel_idempotent(self):
        ch1 = self.router.create_channel("a", "b")
        ch2 = self.router.create_channel("a", "b")
        assert ch1 is ch2

    def test_get_channel(self):
        self.router.create_channel("a", "b")
        ch = self.router.get_channel("a", "b")
        assert ch is not None
        ch_reverse = self.router.get_channel("b", "a")
        assert ch_reverse is ch

    def test_close_channel(self):
        self.router.create_channel("a", "b")
        self.router.close_channel("a", "b")
        ch = self.router.get_channel("a", "b")
        assert ch is None

    def test_set_and_get_route(self):
        self.router.set_route("a", "b")
        assert self.router.get_route("a") == "b"
        assert self.router.get_route("nonexistent") is None

    @pytest.mark.asyncio
    async def test_send_via_channel(self):
        ch = self.router.create_channel("a", "b")
        msg = Message(sender_id="a", receiver_id="b", content="routed")
        await self.router.send(msg)

        received = await ch.receive("b", timeout=1.0)
        assert received.content == "routed"

    @pytest.mark.asyncio
    async def test_send_via_bus_fallback(self):
        received = []

        def handler(msg):
            received.append(msg)

        self.router.bus.subscribe("b", handler)
        msg = Message(sender_id="a", receiver_id="b", content="bus-msg")
        await self.router.send(msg)
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_broadcast(self):
        received = []

        def handler(msg):
            received.append(msg)

        self.router.bus.subscribe_topic("global", handler)
        await self.router.broadcast("sender", "hi all")
        assert len(received) == 1

    def test_list_channels(self):
        self.router.create_channel("a", "b")
        self.router.create_channel("c", "d")
        assert len(self.router.list_channels()) == 2

    def test_clear(self):
        self.router.create_channel("a", "b")
        self.router.set_route("a", "b")
        self.router.clear()
        assert len(self.router.list_channels()) == 0
        assert self.router.get_route("a") is None
