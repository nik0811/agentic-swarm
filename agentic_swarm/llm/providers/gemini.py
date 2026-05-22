import os
import json
from typing import List, AsyncIterator

from ..base import BaseLLMProvider, LLMMessage, LLMResponse


MODEL_INFO = {
    "gemini-2.0-flash": {"context": 1048576, "input_cost": 0.00015, "output_cost": 0.0006},
    "gemini-2.0-flash-lite": {"context": 1048576, "input_cost": 0.000075, "output_cost": 0.0003},
    "gemini-1.5-pro": {"context": 2097152, "input_cost": 0.00125, "output_cost": 0.005},
    "gemini-1.5-flash": {"context": 1048576, "input_cost": 0.000075, "output_cost": 0.0003},
}

DEFAULT_MODEL_INFO = {"context": 1048576, "input_cost": 0.00015, "output_cost": 0.0006}


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider using the google-genai SDK."""

    def __init__(self, model: str = "gemini-2.0-flash", api_key: str = None, **kwargs):
        super().__init__(model, api_key, **kwargs)
        self._model_info = MODEL_INFO.get(model, DEFAULT_MODEL_INFO)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from google import genai
                api_key = self.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable required")
                self._client = genai.Client(api_key=api_key)
            except ImportError:
                raise ImportError("google-genai package not installed. Run: pip install google-genai")
        return self._client

    def _convert_messages(self, messages: List[LLMMessage]) -> tuple[str, List[dict]]:
        """Convert messages to Gemini format, extracting system instruction."""
        system = ""
        converted = []

        for msg in messages:
            if msg.role == "system":
                system = msg.content or ""
            else:
                content = msg.content or ""
                if not content.strip():
                    continue
                role = "user" if msg.role == "user" else "model"
                if converted and converted[-1]["role"] == role:
                    converted[-1]["parts"][0]["text"] += "\n" + content
                else:
                    converted.append({"role": role, "parts": [{"text": content}]})

        if converted and converted[0]["role"] != "user":
            converted.insert(0, {"role": "user", "parts": [{"text": "Continue."}]})

        return system, converted

    def _convert_tools(self, tools: List[dict]) -> List[dict]:
        """Convert OpenAI tool format to Gemini function declarations."""
        if not tools:
            return []

        declarations = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                declarations.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {"type": "object", "properties": {}}),
                })
        return declarations

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: List[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        client = self._get_client()
        from google.genai import types

        system, converted_messages = self._convert_messages(messages)

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        if system:
            config.system_instruction = system

        if tools:
            declarations = self._convert_tools(tools)
            config.tools = [types.Tool(function_declarations=[
                types.FunctionDeclaration(**d) for d in declarations
            ])]

        contents = [
            types.Content(role=m["role"], parts=[types.Part.from_text(p["text"]) for p in m["parts"]])
            for m in converted_messages
        ]

        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
        )

        content = ""
        tool_calls = []

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.text:
                    content += part.text
                elif part.function_call:
                    fc = part.function_call
                    tool_calls.append({
                        "id": fc.name,
                        "name": fc.name,
                        "arguments": json.dumps(dict(fc.args) if fc.args else {}),
                    })

        usage_meta = response.usage_metadata
        usage = {
            "prompt_tokens": getattr(usage_meta, "prompt_token_count", 0) or 0,
            "completion_tokens": getattr(usage_meta, "candidates_token_count", 0) or 0,
        }

        finish_reason = "stop"
        if response.candidates:
            fr = response.candidates[0].finish_reason
            if fr:
                finish_reason = str(fr).lower()

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=usage,
            model=self.model,
            finish_reason=finish_reason,
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        tools: List[dict] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        client = self._get_client()
        from google.genai import types

        system, converted_messages = self._convert_messages(messages)

        config = types.GenerateContentConfig(
            max_output_tokens=kwargs.get("max_tokens", 4096),
        )

        if system:
            config.system_instruction = system

        contents = [
            types.Content(role=m["role"], parts=[types.Part.from_text(p["text"]) for p in m["parts"]])
            for m in converted_messages
        ]

        import asyncio
        loop = asyncio.get_event_loop()

        def _stream():
            return client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=config,
            )

        stream = await loop.run_in_executor(None, _stream)
        for chunk in stream:
            if chunk.text:
                yield chunk.text

    @property
    def context_window(self) -> int:
        return self._model_info["context"]

    @property
    def cost_per_1k_input(self) -> float:
        return self._model_info["input_cost"]

    @property
    def cost_per_1k_output(self) -> float:
        return self._model_info["output_cost"]
