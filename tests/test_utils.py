import pytest
import json
from datetime import datetime

from agentic_swarm.utils.crypto import hash_string, generate_id, generate_token
from agentic_swarm.utils.serialization import serialize, deserialize, safe_serialize
from agentic_swarm.utils.validation import (
    validate_agent_name,
    validate_temperature,
    validate_max_tokens,
)


class TestCrypto:
    def test_hash_string_sha256(self):
        result = hash_string("hello")
        assert len(result) == 64
        assert result == hash_string("hello")

    def test_hash_string_different_inputs(self):
        assert hash_string("foo") != hash_string("bar")

    def test_hash_string_md5(self):
        result = hash_string("test", algorithm="md5")
        assert len(result) == 32

    def test_generate_id_no_prefix(self):
        uid = generate_id()
        assert len(uid) == 36
        assert "-" in uid

    def test_generate_id_with_prefix(self):
        uid = generate_id(prefix="agent-")
        assert uid.startswith("agent-")
        assert len(uid) > len("agent-")

    def test_generate_id_unique(self):
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100

    def test_generate_token_default_length(self):
        token = generate_token()
        assert len(token) == 64  # hex of 32 bytes

    def test_generate_token_custom_length(self):
        token = generate_token(length=16)
        assert len(token) == 32  # hex of 16 bytes

    def test_generate_token_unique(self):
        tokens = {generate_token() for _ in range(50)}
        assert len(tokens) == 50


class TestSerialization:
    def test_serialize_dict(self):
        data = {"key": "value", "num": 42}
        result = serialize(data)
        assert json.loads(result) == data

    def test_serialize_list(self):
        data = [1, 2, 3]
        result = serialize(data)
        assert json.loads(result) == data

    def test_serialize_datetime(self):
        dt = datetime(2024, 1, 15, 12, 0, 0)
        result = serialize({"ts": dt})
        parsed = json.loads(result)
        assert "2024-01-15" in parsed["ts"]

    def test_deserialize(self):
        data = '{"name": "agent", "active": true}'
        result = deserialize(data)
        assert result == {"name": "agent", "active": True}

    def test_serialize_deserialize_roundtrip(self):
        original = {"a": 1, "b": [2, 3], "c": "hello"}
        serialized = serialize(original)
        restored = deserialize(serialized)
        assert restored == original

    def test_safe_serialize_fallback(self):
        class Unserializable:
            def __repr__(self):
                return "Unserializable()"

        result = safe_serialize(Unserializable())
        assert "Unserializable" in result


class TestValidation:
    def test_validate_agent_name_valid(self):
        assert validate_agent_name("myAgent") is None
        assert validate_agent_name("agent-1") is None
        assert validate_agent_name("agent_name") is None
        assert validate_agent_name("A") is None

    def test_validate_agent_name_empty(self):
        err = validate_agent_name("")
        assert err is not None
        assert "empty" in err.lower()

    def test_validate_agent_name_too_long(self):
        err = validate_agent_name("a" * 65)
        assert err is not None
        assert "64" in err

    def test_validate_agent_name_invalid_start(self):
        err = validate_agent_name("1agent")
        assert err is not None
        assert "start with a letter" in err

    def test_validate_agent_name_invalid_chars(self):
        err = validate_agent_name("agent name")
        assert err is not None

        err = validate_agent_name("agent.name")
        assert err is not None

    def test_validate_temperature_valid(self):
        assert validate_temperature(0.0) is None
        assert validate_temperature(1.0) is None
        assert validate_temperature(2.0) is None
        assert validate_temperature(0.7) is None

    def test_validate_temperature_invalid(self):
        err = validate_temperature(-0.1)
        assert err is not None
        assert "between" in err.lower()

        err = validate_temperature(2.1)
        assert err is not None

    def test_validate_max_tokens_valid(self):
        assert validate_max_tokens(1) is None
        assert validate_max_tokens(4096) is None
        assert validate_max_tokens(1000000) is None

    def test_validate_max_tokens_too_low(self):
        err = validate_max_tokens(0)
        assert err is not None
        assert "at least 1" in err

    def test_validate_max_tokens_too_high(self):
        err = validate_max_tokens(1000001)
        assert err is not None
        assert "cannot exceed" in err.lower()
