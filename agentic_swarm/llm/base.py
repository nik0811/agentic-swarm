from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str
    content: str
    name: str | None = None
    tool_call_id: str | None = None


class LLMResponse(BaseModel):
    content: str
    tool_calls: list[dict] = []
    usage: dict = {}
    model: str
    finish_reason: str


class BaseLLMProvider(ABC):
    """Base interface for LLM providers."""

    def __init__(self, model: str, api_key: str = None, **kwargs):
        self.model = model
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        """Send chat completion request."""
        pass

    @abstractmethod
    async def stream(
        self, messages: list[LLMMessage], tools: list[dict] = None, **kwargs
    ) -> AsyncIterator[str]:
        """Stream chat completion."""
        pass

    @property
    @abstractmethod
    def context_window(self) -> int:
        """Return model's context window size."""
        pass

    @property
    @abstractmethod
    def cost_per_1k_input(self) -> float:
        """Cost per 1000 input tokens."""
        pass

    @property
    @abstractmethod
    def cost_per_1k_output(self) -> float:
        """Cost per 1000 output tokens."""
        pass
