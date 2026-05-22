"""Redis-based storage backend for distributed deployments."""
import json
from typing import Any, Dict, List, Optional

from .base import BaseStorage


class RedisStorage(BaseStorage):
    """Redis storage backend. Requires `redis` package."""

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        prefix: str = "agentic_swarm:",
        **kwargs
    ):
        self._url = url
        self._prefix = prefix
        self._kwargs = kwargs
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import redis.asyncio as aioredis
                self._client = aioredis.from_url(self._url, **self._kwargs)
            except ImportError:
                raise ImportError("redis package not installed. Run: pip install redis")
        return self._client

    def _make_key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        client = self._get_client()
        data = await client.get(self._make_key(key))
        if data is None:
            return None
        return json.loads(data)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        client = self._get_client()
        data = json.dumps(value, default=str)
        if ttl:
            await client.setex(self._make_key(key), ttl, data)
        else:
            await client.set(self._make_key(key), data)

    async def delete(self, key: str) -> bool:
        client = self._get_client()
        result = await client.delete(self._make_key(key))
        return result > 0

    async def exists(self, key: str) -> bool:
        client = self._get_client()
        return await client.exists(self._make_key(key)) > 0

    async def list_keys(self, prefix: str = "") -> List[str]:
        client = self._get_client()
        pattern = f"{self._prefix}{prefix}*"
        keys = []
        async for key in client.scan_iter(match=pattern):
            clean_key = key.decode().removeprefix(self._prefix)
            keys.append(clean_key)
        return keys

    async def clear(self) -> None:
        client = self._get_client()
        pattern = f"{self._prefix}*"
        async for key in client.scan_iter(match=pattern):
            await client.delete(key)

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        client = self._get_client()
        full_keys = [self._make_key(k) for k in keys]
        values = await client.mget(full_keys)
        result = {}
        for key, val in zip(keys, values):
            if val is not None:
                result[key] = json.loads(val)
        return result

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
