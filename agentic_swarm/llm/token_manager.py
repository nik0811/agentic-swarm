from typing import Optional
from ..core.config import get_config


class TokenManager:
    """Manage token budgets and counting."""
    
    def __init__(self, encoding_name: str = None):
        cfg = get_config().llm
        self._encoding = None
        self._encoding_name = encoding_name or cfg.token_encoding
        self._tokens_per_message = cfg.tokens_per_message_overhead
        self._tokens_per_request = cfg.tokens_per_request_overhead
        self._usage_history: list[dict] = []
    
    def _get_encoding(self):
        if self._encoding is None:
            try:
                import tiktoken
                self._encoding = tiktoken.get_encoding(self._encoding_name)
            except ImportError:
                raise ImportError("tiktoken package not installed. Run: pip install tiktoken")
        return self._encoding
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        encoding = self._get_encoding()
        return len(encoding.encode(text))
    
    def count_messages_tokens(self, messages: list[dict]) -> int:
        """Count tokens in a list of messages."""
        total = 0
        for msg in messages:
            total += self._tokens_per_message
            for key, value in msg.items():
                total += self.count_tokens(str(value))
        total += self._tokens_per_request
        return total
    
    def calculate_budget(
        self,
        model_context_limit: int,
        reserved_output: int = None,
        system_prompt_tokens: int = None,
    ) -> int:
        """Calculate available token budget for context."""
        cfg = get_config().llm
        reserved_output = reserved_output if reserved_output is not None else cfg.reserved_output_tokens
        system_prompt_tokens = system_prompt_tokens if system_prompt_tokens is not None else cfg.system_prompt_tokens
        return model_context_limit - reserved_output - system_prompt_tokens
    
    def allocate_budget(
        self,
        total_budget: int,
        core_memory: str,
        task: str,
        tools: list[dict] = None,
        recall_messages: list[dict] = None,
    ) -> dict:
        """Allocate budget across components."""
        allocation = {
            "core_memory": 0,
            "task": 0,
            "tools": 0,
            "recall": 0,
            "remaining": total_budget,
        }
        
        core_tokens = self.count_tokens(core_memory)
        allocation["core_memory"] = core_tokens
        allocation["remaining"] -= core_tokens
        
        task_tokens = self.count_tokens(task)
        allocation["task"] = task_tokens
        allocation["remaining"] -= task_tokens
        
        if tools:
            import json
            tools_str = json.dumps(tools)
            tools_tokens = self.count_tokens(tools_str)
            allocation["tools"] = tools_tokens
            allocation["remaining"] -= tools_tokens
        
        if recall_messages and allocation["remaining"] > 0:
            recall_tokens = self.count_messages_tokens(recall_messages)
            allocation["recall"] = min(recall_tokens, allocation["remaining"])
            allocation["remaining"] -= allocation["recall"]
        
        return allocation
    
    def track_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        cost_per_1k_input: float = 0,
        cost_per_1k_output: float = 0,
    ) -> dict:
        """Track token usage and cost."""
        cost = (prompt_tokens / 1000 * cost_per_1k_input) + \
               (completion_tokens / 1000 * cost_per_1k_output)
        
        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "model": model,
            "cost": cost,
        }
        
        self._usage_history.append(usage)
        return usage
    
    def get_total_usage(self) -> dict:
        """Get total usage across all tracked calls."""
        total = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0,
            "num_calls": len(self._usage_history),
        }
        
        for usage in self._usage_history:
            total["prompt_tokens"] += usage["prompt_tokens"]
            total["completion_tokens"] += usage["completion_tokens"]
            total["total_tokens"] += usage["total_tokens"]
            total["total_cost"] += usage["cost"]
        
        return total
    
    def clear_history(self):
        """Clear usage history."""
        self._usage_history.clear()
