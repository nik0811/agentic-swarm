"""
Prompt/Token Caching for LLM calls.

Two caching strategies:
1. Response Cache: Cache full LLM responses by prompt hash (avoids duplicate API calls)
2. Prefix Cache: Track cacheable prefixes for providers that support native prompt caching
   (Anthropic cache_control, OpenAI automatic prefix caching, Bedrock prompt caching)
"""

import hashlib
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from collections import OrderedDict

from .base import LLMMessage, LLMResponse


@dataclass
class CacheEntry:
    """A cached LLM response."""
    response: LLMResponse
    created_at: float
    hit_count: int = 0
    token_cost_saved: int = 0


@dataclass
class CacheStats:
    """Statistics about cache usage."""
    hits: int = 0
    misses: int = 0
    total_tokens_saved: int = 0
    total_cost_saved: float = 0.0
    entries: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class PromptCache:
    """
    LLM response cache that avoids redundant API calls for identical prompts.
    
    Features:
    - Hash-based lookup (SHA-256 of messages + system prompt + model)
    - TTL expiration (configurable, default 1 hour)
    - LRU eviction when max size reached
    - Token savings tracking
    - Per-model cache isolation
    
    Usage:
        cache = PromptCache(max_size=1000, ttl=3600)
        
        # Check before calling LLM
        cached = cache.get(messages, system_prompt, model)
        if cached:
            return cached  # Free!
        
        # After LLM call, store result
        response = await provider.chat(messages)
        cache.put(messages, system_prompt, model, response, input_tokens=150)
    """

    def __init__(
        self,
        max_size: int = 500,
        ttl: int = 3600,
        enabled: bool = True,
    ):
        self.max_size = max_size
        self.ttl = ttl
        self.enabled = enabled
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats()

    def _compute_key(
        self,
        messages: List[LLMMessage],
        system_prompt: str = "",
        model: str = "",
        tools: List[dict] = None,
    ) -> str:
        """Compute a deterministic cache key from the prompt."""
        parts = [
            f"model:{model}",
            f"system:{system_prompt}",
        ]
        for msg in messages:
            parts.append(f"{msg.role}:{msg.content}")
        if tools:
            parts.append(f"tools:{len(tools)}")

        raw = "\n".join(parts)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(
        self,
        messages: List[LLMMessage],
        system_prompt: str = "",
        model: str = "",
        tools: List[dict] = None,
    ) -> Optional[LLMResponse]:
        """Look up a cached response. Returns None on miss."""
        if not self.enabled:
            return None

        key = self._compute_key(messages, system_prompt, model, tools)
        entry = self._cache.get(key)

        if entry is None:
            self._stats.misses += 1
            return None

        if time.time() - entry.created_at > self.ttl:
            del self._cache[key]
            self._stats.misses += 1
            return None

        entry.hit_count += 1
        self._stats.hits += 1
        self._cache.move_to_end(key)
        return entry.response

    def put(
        self,
        messages: List[LLMMessage],
        system_prompt: str,
        model: str,
        response: LLMResponse,
        tools: List[dict] = None,
        input_tokens: int = 0,
    ) -> None:
        """Store a response in cache."""
        if not self.enabled:
            return

        key = self._compute_key(messages, system_prompt, model, tools)

        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)

        self._cache[key] = CacheEntry(
            response=response,
            created_at=time.time(),
            token_cost_saved=input_tokens,
        )
        self._stats.entries = len(self._cache)

    def invalidate(
        self,
        messages: List[LLMMessage] = None,
        system_prompt: str = "",
        model: str = "",
    ) -> bool:
        """Invalidate a specific cache entry. Returns True if found."""
        if messages:
            key = self._compute_key(messages, system_prompt, model)
            if key in self._cache:
                del self._cache[key]
                self._stats.entries = len(self._cache)
                return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._stats.entries = 0

    @property
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self._stats = CacheStats(entries=len(self._cache))


