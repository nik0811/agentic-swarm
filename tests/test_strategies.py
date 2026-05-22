import pytest
from unittest.mock import MagicMock, PropertyMock

from agentic_swarm.llm.strategies.cost_optimized import CostOptimizedStrategy
from agentic_swarm.llm.strategies.speed_optimized import SpeedOptimizedStrategy, SPEED_TIERS
from agentic_swarm.llm.strategies.quality_optimized import QualityOptimizedStrategy, QUALITY_TIERS


def _make_provider(model: str, cost_in: float, cost_out: float, ctx: int):
    p = MagicMock()
    p.model = model
    type(p).cost_per_1k_input = PropertyMock(return_value=cost_in)
    type(p).cost_per_1k_output = PropertyMock(return_value=cost_out)
    type(p).context_window = PropertyMock(return_value=ctx)
    return p


class TestCostOptimizedStrategy:
    def setup_method(self):
        self.strategy = CostOptimizedStrategy()

    def test_rank_models_cheapest_first(self):
        models = ["expensive", "cheap", "mid"]
        model_info = {
            "expensive": {"input_cost": 10.0, "output_cost": 10.0},
            "cheap": {"input_cost": 0.1, "output_cost": 0.1},
            "mid": {"input_cost": 1.0, "output_cost": 1.0},
        }
        ranked = self.strategy.rank_models(models, model_info)
        assert ranked[0] == "cheap"
        assert ranked[1] == "mid"
        assert ranked[2] == "expensive"

    def test_rank_models_unknown_goes_last(self):
        models = ["known", "unknown"]
        model_info = {"known": {"input_cost": 1.0, "output_cost": 1.0}}
        ranked = self.strategy.rank_models(models, model_info)
        assert ranked[0] == "known"
        assert ranked[1] == "unknown"

    def test_select_cheapest(self):
        providers = {
            "p1": _make_provider("model-a", 5.0, 5.0, 8000),
            "p2": _make_provider("model-b", 0.5, 0.5, 4000),
        }
        result = self.strategy.select(providers, complexity="trivial")
        assert result == "model-b"

    def test_select_empty_providers(self):
        result = self.strategy.select({}, complexity="trivial")
        assert result is None

    def test_select_complex_considers_context(self):
        providers = {
            "p1": _make_provider("cheap-small", 0.1, 0.1, 4000),
            "p2": _make_provider("mid-large", 1.0, 1.0, 128000),
            "p3": _make_provider("expensive-large", 5.0, 5.0, 200000),
        }
        result = self.strategy.select(providers, complexity="expert")
        assert result is not None


class TestSpeedOptimizedStrategy:
    def setup_method(self):
        self.strategy = SpeedOptimizedStrategy()

    def test_rank_models_fastest_first(self):
        models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
        ranked = self.strategy.rank_models(models, {})
        assert ranked[0] == "gpt-4o-mini"
        assert ranked.index("gpt-4o") < ranked.index("gpt-4-turbo")

    def test_rank_models_unknown_goes_last(self):
        models = ["gpt-4o-mini", "custom-model"]
        ranked = self.strategy.rank_models(models, {})
        assert ranked[0] == "gpt-4o-mini"
        assert ranked[-1] == "custom-model"

    def test_select_trivial_picks_fastest(self):
        providers = {
            "p1": _make_provider("gpt-4o-mini", 0.1, 0.1, 128000),
            "p2": _make_provider("gpt-4-turbo", 5.0, 5.0, 128000),
        }
        result = self.strategy.select(providers, complexity="trivial")
        assert result == "gpt-4o-mini"

    def test_select_expert_avoids_fastest_tier_first(self):
        providers = {
            "p1": _make_provider("gpt-4o-mini", 0.1, 0.1, 128000),
            "p2": _make_provider("gpt-4o", 2.0, 2.0, 128000),
        }
        result = self.strategy.select(providers, complexity="expert")
        assert result == "gpt-4o"

    def test_select_empty_providers(self):
        result = self.strategy.select({}, complexity="moderate")
        assert result is None


class TestQualityOptimizedStrategy:
    def setup_method(self):
        self.strategy = QualityOptimizedStrategy()

    def test_rank_models_best_first(self):
        models = ["gpt-4o-mini", "claude-3-opus-20240229", "gpt-4o"]
        ranked = self.strategy.rank_models(models, {})
        assert ranked[0] == "claude-3-opus-20240229"
        assert ranked[1] == "gpt-4o"
        assert ranked[2] == "gpt-4o-mini"

    def test_rank_models_unknown_goes_last(self):
        models = ["gpt-4o", "my-custom-model"]
        ranked = self.strategy.rank_models(models, {})
        assert ranked[-1] == "my-custom-model"

    def test_select_expert_picks_best(self):
        providers = {
            "p1": _make_provider("gpt-4o-mini", 0.1, 0.1, 128000),
            "p2": _make_provider("claude-3-opus-20240229", 15.0, 15.0, 200000),
        }
        result = self.strategy.select(providers, complexity="expert")
        assert result == "claude-3-opus-20240229"

    def test_select_trivial_picks_good_tier(self):
        providers = {
            "p1": _make_provider("gpt-4o-mini", 0.1, 0.1, 128000),
            "p2": _make_provider("claude-3-opus-20240229", 15.0, 15.0, 200000),
        }
        result = self.strategy.select(providers, complexity="trivial")
        assert result == "gpt-4o-mini"

    def test_select_empty_providers(self):
        result = self.strategy.select({}, complexity="expert")
        assert result is None
