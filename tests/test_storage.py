import pytest
import time
from unittest.mock import patch

from agentic_swarm.storage.local import LocalStorage


class TestLocalStorage:
    @pytest.fixture(autouse=True)
    def setup_storage(self, tmp_path):
        self.storage = LocalStorage(base_dir=str(tmp_path / "storage"))

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        await self.storage.set("key1", "value1")
        result = await self.storage.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        result = await self.storage.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_complex_value(self):
        data = {"name": "agent", "scores": [1, 2, 3]}
        await self.storage.set("complex", data)
        result = await self.storage.get("complex")
        assert result == data

    @pytest.mark.asyncio
    async def test_overwrite(self):
        await self.storage.set("key", "old")
        await self.storage.set("key", "new")
        result = await self.storage.get("key")
        assert result == "new"

    @pytest.mark.asyncio
    async def test_delete_existing(self):
        await self.storage.set("key", "value")
        deleted = await self.storage.delete("key")
        assert deleted is True
        result = await self.storage.get("key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        deleted = await self.storage.delete("ghost")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_exists_true(self):
        await self.storage.set("key", "val")
        assert await self.storage.exists("key") is True

    @pytest.mark.asyncio
    async def test_exists_false(self):
        assert await self.storage.exists("nope") is False

    @pytest.mark.asyncio
    async def test_list_keys_empty(self):
        keys = await self.storage.list_keys()
        assert keys == []

    @pytest.mark.asyncio
    async def test_list_keys(self):
        await self.storage.set("app:users:1", "u1")
        await self.storage.set("app:users:2", "u2")
        await self.storage.set("app:settings", "s")

        keys = await self.storage.list_keys()
        assert len(keys) == 3

    @pytest.mark.asyncio
    async def test_list_keys_with_prefix(self):
        await self.storage.set("app:users:1", "u1")
        await self.storage.set("app:users:2", "u2")
        await self.storage.set("app:settings", "s")

        keys = await self.storage.list_keys(prefix="app:users")
        assert len(keys) == 2
        assert all(k.startswith("app:users") for k in keys)

    @pytest.mark.asyncio
    async def test_clear(self):
        await self.storage.set("a", 1)
        await self.storage.set("b", 2)
        await self.storage.clear()
        keys = await self.storage.list_keys()
        assert keys == []

    @pytest.mark.asyncio
    async def test_ttl_not_expired(self):
        await self.storage.set("key", "val", ttl=3600)
        result = await self.storage.get("key")
        assert result == "val"

    @pytest.mark.asyncio
    async def test_ttl_expired(self):
        with patch("agentic_swarm.storage.local.time.time", return_value=1000.0):
            await self.storage.set("key", "val", ttl=10)

        with patch("agentic_swarm.storage.local.time.time", return_value=1020.0):
            result = await self.storage.get("key")
            assert result is None

    @pytest.mark.asyncio
    async def test_ttl_expired_exists_false(self):
        with patch("agentic_swarm.storage.local.time.time", return_value=1000.0):
            await self.storage.set("key", "val", ttl=5)

        with patch("agentic_swarm.storage.local.time.time", return_value=1010.0):
            assert await self.storage.exists("key") is False

    @pytest.mark.asyncio
    async def test_ttl_expired_not_in_list_keys(self):
        with patch("agentic_swarm.storage.local.time.time", return_value=1000.0):
            await self.storage.set("expired", "val", ttl=5)
            await self.storage.set("alive", "val", ttl=3600)

        with patch("agentic_swarm.storage.local.time.time", return_value=1010.0):
            keys = await self.storage.list_keys()
            assert "expired" not in keys
            assert "alive" in keys

    def test_key_to_path_slashes(self):
        path = self.storage._key_to_path("a/b/c")
        assert "__" in path.name
        assert "/" not in path.stem

    def test_key_to_path_colons(self):
        path = self.storage._key_to_path("ns:key:sub")
        assert ":" not in path.stem
