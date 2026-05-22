import pytest
from unittest.mock import AsyncMock, MagicMock
from agentic_swarm.llm.router import LLMRouter
from agentic_swarm.llm.base import LLMMessage, LLMResponse
from agentic_swarm.core.types import TaskComplexity


def test_router_creation():
    router = LLMRouter()
    assert router.strategy == "cost_optimized"
    assert router.providers == {}


def test_router_register_provider():
    router = LLMRouter()
    mock_provider = MagicMock()
    mock_provider.model = "gpt-4o-mini"
    
    router.register_provider("openai", mock_provider)
    assert "openai" in router.providers


def test_router_select_model_trivial():
    router = LLMRouter(strategy="cost_optimized")
    model = router._select_model(TaskComplexity.TRIVIAL)
    assert model in ["gpt-3.5-turbo", "claude-3-haiku-20240307", "gpt-4o-mini"]


def test_router_select_model_expert():
    router = LLMRouter(strategy="quality_optimized")
    model = router._select_model(TaskComplexity.EXPERT)
    assert model in ["claude-3-opus-20240229", "o1-preview", "gpt-4o-mini"]


@pytest.mark.asyncio
async def test_router_route():
    mock_provider = AsyncMock()
    mock_provider.model = "gpt-4o-mini"
    mock_provider.context_window = 128000
    mock_provider.cost_per_1k_input = 0.00015
    mock_provider.cost_per_1k_output = 0.0006
    mock_provider.chat.return_value = LLMResponse(
        content="Hello!",
        tool_calls=[],
        usage={"prompt_tokens": 10, "completion_tokens": 5},
        model="gpt-4o-mini",
        finish_reason="stop",
    )
    
    router = LLMRouter()
    router.register_provider("openai", mock_provider)
    
    response = await router.route("What is 2+2?")
    
    assert response.content == "Hello!"
    mock_provider.chat.assert_called_once()


def test_router_get_usage_stats():
    router = LLMRouter()
    router.token_manager.track_usage(100, 50, "gpt-4o-mini")
    
    stats = router.get_usage_stats()
    assert stats["prompt_tokens"] == 100
    assert stats["completion_tokens"] == 50


def test_router_clear_stats():
    router = LLMRouter()
    router.token_manager.track_usage(100, 50, "gpt-4o-mini")
    router.classifier.classify("test")
    
    router.clear_stats()
    
    assert router.get_usage_stats()["num_calls"] == 0
    assert len(router.classifier._cache) == 0
