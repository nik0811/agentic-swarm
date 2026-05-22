import os
from typing import List, AsyncIterator

from ..base import BaseLLMProvider, LLMMessage, LLMResponse


MODEL_INFO = {
    "gpt-4o": {"context": 128000, "input_cost": 0.005, "output_cost": 0.015},
    "gpt-4o-mini": {"context": 128000, "input_cost": 0.00015, "output_cost": 0.0006},
    "gpt-4-turbo": {"context": 128000, "input_cost": 0.01, "output_cost": 0.03},
    "gpt-3.5-turbo": {"context": 16385, "input_cost": 0.0005, "output_cost": 0.0015},
    "o1-mini": {"context": 128000, "input_cost": 0.003, "output_cost": 0.012},
    "o1-preview": {"context": 128000, "input_cost": 0.015, "output_cost": 0.06},
}


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: str = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        self._model_info = MODEL_INFO.get(model, MODEL_INFO["gpt-4o-mini"])
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key or os.getenv("OPENAI_API_KEY"))
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
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
