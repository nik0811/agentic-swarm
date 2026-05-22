from typing import List, Optional
from .token_manager import TokenManager
from ..core.config import get_config


class ContextCompressor:
    """Compress context to fit within token budget."""
    
    def __init__(self, token_manager: TokenManager = None, config: dict = None):
        self.token_manager = token_manager or TokenManager()
        
        cfg = get_config().compressor
        self.preserve_recent = cfg.preserve_recent
        self.summary_truncate_length = cfg.summary_truncate_length
        self.summary_safety_factor = cfg.summary_safety_factor
        self.min_fact_length = cfg.min_fact_length
        self.max_facts = cfg.max_facts
        self.relevance_threshold = cfg.relevance_threshold
        
        if config:
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
    
    def compress(
        self,
        messages: List[dict],
        budget: int,
        preserve_recent: int = None,
    ) -> List[dict]:
        """
        Compress messages to fit within budget.
        """
        preserve_recent = preserve_recent if preserve_recent is not None else self.preserve_recent
        
        if not messages:
            return []
        
        current_tokens = self.token_manager.count_messages_tokens(messages)
        
        if current_tokens <= budget:
            return messages
        
        recent = messages[-preserve_recent:] if len(messages) > preserve_recent else messages
        older = messages[:-preserve_recent] if len(messages) > preserve_recent else []
        
        recent_tokens = self.token_manager.count_messages_tokens(recent)
        
        if recent_tokens >= budget:
            return self._truncate_messages(recent, budget)
        
        remaining_budget = budget - recent_tokens
        
        if older:
            compressed_older = self._summarize_messages(older, remaining_budget)
            return compressed_older + recent
        
        return recent
    
    def _summarize_messages(self, messages: List[dict], budget: int) -> List[dict]:
        """Summarize older messages into a single context message."""
        if not messages:
            return []
        
        summary_parts = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if len(content) > self.summary_truncate_length:
                content = content[:self.summary_truncate_length] + "..."
            summary_parts.append(f"[{role}]: {content}")
        
        summary = "Previous context summary:\n" + "\n".join(summary_parts)
        
        summary_tokens = self.token_manager.count_tokens(summary)
        if summary_tokens > budget:
            ratio = budget / summary_tokens
            summary = summary[:int(len(summary) * ratio * self.summary_safety_factor)]
        
        return [{"role": "system", "content": summary}]
    
    def _truncate_messages(self, messages: List[dict], budget: int) -> List[dict]:
        """Truncate messages to fit budget, keeping most recent."""
        result = []
        current_tokens = 0
        
        for msg in reversed(messages):
            msg_tokens = self.token_manager.count_messages_tokens([msg])
            if current_tokens + msg_tokens <= budget:
                result.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
        
        return result
    
    def extract_key_facts(self, messages: List[dict]) -> List[str]:
        """Extract key facts from messages."""
        facts = []
        
        for msg in messages:
            content = msg.get("content", "")
            sentences = content.split(".")
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > self.min_fact_length and any(
                    keyword in sentence.lower()
                    for keyword in ["is", "are", "was", "were", "has", "have", "will", "should"]
                ):
                    facts.append(sentence)
        
        return facts[:self.max_facts]
    
    def filter_by_relevance(
        self,
        messages: List[dict],
        query: str,
        threshold: float = None,
    ) -> List[dict]:
        """Filter messages by relevance to query (simple keyword matching)."""
        threshold = threshold if threshold is not None else self.relevance_threshold
        query_words = set(query.lower().split())
        
        scored = []
        for msg in messages:
            content = msg.get("content", "").lower()
            content_words = set(content.split())
            
            if not content_words:
                continue
            
            overlap = len(query_words & content_words)
            score = overlap / len(query_words) if query_words else 0
            
            if score >= threshold:
                scored.append((score, msg))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [msg for _, msg in scored]
