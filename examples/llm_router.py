"""
Example: LLM Router with Multiple Providers

Demonstrates smart model routing with cost/speed/quality strategies,
multi-provider setup, and task-based model selection.
"""

import asyncio
from agentic_swarm.llm import LLMRouter
from agentic_swarm.llm.strategies import (
    CostOptimizedStrategy,
    SpeedOptimizedStrategy,
    QualityOptimizedStrategy,
)


def demonstrate_strategies():
    """Show how routing strategies rank models."""
    models = ["gpt-4o", "gpt-4o-mini", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
    model_info = {
        "gpt-4o": {"input_cost": 0.005, "output_cost": 0.015},
        "gpt-4o-mini": {"input_cost": 0.00015, "output_cost": 0.0006},
        "claude-3-opus-20240229": {"input_cost": 0.015, "output_cost": 0.075},
        "claude-3-haiku-20240307": {"input_cost": 0.00025, "output_cost": 0.00125},
    }

    print("=== Cost Optimized Strategy ===")
    cost = CostOptimizedStrategy()
    ranked = cost.rank_models(models, model_info)
    print(f"  Cheapest first: {ranked}")

    print("\n=== Speed Optimized Strategy ===")
    speed = SpeedOptimizedStrategy()
    ranked = speed.rank_models(models, model_info)
    print(f"  Fastest first: {ranked}")

    print("\n=== Quality Optimized Strategy ===")
    quality = QualityOptimizedStrategy()
    ranked = quality.rank_models(models, model_info)
    print(f"  Best quality first: {ranked}")


async def demonstrate_router():
    """Show router setup with multiple providers."""
    print("\n=== LLM Router Setup ===")

    router = LLMRouter(strategy="cost_optimized")
    print(f"  Strategy: {router.strategy}")
    print(f"  Router ready (register providers to use)")

    # In production you'd do:
    # from agentic_swarm.llm import OpenAIProvider, AnthropicProvider, GroqProvider
    # router.register_provider("openai", OpenAIProvider(model="gpt-4o"))
    # router.register_provider("anthropic", AnthropicProvider(model="claude-sonnet-4-20250514"))
    # router.register_provider("groq", GroqProvider(model="llama-3.3-70b-versatile"))
    #
    # response = await router.route("Hello!", system_prompt="Be helpful")
    # print(response.content)

    print("\n=== Custom Routing Rules ===")
    print("  TRIVIAL  → gpt-4o-mini (cheapest)")
    print("  MODERATE → gpt-4o (balanced)")
    print("  COMPLEX  → claude-sonnet-4-20250514 (capable)")
    print("  EXPERT   → claude-3-opus (most powerful)")


if __name__ == "__main__":
    demonstrate_strategies()
    asyncio.run(demonstrate_router())
