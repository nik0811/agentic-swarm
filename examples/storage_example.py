"""
Example: Persistent Storage

Demonstrates local file-based storage with TTL and key management.
"""

import asyncio
from pathlib import Path
from agentic_swarm.storage import LocalStorage


async def main():
    storage = LocalStorage(base_dir=".data/example_storage")

    print("--- Setting values ---")
    await storage.set("agent:config:researcher", {
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 4096,
    })
    await storage.set("agent:config:writer", {
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.9,
        "max_tokens": 8192,
    })
    await storage.set("session:token", "abc123xyz", ttl=3600)

    print("--- Getting values ---")
    config = await storage.get("agent:config:researcher")
    print(f"Researcher config: {config}")

    print("\n--- Listing keys ---")
    keys = await storage.list_keys(prefix="agent:")
    print(f"Agent keys: {keys}")

    all_keys = await storage.list_keys()
    print(f"All keys: {all_keys}")

    print("\n--- Checking existence ---")
    exists = await storage.exists("agent:config:researcher")
    print(f"Researcher exists: {exists}")

    missing = await storage.exists("agent:config:unknown")
    print(f"Unknown exists: {missing}")

    print("\n--- Deleting ---")
    await storage.delete("session:token")
    exists = await storage.exists("session:token")
    print(f"Token after delete: {exists}")

    print("\n--- Batch operations ---")
    await storage.set_many({
        "metric:latency": 42.5,
        "metric:tokens": 1500,
        "metric:cost": 0.003,
    })
    metrics = await storage.get_many(["metric:latency", "metric:tokens", "metric:cost"])
    print(f"Metrics: {metrics}")

    await storage.clear()
    print("\nStorage cleared.")


if __name__ == "__main__":
    asyncio.run(main())
