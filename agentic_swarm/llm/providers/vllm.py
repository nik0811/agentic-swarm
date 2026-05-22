from collections.abc import AsyncIterator

from ..base import BaseLLMProvider, LLMMessage, LLMResponse

DEFAULT_MODEL_INFO = {"context": 8192, "input_cost": 0.0, "output_cost": 0.0}


class VLLMProvider(BaseLLMProvider):
    """vLLM server provider (OpenAI-compatible API)."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "EMPTY",
        **kwargs,
    ):
        super().__init__(model, api_key=api_key, **kwargs)
        self.base_url = base_url
        self._model_info = DEFAULT_MODEL_INFO
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(
                    api_key=self.api_key or "EMPTY",
                    base_url=self.base_url,
                )
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai") from None
        return self._client

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        client = self._get_client()

        msg_dicts = []
        for m in messages:
            d = m.model_dump(exclude_none=True)
            if d.get("role") == "tool":
                d["role"] = "user"
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

        usage_data = {}
        if response.usage:
            usage_data = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }

        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            usage=usage_data,
            model=response.model or self.model,
            finish_reason=choice.finish_reason or "stop",
        )

    async def stream(
        self, messages: list[LLMMessage], tools: list[dict] = None, **kwargs
    ) -> AsyncIterator[str]:
        client = self._get_client()

        msg_dicts = []
        for m in messages:
            d = m.model_dump(exclude_none=True)
            if d.get("role") == "tool":
                d["role"] = "user"
            if not d.get("content", "").strip() and d.get("role") != "assistant":
                continue
            msg_dicts.append(d)

        request = {
            "model": self.model,
            "messages": msg_dicts,
            "stream": True,
        }

        stream = await client.chat.completions.create(**request)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
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
