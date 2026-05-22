"""Cost-optimized routing strategy. Prefers cheapest models that can handle the task."""
from typing import List, Optional
from ..base import BaseLLMProvider


class CostOptimizedStrategy:
    """Select the cheapest model that meets minimum quality for the task complexity."""
    
    def select(self, providers: dict[str, BaseLLMProvider], complexity: str) -> Optional[str]:
        """Select cheapest provider/model pair."""
        if not providers:
            return None
        
        candidates = []
        for name, provider in providers.items():
            cost = provider.cost_per_1k_input + provider.cost_per_1k_output
            candidates.append((cost, provider.context_window, name, provider.model))
        
        candidates.sort(key=lambda x: x[0])
        
        if complexity in ("expert", "complex"):
            # For complex tasks, pick from top half by context window
            candidates.sort(key=lambda x: -x[1])
            candidates = candidates[:max(1, len(candidates)//2)]
            candidates.sort(key=lambda x: x[0])
        
        return candidates[0][3] if candidates else None
    
    def rank_models(self, models: List[str], model_info: dict) -> List[str]:
        """Rank models by cost (cheapest first)."""
        def cost_key(m):
            info = model_info.get(m, {})
            return info.get("input_cost", 999) + info.get("output_cost", 999)
        return sorted(models, key=cost_key)
