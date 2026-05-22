from typing import Literal

from ..core.exceptions import LLMProviderError
from ..core.types import TaskComplexity
from .base import BaseLLMProvider, LLMMessage, LLMResponse
from .cache import PrefixCache, PromptCache
from .classifier import TaskClassifier
from .context_compressor import ContextCompressor
from .token_manager import TokenManager

MODEL_ROUTING = {
    TaskComplexity.TRIVIAL: {
        "cost_optimized": ["gpt-3.5-turbo", "claude-3-haiku-20240307"],
        "speed_optimized": ["gpt-3.5-turbo", "gpt-4o-mini"],
        "quality_optimized": ["gpt-4o-mini", "claude-3-haiku-20240307"],
    },
    TaskComplexity.MODERATE: {
        "cost_optimized": ["gpt-4o-mini", "claude-3-haiku-20240307"],
        "speed_optimized": ["gpt-4o-mini", "gpt-4o"],
        "quality_optimized": ["gpt-4o", "claude-3-5-sonnet-latest"],
    },
    TaskComplexity.COMPLEX: {
        "cost_optimized": ["gpt-4o", "claude-3-5-sonnet-latest"],
        "speed_optimized": ["gpt-4o", "claude-3-5-sonnet-latest"],
        "quality_optimized": ["gpt-4o", "claude-3-5-sonnet-latest"],
    },
    TaskComplexity.EXPERT: {
        "cost_optimized": ["gpt-4o", "claude-3-opus-20240229"],
        "speed_optimized": ["gpt-4o", "claude-3-5-sonnet-latest"],
        "quality_optimized": ["claude-3-opus-20240229", "o1-preview"],
    },
}