class PrefixCache:
    """
    Tracks common prompt prefixes for provider-level caching.
    
    Many LLM providers (Anthropic, OpenAI, Bedrock) cache token prefixes
    server-side. This class helps identify and mark cacheable prefixes
    to maximize cache hits at the provider level.
    
    How it works:
    - Track system prompts and tool definitions that repeat across calls
    - Mark them with cache_control for providers that support it
    - Reorder messages to maximize prefix overlap between calls
    
    Supported providers:
    - Anthropic: Adds cache_control: {"type": "ephemeral"} to system message
    - OpenAI: Automatic (same prefix across requests gets cached)
    - Bedrock: Passes cache hints in request metadata
    """

    def __init__(self):
        self._prefix_registry: Dict[str, Dict[str, Any]] = {}
        self._hit_counts: Dict[str, int] = {}

    def register_prefix(self, prefix_id: str, content: str, token_count: int = 0) -> None:
        """Register a cacheable prefix (system prompt, tool defs, etc.)."""
        self._prefix_registry[prefix_id] = {
            "content": content,
            "tokens": token_count,
            "hash": hashlib.md5(content.encode()).hexdigest(),
        }
        self._hit_counts[prefix_id] = 0

    def mark_for_caching(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        provider: str = "anthropic",
    ) -> Dict[str, Any]:
        """
        Return cache hints for the provider.
        
        For Anthropic/Bedrock: returns cache_control markers
        For OpenAI: returns prefix ordering hints
        """
        hints = {
            "cache_control": None,
            "system_cache": False,
            "prefix_tokens": 0,
        }

        prefix_hash = hashlib.md5(system_prompt.encode()).hexdigest()

        if prefix_hash in [p["hash"] for p in self._prefix_registry.values()]:
            hints["system_cache"] = True
            self._hit_counts[prefix_hash] = self._hit_counts.get(prefix_hash, 0) + 1

        if provider in ("anthropic", "bedrock"):
            hints["cache_control"] = {"type": "ephemeral"}

        return hints

    def get_anthropic_system(self, system_prompt: str) -> List[dict]:
        """Format system prompt with Anthropic cache_control."""
        return [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def get_bedrock_cache_config(self, system_prompt: str) -> dict:
        """Format cache config for Bedrock's prompt caching."""
        return {
            "cachePoint": {"type": "default"},
            "text": system_prompt,
        }

    def estimate_savings(self, tokens_per_call: int, calls: int, provider: str = "anthropic") -> dict:
        """Estimate cost savings from prefix caching."""
        pricing = {
            "anthropic": {"write_per_1k": 0.00375, "read_per_1k": 0.0003, "base_per_1k": 0.003},
            "openai": {"cached_per_1k": 0.0000075, "base_per_1k": 0.000015},
            "bedrock": {"write_per_1k": 0.00375, "read_per_1k": 0.0003, "base_per_1k": 0.003},
        }

        rates = pricing.get(provider, pricing["anthropic"])

        if provider in ("anthropic", "bedrock"):
            base_cost = (tokens_per_call / 1000) * rates["base_per_1k"] * calls
            cached_cost = (
                (tokens_per_call / 1000) * rates["write_per_1k"] * 1 +
                (tokens_per_call / 1000) * rates["read_per_1k"] * (calls - 1)
            )
        else:
            base_cost = (tokens_per_call / 1000) * rates["base_per_1k"] * calls
            cached_cost = (
                (tokens_per_call / 1000) * rates["base_per_1k"] * 1 +
                (tokens_per_call / 1000) * rates["cached_per_1k"] * (calls - 1)
            )

        return {
            "base_cost": round(base_cost, 6),
            "cached_cost": round(cached_cost, 6),
            "savings": round(base_cost - cached_cost, 6),
            "savings_pct": round((1 - cached_cost / base_cost) * 100, 1) if base_cost > 0 else 0,
        }

    @property
    def registered_prefixes(self) -> int:
        return len(self._prefix_registry)
