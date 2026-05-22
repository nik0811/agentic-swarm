"""Local file-based storage backend using JSON files."""
import json
import os
import time
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base import BaseStorage


class LocalStorage(BaseStorage):
    """File-system based storage using JSON. Suitable for development and single-node deployments."""

    def __init__(self, base_dir: str = ".agentic_swarm/storage"):
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, dict] = {}

    def _key_to_path(self, key: str) -> Path:
        safe_key = key.replace("/", "__").replace(":", "_")
        return self._base_dir / f"{safe_key}.json"

    def _is_expired(self, entry: dict) -> bool:
        if entry.get("ttl") is None:
            return False
        return time.time() > entry["created_at"] + entry["ttl"]

    async def get(self, key: str) -> Optional[Any]:
        path = self._key_to_path(key)
        if not path.exists():
            return None
        
        with open(path, "r") as f:
            entry = json.load(f)
        
        if self._is_expired(entry):
            path.unlink(missing_ok=True)
            return None
        
        return entry["value"]

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        path = self._key_to_path(key)
        entry = {
            "key": key,
            "value": value,
            "ttl": ttl,
            "created_at": time.time(),
        }
        with open(path, "w") as f:
            json.dump(entry, f, default=str)

    async def delete(self, key: str) -> bool:
        path = self._key_to_path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    async def exists(self, key: str) -> bool:
        path = self._key_to_path(key)
        if not path.exists():
            return False
        with open(path, "r") as f:
            entry = json.load(f)
        return not self._is_expired(entry)

    async def list_keys(self, prefix: str = "") -> List[str]:
        keys = []
        for path in self._base_dir.glob("*.json"):
            with open(path, "r") as f:
                entry = json.load(f)
            if not self._is_expired(entry):
                key = entry["key"]
                if key.startswith(prefix):
                    keys.append(key)
        return keys

    async def clear(self) -> None:
        for path in self._base_dir.glob("*.json"):
            path.unlink()
