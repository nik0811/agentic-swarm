"""
Example: Utility Functions

Demonstrates crypto, serialization, and validation utilities.
"""

from datetime import datetime, timezone
from agentic_swarm.utils import (
    hash_string, generate_id, generate_token,
    serialize, deserialize,
    validate_agent_name, validate_temperature, validate_max_tokens,
)


def demonstrate_crypto():
    """Hashing, ID generation, and secure tokens."""
    print("=== Crypto Utilities ===")

    digest = hash_string("sensitive data", algorithm="sha256")
    print(f"  SHA-256 hash: {digest[:40]}...")

    agent_id = generate_id(prefix="agent")
    print(f"  Generated ID: {agent_id}")

    token = generate_token(32)
    print(f"  Secure token: {token}")

    id1 = generate_id()
    id2 = generate_id()
    print(f"  IDs are unique: {id1 != id2}")


def demonstrate_serialization():
    """JSON serialization with datetime support."""
    print("\n=== Serialization ===")

    data = {
        "agent": "researcher",
        "created_at": datetime.now(timezone.utc),
        "config": {"temperature": 0.7, "max_tokens": 4096},
        "tags": ["ai", "research"],
    }

    json_str = serialize(data)
    print(f"  Serialized: {json_str[:80]}...")

    restored = deserialize(json_str)
    print(f"  Deserialized agent: {restored['agent']}")
    print(f"  Deserialized config: {restored['config']}")


def demonstrate_validation():
    """Input validation for agent parameters."""
    print("\n=== Validation ===")

    valid_names = ["my-agent", "researcher_v2", "agent123"]
    for name in valid_names:
        error = validate_agent_name(name)
        print(f"  '{name}' → {'valid' if not error else f'invalid: {error}'}")

    invalid_names = ["", "123start", "has spaces", "a" * 200]
    for name in invalid_names:
        error = validate_agent_name(name)
        print(f"  '{name[:20]}' → {'valid' if not error else f'invalid: {error}'}")

    print()
    for temp in [0.0, 0.7, 1.5, 2.0, 2.5]:
        error = validate_temperature(temp)
        print(f"  temperature={temp} → {'valid' if not error else f'invalid: {error}'}")

    print()
    for tokens in [1, 4096, 100_000, 0, 2_000_000]:
        error = validate_max_tokens(tokens)
        print(f"  max_tokens={tokens} → {'valid' if not error else f'invalid: {error}'}")


if __name__ == "__main__":
    demonstrate_crypto()
    demonstrate_serialization()
    demonstrate_validation()
