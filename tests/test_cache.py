"""Tests for LLM prompt/token caching."""

import pytest
import time
from unittest.mock import patch
from agentic_swarm.llm.cache import PromptCache, PrefixCache, CacheEntry
from agentic_swarm.llm.base import LLMMessage, LLMResponse


@pytest.fixture
def cache():
    return PromptCache(max_size=10, ttl=60, enabled=True)


@pytest.fixture
def messages():
    return [
        LLMMessage(role="system", content="You are helpful."),
        LLMMessage(role="user", content="Hello"),
    ]


@pytest.fixture
def response():
    return LLMResponse(
        content="Hi there!",
        model="gpt-4o-mini",
        finish_reason="stop",
        usage={"prompt_tokens": 10, "completion_tokens": 5},
    )


class TestPromptCache:
    def test_miss_on_empty(self, cache, messages):
        result = cache.get(messages, "system", "gpt-4o")
        assert result is None
        assert cache.stats.misses == 1

    def test_hit_after_put(self, cache, messages, response):
        cache.put(messages, "system", "gpt-4o", response)
        result = cache.get(messages, "system", "gpt-4o")
        assert result is not None
        assert result.content == "Hi there!"
        assert cache.stats.hits == 1

    def test_different_model_misses(self, cache, messages, response):
        cache.put(messages, "system", "gpt-4o", response)
        result = cache.get(messages, "system", "claude-3")
        assert result is None

    def test_different_system_prompt_misses(self, cache, messages, response):
        cache.put(messages, "system A", "gpt-4o", response)
        result = cache.get(messages, "system B", "gpt-4o")
        assert result is None

    def test_ttl_expiration(self, cache, messages, response):
        cache.put(messages, "sys", "model", response)

        with patch("agentic_swarm.llm.cache.time") as mock_time:
            mock_time.time.return_value = time.time() + 120
            result = cache.get(messages, "sys", "model")
            assert result is None

    def test_lru_eviction(self, messages, response):
        cache = PromptCache(max_size=3, ttl=60)
        for i in range(4):
            msgs = [LLMMessage(role="user", content=f"msg-{i}")]
            cache.put(msgs, "", "m", response)

        assert cache.stats.entries == 3
        first = cache.get([LLMMessage(role="user", content="msg-0")], "", "m")
        assert first is None

    def test_hit_rate(self, cache, messages, response):
        cache.put(messages, "s", "m", response)
        cache.get(messages, "s", "m")
        cache.get(messages, "s", "m")
        cache.get([LLMMessage(role="user", content="miss")], "s", "m")

        assert cache.stats.hits == 2
        assert cache.stats.misses == 1
        assert cache.stats.hit_rate == pytest.approx(2 / 3)

    def test_invalidate(self, cache, messages, response):
        cache.put(messages, "s", "m", response)
        assert cache.get(messages, "s", "m") is not None

        removed = cache.invalidate(messages, "s", "m")
        assert removed is True
        assert cache.get(messages, "s", "m") is None

    def test_clear(self, cache, messages, response):
        cache.put(messages, "s", "m", response)
        cache.clear()
        assert cache.stats.entries == 0
        assert cache.get(messages, "s", "m") is None

    def test_disabled_cache(self, messages, response):
        cache = PromptCache(enabled=False)
        cache.put(messages, "s", "m", response)
        result = cache.get(messages, "s", "m")
        assert result is None

    def test_reset_stats(self, cache, messages, response):
        cache.put(messages, "s", "m", response)
        cache.get(messages, "s", "m")
        cache.reset_stats()
        assert cache.stats.hits == 0
        assert cache.stats.misses == 0
        assert cache.stats.entries == 1

    def test_tools_affect_key(self, cache, messages, response):
        cache.put(messages, "s", "m", response, tools=[{"name": "search"}])
        result = cache.get(messages, "s", "m", tools=None)
        assert result is None


class TestPrefixCache:
    def test_register_prefix(self):
        pc = PrefixCache()
        pc.register_prefix("system", "You are a helpful assistant.", token_count=8)
        assert pc.registered_prefixes == 1

    def test_anthropic_system_format(self):
        pc = PrefixCache()
        result = pc.get_anthropic_system("Be helpful.")
        assert result[0]["type"] == "text"
        assert result[0]["text"] == "Be helpful."
        assert result[0]["cache_control"] == {"type": "ephemeral"}

    def test_bedrock_cache_config(self):
        pc = PrefixCache()
        result = pc.get_bedrock_cache_config("System prompt here")
        assert result["cachePoint"] == {"type": "default"}
        assert result["text"] == "System prompt here"

    def test_estimate_savings_anthropic(self):
        pc = PrefixCache()
        savings = pc.estimate_savings(tokens_per_call=2000, calls=100, provider="anthropic")
        assert savings["savings"] > 0
        assert savings["savings_pct"] > 50

    def test_estimate_savings_openai(self):
        pc = PrefixCache()
        savings = pc.estimate_savings(tokens_per_call=2000, calls=100, provider="openai")
        assert savings["savings"] > 0
        assert savings["savings_pct"] > 0

    def test_mark_for_caching(self):
        pc = PrefixCache()
        hints = pc.mark_for_caching(
            "system prompt",
            [LLMMessage(role="user", content="hi")],
            provider="anthropic",
        )
        assert hints["cache_control"] == {"type": "ephemeral"}


class TestRouterCacheIntegration:
    def test_router_has_cache(self):
        from agentic_swarm.llm import LLMRouter
        router = LLMRouter()
        assert router.cache is not None
        assert router.cache.enabled is True

    def test_router_cache_disabled(self):
        from agentic_swarm.llm import LLMRouter
        router = LLMRouter(cache_enabled=False)
        assert router.cache.enabled is False

    def test_router_cache_custom_size(self):
        from agentic_swarm.llm import LLMRouter
        router = LLMRouter(cache_max_size=100, cache_ttl=300)
        assert router.cache.max_size == 100
        assert router.cache.ttl == 300

    def test_router_stats_include_cache(self):
        from agentic_swarm.llm import LLMRouter
        router = LLMRouter()
        stats = router.get_usage_stats()
        assert "cache" in stats
        assert "hits" in stats["cache"]
        assert "hit_rate" in stats["cache"]

    def test_router_clear_resets_cache(self):
        from agentic_swarm.llm import LLMRouter
        router = LLMRouter()
        router.clear_stats()
        assert router.cache.stats.entries == 0