class LLMRouter:
    """Smart router that selects optimal model based on task complexity."""

    def __init__(
        self,
        providers: dict[str, BaseLLMProvider] = None,
        strategy: Literal[
            "cost_optimized", "speed_optimized", "quality_optimized"
        ] = "cost_optimized",
        default_provider: str = "openai",
        model_routing: dict = None,
        cache_enabled: bool = True,
        cache_max_size: int = 500,
        cache_ttl: int = 3600,
    ):
        self.providers = providers or {}
        self.strategy = strategy
        self.default_provider = default_provider
        self.model_routing = model_routing or MODEL_ROUTING
        self.classifier = TaskClassifier()
        self.token_manager = TokenManager()
        self.compressor = ContextCompressor(self.token_manager)
        self.cache = PromptCache(
            max_size=cache_max_size,
            ttl=cache_ttl,
            enabled=cache_enabled,
        )
        self.prefix_cache = PrefixCache()

    def set_routing(self, routing: dict) -> None:
        """Override the model routing table.

        Example:
            router.set_routing({
                TaskComplexity.TRIVIAL: {
                    "cost_optimized": ["us.anthropic.claude-haiku-v1"],
                    "quality_optimized": ["us.anthropic.claude-opus-4-6-v1"],
                },
                TaskComplexity.EXPERT: {
                    "cost_optimized": ["us.anthropic.claude-opus-4-6-v1"],
                    "quality_optimized": ["us.anthropic.claude-opus-4-6-v1"],
                },
            })
        """
        self.model_routing = routing

    def update_routing(
        self, complexity: "TaskComplexity", strategy: str, models: list[str]
    ) -> None:
        """Update routing for a specific complexity+strategy combo.

        Example:
            router.update_routing(TaskComplexity.TRIVIAL, "cost_optimized", ["my-model-id"])
        """
        if complexity not in self.model_routing:
            self.model_routing[complexity] = {}
        self.model_routing[complexity][strategy] = models

    def register_provider(self, name: str, provider: BaseLLMProvider) -> None:
        """Register an LLM provider."""
        self.providers[name] = provider

    def _get_provider_for_model(self, model: str) -> BaseLLMProvider | None:
        """Get provider that supports the given model."""
        if "bedrock" in self.providers and (
            "anthropic." in model
            or "meta." in model
            or "amazon." in model
            or "mistral." in model
            or "us.anthropic" in model
            or "us.meta" in model
        ):
            return self.providers.get("bedrock")
        if "gpt" in model or "o1" in model:
            return self.providers.get("openai")
        elif "claude" in model and "anthropic" in self.providers:
            return self.providers.get("anthropic")

        # Fallback: if only one provider registered, use it
        if len(self.providers) == 1:
            return list(self.providers.values())[0]

        return None

    def _select_model(self, complexity: TaskComplexity) -> str:
        """Select model based on complexity and strategy."""
        models = self.model_routing.get(complexity, {}).get(self.strategy, [])

        for model in models:
            provider = self._get_provider_for_model(model)
            if provider:
                return model

        # Fallback: use the first registered provider's model
        if self.providers:
            first_provider = list(self.providers.values())[0]
            return first_provider.model

        return "gpt-4o-mini"

    async def route(
        self,
        task: str,
        messages: list[LLMMessage] = None,
        tools: list[dict] = None,
        system_prompt: str = None,
        force_model: str = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Route request to optimal model.

        1. Classify task complexity
        2. Select model based on complexity + strategy
        3. Compress context if needed
        4. Execute request with fallback on failure
        """
        complexity = self.classifier.classify(task)

        model = force_model or self._select_model(complexity)
        provider = self._get_provider_for_model(model)

        if not provider:
            raise LLMProviderError(f"No provider available for model: {model}")

        all_messages = []
        if system_prompt:
            all_messages.append(LLMMessage(role="system", content=system_prompt))
        if messages:
            all_messages.extend(messages)
        all_messages.append(LLMMessage(role="user", content=task))

        budget = self.token_manager.calculate_budget(
            provider.context_window,
            reserved_output=kwargs.get("max_tokens", 4096),
        )

        messages_dict = [m.model_dump() for m in all_messages]
        current_tokens = self.token_manager.count_messages_tokens(messages_dict)

        if current_tokens > budget:
            compressed = self.compressor.compress(messages_dict, budget)
            all_messages = [LLMMessage(**m) for m in compressed]

        # Check prompt cache before calling LLM
        cached_response = self.cache.get(all_messages, system_prompt or "", model, tools)
        if cached_response:
            return cached_response

        try:
            response = await provider.chat(all_messages, tools=tools, **kwargs)

            input_tokens = response.usage.get("prompt_tokens", 0)
            self.token_manager.track_usage(
                input_tokens,
                response.usage.get("completion_tokens", 0),
                response.model,
                provider.cost_per_1k_input,
                provider.cost_per_1k_output,
            )

            # Store in cache (only cache non-tool-call responses for safety)
            if not response.tool_calls:
                self.cache.put(
                    all_messages,
                    system_prompt or "",
                    model,
                    response,
                    tools=tools,
                    input_tokens=input_tokens,
                )

            return response

        except Exception as e:
            fallback_models = self.model_routing.get(complexity, {}).get(self.strategy, [])

            for fallback_model in fallback_models:
                if fallback_model == model:
                    continue

                fallback_provider = self._get_provider_for_model(fallback_model)
                if fallback_provider:
                    try:
                        return await fallback_provider.chat(all_messages, tools=tools, **kwargs)
                    except Exception:
                        continue

            raise e

    def get_usage_stats(self) -> dict:
        """Get token usage and cache statistics."""
        stats = self.token_manager.get_total_usage()
        cache_stats = self.cache.stats
        stats["cache"] = {
            "hits": cache_stats.hits,
            "misses": cache_stats.misses,
            "hit_rate": f"{cache_stats.hit_rate:.1%}",
            "entries": cache_stats.entries,
            "tokens_saved": cache_stats.total_tokens_saved,
        }
        return stats

    def clear_stats(self) -> None:
        """Clear usage statistics and cache."""
        self.token_manager.clear_history()
        self.classifier.clear_cache()
        self.cache.clear()
        self.cache.reset_stats()
