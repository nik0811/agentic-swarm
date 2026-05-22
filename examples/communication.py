"""
Example: Inter-Agent Communication

Demonstrates message bus (pub/sub) and direct channels between agents.
"""

import asyncio
from agentic_swarm.communication import MessageBus, MessageRouter, Message, MessageType, Channel


async def message_handler(message: Message):
    print(f"[{message.receiver_id}] Received from {message.sender_id}: {message.content}")


async def main():
    bus = MessageBus()

    bus.subscribe("researcher", message_handler)
    bus.subscribe("writer", message_handler)

    await bus.publish(Message(
        type=MessageType.TASK_DELEGATE,
        sender_id="coordinator",
        receiver_id="researcher",
        content="Research the latest developments in quantum computing",
    ))

    await bus.publish(Message(
        type=MessageType.TASK_RESULT,
        sender_id="researcher",
        receiver_id="writer",
        content="Quantum computing has made major breakthroughs in error correction...",
    ))

    await bus.broadcast(
        sender_id="coordinator",
        content="All tasks completed, shutting down",
        topic="system",
    )

    print("\n--- Direct Channel Communication ---")
    router = MessageRouter()
    channel = router.create_channel("agent-a", "agent-b")

    await channel.send("agent-a", "Can you help me with this analysis?")
    msg = await channel.receive("agent-b", timeout=1.0)
    print(f"agent-b received: {msg.content}")

    await channel.send("agent-b", "Sure, sending results now")
    msg = await channel.receive("agent-a", timeout=1.0)
    print(f"agent-a received: {msg.content}")

    print("\n--- Message History ---")
    history = bus.get_history(limit=5)
    for m in history:
        print(f"  [{m.type.value}] {m.sender_id} → {m.receiver_id}: {m.content[:50]}")


if __name__ == "__main__":
    asyncio.run(main())
