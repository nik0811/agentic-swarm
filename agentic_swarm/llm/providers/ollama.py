import json
from typing import List, AsyncIterator

from ..base import BaseLLMProvider, LLMMessage, LLMResponse


MODEL_INFO = {
    "llama3.2": {"context": 8192, "input_cost": 0.0, "output_cost": 0.0},
    "mistral": {"context": 8192, "input_cost": 0.0, "output_cost": 0.0},
    "codellama": {"context": 8192, "input_cost": 0.0, "output_cost": 0.0},
    "phi3": {"context": 8192, "input_cost": 0.0, "output_cost": 0.0},
}

DEFAULT_MODEL_INFO = {"context": 8192, "input_cost": 0.0, "output_cost": 0.0}


class OllamaProvider(BaseLLMProvider):
    """Local Ollama LLM provider using HTTP API."""

    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(model, api_key=None, **kwargs)
        self.base_url = base_url.rstrip("/")
        self._model_info = MODEL_INFO.get(model, DEFAULT_MODEL_INFO)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import httpx
                self._client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)
            except ImportError:
                raise ImportError("httpx package not installed. Run: pip install httpx")
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
            d = {"role": m.role, "content": m.content or ""}
            if not d["content"].strip() and d["role"] != "assistant":
                continue
            msg_dicts.append(d)

        request_body = {
            "model": self.model,
            "messages": msg_dicts,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        response = await client.post("/api/chat", json=request_body)
        response.raise_for_status()
        data = response.json()

        content = data.get("message", {}).get("content", "")

        usage = {}
        if "prompt_eval_count" in data or "eval_count" in data:
            usage = {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            }

        return LLMResponse(
            content=content,
            tool_calls=[],
            usage=usage,
            model=self.model,
            finish_reason="stop" if data.get("done", False) else "length",
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        tools: List[dict] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        client = self._get_client()

        msg_dicts = []
        for m in messages:
            d = {"role": m.role, "content": m.content or ""}
            if not d["content"].strip() and d["role"] != "assistant":
                continue
            msg_dicts.append(d)

        request_body = {
            "model": self.model,
            "messages": msg_dicts,
            "stream": True,
        }

        async with client.stream("POST", "/api/chat", json=request_body) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                chunk = json.loads(line)
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content

    @property
    def context_window(self) -> int:
        return self._model_info["context"]

    @property
    def cost_per_1k_input(self) -> float:
        return self._model_info["input_cost"]

    @property
    def cost_per_1k_output(self) -> float:
        return self._model_info["output_cost"]
