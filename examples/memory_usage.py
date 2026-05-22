"""
Memory Usage Example

This example shows how to use the tiered memory system.
"""
import asyncio
from agentic_swarm import Agent
from agentic_swarm.memory import MemoryController
from agentic_swarm.vectordb import InMemoryVectorDB
from agentic_swarm.rag import MockEmbedder


async def main():
    vectordb = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=32)
    
    controller = MemoryController(
        agent_id="memory-demo-agent",
        name="MemoryBot",
        persona="You are an assistant with excellent memory.",
        capabilities=["remember", "recall", "search"],
        vectordb=vectordb,
        embedder=embedder,
    )
    
    print("=== Core Memory (Immutable Identity) ===")
    print(f"Name: {controller.core.name}")
    print(f"Persona: {controller.core.persona}")
    print(f"Capabilities: {controller.core.capabilities}")
    
    print("\n=== Recall Memory (Working Context) ===")
    controller.push_recall("Hello, I'm a user!", role="user")
    controller.push_recall("Hi! How can I help you?", role="assistant")
    controller.push_recall("Remember that I like Python.", role="user")
    controller.push_recall("Got it! You like Python.", role="assistant")
    
    print(f"Messages in recall: {controller.recall.size}")
    print("Recent messages:")
    for msg in controller.get_recall_messages():
        print(f"  [{msg['role']}]: {msg['content']}")
    
    print("\n=== Archival Memory (Long-term Storage) ===")
    memory_id = await controller.store_archival("User prefers Python over JavaScript")
    print(f"Stored memory with ID: {memory_id}")
    
    await controller.store_archival("User is working on an AI project")
    await controller.store_archival("User's favorite color is blue")
    
    results = await controller.search_archival("Python", limit=2)
    print(f"\nSearch results for 'Python':")
    for r in results:
        print(f"  - {r.content}")
    
    print("\n=== Memory Stats ===")
    stats = controller.get_stats()
    print(f"Core memory: {stats['core']}")
    print(f"Recall memory: {stats['recall']}")
    print(f"Archival enabled: {stats['archival']['enabled']}")


if __name__ == "__main__":
    asyncio.run(main())
