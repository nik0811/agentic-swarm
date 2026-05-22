import os
import json
from typing import List, AsyncIterator

from ..base import BaseLLMProvider, LLMMessage, LLMResponse


MODEL_INFO = {
    "llama-3.3-70b-versatile": {"context": 128000, "input_cost": 0.00059, "output_cost": 0.00079},
    "llama-3.1-8b-instant": {"context": 128000, "input_cost": 0.00005, "output_cost": 0.00008},
    "mixtral-8x7b-32768": {"context": 32768, "input_cost": 0.00024, "output_cost": 0.00024},
    "gemma2-9b-it": {"context": 8192, "input_cost": 0.00020, "output_cost": 0.00020},
}

DEFAULT_MODEL_INFO = {"context": 128000, "input_cost": 0.00059, "output_cost": 0.00079}


class GroqProvider(BaseLLMProvider):
    """Groq cloud LLM provider (OpenAI-compatible API)."""

    def __init__(self, model: str = "llama-3.3-70b-versatile", api_key: str = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        self._model_info = MODEL_INFO.get(model, DEFAULT_MODEL_INFO)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from groq import AsyncGroq
                self._client = AsyncGroq(api_key=self.api_key or os.getenv("GROQ_API_KEY"))
            except ImportError:
                raise ImportError("groq package not installed. Run: pip install groq")
        return self._client

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: List[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        client = self._get_client()

        msg_dicts = []
        for m in messages:
            d = m.model_dump(exclude_none=True)
            if not d.get("content", "").strip() and d.get("role") != "assistant":
                continue
            msg_dicts.append(d)

        request = {
            "model": self.model,
            "messages": msg_dicts,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            request["tools"] = tools
            request["tool_choice"] = "auto"

        response = await client.chat.completions.create(**request)
        choice = response.choices[0]

        tool_calls = []
        if choice.message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
                for tc in choice.message.tool_calls
            ]

        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
            model=response.model,
            finish_reason=choice.finish_reason,
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        tools: List[dict] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        client = self._get_client()

        request = {
            "model": self.model,
            "messages": [m.model_dump(exclude_none=True) for m in messages],
            "stream": True,
        }

        stream = await client.chat.completions.create(**request)
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    @property
    def context_window(self) -> int:
        return self._model_info["context"]

    @property
    def cost_per_1k_input(self) -> float:
        return self._model_info["input_cost"]

    @property
    def cost_per_1k_output(self) -> float:
        return self._model_info["output_cost"]
