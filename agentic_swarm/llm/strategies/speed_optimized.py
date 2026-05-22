"""Speed-optimized routing strategy. Prefers fastest models (smaller context = faster inference)."""
from typing import List, Optional
from ..base import BaseLLMProvider


SPEED_TIERS = {
    "fastest": ["gpt-4o-mini", "llama-3.1-8b-instant", "gemini-2.0-flash-lite", "claude-3-haiku-20240307"],
    "fast": ["gpt-4o", "gemini-2.0-flash", "claude-3-5-sonnet-latest", "llama-3.3-70b-versatile"],
    "moderate": ["gpt-4-turbo", "gemini-1.5-pro", "claude-3-opus-20240229"],
}


class SpeedOptimizedStrategy:
    """Select the fastest model that meets minimum quality for the task."""
    
    def select(self, providers: dict[str, BaseLLMProvider], complexity: str) -> Optional[str]:
        """Select fastest available provider/model."""
        if not providers:
            return None
        
        available_models = {p.model for p in providers.values()}
        
        if complexity in ("trivial", "moderate"):
            tier_order = ["fastest", "fast", "moderate"]
        else:
            tier_order = ["fast", "moderate", "fastest"]
        
        for tier in tier_order:
            for model in SPEED_TIERS.get(tier, []):
                if model in available_models:
                    return model
        
        return list(providers.values())[0].model
    
    def rank_models(self, models: List[str], model_info: dict) -> List[str]:
        """Rank models by speed (fastest first based on known tiers)."""
        speed_order = SPEED_TIERS.get("fastest", []) + SPEED_TIERS.get("fast", []) + SPEED_TIERS.get("moderate", [])
        
        def speed_key(m):
            try:
                return speed_order.index(m)
            except ValueError:
                return len(speed_order)
        
        return sorted(models, key=speed_key)
