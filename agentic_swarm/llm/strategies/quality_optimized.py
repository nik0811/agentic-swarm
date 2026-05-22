"""Quality-optimized routing strategy. Prefers most capable models regardless of cost."""
from typing import List, Optional
from ..base import BaseLLMProvider


QUALITY_TIERS = {
    "best": ["claude-3-opus-20240229", "gpt-4o", "gemini-1.5-pro", "us.anthropic.claude-opus-4-6-v1"],
    "high": ["claude-3-5-sonnet-latest", "gpt-4-turbo", "gemini-2.0-flash", "llama-3.3-70b-versatile"],
    "good": ["gpt-4o-mini", "gemini-2.0-flash-lite", "llama-3.1-8b-instant", "claude-3-haiku-20240307"],
}


class QualityOptimizedStrategy:
    """Select the highest quality model available."""
    
    def select(self, providers: dict[str, BaseLLMProvider], complexity: str) -> Optional[str]:
        """Select highest quality provider/model."""
        if not providers:
            return None
        
        available_models = {p.model for p in providers.values()}
        
        if complexity in ("expert", "complex"):
            tier_order = ["best", "high", "good"]
        elif complexity == "moderate":
            tier_order = ["high", "best", "good"]
        else:
            tier_order = ["good", "high", "best"]
        
        for tier in tier_order:
            for model in QUALITY_TIERS.get(tier, []):
                if model in available_models:
                    return model
        
        return list(providers.values())[0].model
    
    def rank_models(self, models: List[str], model_info: dict) -> List[str]:
        """Rank models by quality (best first)."""
        quality_order = QUALITY_TIERS.get("best", []) + QUALITY_TIERS.get("high", []) + QUALITY_TIERS.get("good", [])
        
        def quality_key(m):
            try:
                return quality_order.index(m)
            except ValueError:
                return len(quality_order)
        
        return sorted(models, key=quality_key)
