import json
import os
from collections.abc import AsyncIterator

from ..base import BaseLLMProvider, LLMMessage, LLMResponse

MODEL_INFO = {
    "claude-3-5-sonnet-20241022": {"context": 200000, "input_cost": 0.003, "output_cost": 0.015},
    "claude-3-5-sonnet-latest": {"context": 200000, "input_cost": 0.003, "output_cost": 0.015},
    "claude-3-opus-20240229": {"context": 200000, "input_cost": 0.015, "output_cost": 0.075},
    "claude-3-sonnet-20240229": {"context": 200000, "input_cost": 0.003, "output_cost": 0.015},
    "claude-3-haiku-20240307": {"context": 200000, "input_cost": 0.00025, "output_cost": 0.00125},
}


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(self, model: str = "claude-3-5-sonnet-latest", api_key: str = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        self._model_info = MODEL_INFO.get(model, MODEL_INFO["claude-3-5-sonnet-latest"])
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic

                self._client = AsyncAnthropic(
                    api_key=self.api_key or os.getenv("ANTHROPIC_API_KEY")
                )
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. Run: pip install anthropic"
                ) from None
        return self._client

    def _convert_messages(self, messages: list[LLMMessage]) -> tuple[str, list[dict]]:
        """Convert messages to Anthropic format, extracting system message."""
        system = ""
        converted = []

        for msg in messages:
            if msg.role == "system":
                system = msg.content or ""
            else:
                content = msg.content or ""
                if not content.strip():
                    continue
                role = "user" if msg.role in ("user", "tool") else "assistant"
                if converted and converted[-1]["role"] == role:
                    converted[-1]["content"] += "\n" + content
                else:
                    converted.append({"role": role, "content": content})

        if converted and converted[0]["role"] != "user":
            converted.insert(0, {"role": "user", "content": "Continue."})

        return system, converted

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Convert OpenAI tool format to Anthropic format."""
        if not tools:
            return []

        converted = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                converted.append(
                    {
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "input_schema": func.get(
                            "parameters", {"type": "object", "properties": {}}
                        ),
                    }
                )
        return converted

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        client = self._get_client()

        system, converted_messages = self._convert_messages(messages)

        request = {
            "model": self.model,
            "messages": converted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            request["system"] = system

        if tools:
            request["tools"] = self._convert_tools(tools)

        response = await client.messages.create(**request)

        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    {
                        "id": block.id,
                        "name": block.name,
                        "arguments": json.dumps(block.input),
                    }
                )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
            model=response.model,
            finish_reason=response.stop_reason or "stop",
        )

    async def stream(
        self, messages: list[LLMMessage], tools: list[dict] = None, **kwargs
    ) -> AsyncIterator[str]:
        client = self._get_client()

        system, converted_messages = self._convert_messages(messages)

        request = {
            "model": self.model,
            "messages": converted_messages,
            "max_tokens": 4096,
        }

        if system:
            request["system"] = system

        async with client.messages.stream(**request) as stream:
            async for text in stream.text_stream:
                yield text

    @property
    def context_window(self) -> int:
        return self._model_info["context"]

    @property
    def cost_per_1k_input(self) -> float:
        return self._model_info["input_cost"]

    @property
    def cost_per_1k_output(self) -> float:
        return self._model_info["output_cost"]
