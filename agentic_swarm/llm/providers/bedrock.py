import os
import json
from typing import List, AsyncIterator

from ..base import BaseLLMProvider, LLMMessage, LLMResponse


MODEL_INFO = {
    "us.anthropic.claude-opus-4-6-v1": {"context": 200000, "input_cost": 0.015, "output_cost": 0.075},
    "us.anthropic.claude-sonnet-4-20250514-v1:0": {"context": 200000, "input_cost": 0.003, "output_cost": 0.015},
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {"context": 200000, "input_cost": 0.003, "output_cost": 0.015},
    "anthropic.claude-3-sonnet-20240229-v1:0": {"context": 200000, "input_cost": 0.003, "output_cost": 0.015},
    "anthropic.claude-3-haiku-20240307-v1:0": {"context": 200000, "input_cost": 0.00025, "output_cost": 0.00125},
    "meta.llama3-70b-instruct-v1:0": {"context": 8000, "input_cost": 0.00265, "output_cost": 0.0035},
    "meta.llama3-8b-instruct-v1:0": {"context": 8000, "input_cost": 0.0003, "output_cost": 0.0006},
    "amazon.titan-text-express-v1": {"context": 8000, "input_cost": 0.0002, "output_cost": 0.0006},
    "amazon.titan-text-premier-v1:0": {"context": 32000, "input_cost": 0.0005, "output_cost": 0.0015},
    "mistral.mistral-7b-instruct-v0:2": {"context": 32000, "input_cost": 0.00015, "output_cost": 0.0002},
    "mistral.mixtral-8x7b-instruct-v0:1": {"context": 32000, "input_cost": 0.00045, "output_cost": 0.0007},
}

DEFAULT_MODEL_INFO = {"context": 200000, "input_cost": 0.003, "output_cost": 0.015}


class BedrockProvider(BaseLLMProvider):
    """AWS Bedrock LLM provider."""
    
    def __init__(
        self,
        model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        region: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        **kwargs
    ):
        super().__init__(model, api_key=None, **kwargs)
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self._model_info = MODEL_INFO.get(model, DEFAULT_MODEL_INFO)
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=self.region,
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                )
            except ImportError:
                raise ImportError("boto3 package not installed. Run: pip install boto3")
        return self._client
    
    def _convert_messages(self, messages: List[LLMMessage]) -> tuple[str, List[dict]]:
        """Convert messages to Bedrock format, extracting system message."""
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
                    converted[-1]["content"][0]["text"] += "\n" + content
                else:
                    converted.append({"role": role, "content": [{"text": content}]})
        
        if converted and converted[0]["role"] != "user":
            converted.insert(0, {"role": "user", "content": [{"text": "Continue."}]})
        
        return system, converted
    
    def _convert_tools(self, tools: List[dict]) -> List[dict]:
        """Convert OpenAI tool format to Bedrock format."""
        if not tools:
            return []
        
        converted = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                converted.append({
                    "toolSpec": {
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "inputSchema": {
                            "json": func.get("parameters", {"type": "object", "properties": {}})
                        },
                    }
                })
        return converted
    
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: List[dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        client = self._get_client()
        
        system, converted_messages = self._convert_messages(messages)
        
        request = {
            "modelId": self.model,
            "messages": converted_messages,
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
        }
        
        if system:
            request["system"] = [{"text": system}]
        
        if tools:
            request["toolConfig"] = {"tools": self._convert_tools(tools)}
        
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.converse(**request)
        )
        
        content = ""
        tool_calls = []
        
        for block in response.get("output", {}).get("message", {}).get("content", []):
            if "text" in block:
                content = block["text"]
            elif "toolUse" in block:
                tool_use = block["toolUse"]
                tool_calls.append({
                    "id": tool_use.get("toolUseId", ""),
                    "name": tool_use.get("name", ""),
                    "arguments": json.dumps(tool_use.get("input", {})),
                })
        
        usage = response.get("usage", {})
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": usage.get("inputTokens", 0),
                "completion_tokens": usage.get("outputTokens", 0),
            },
            model=self.model,
            finish_reason=response.get("stopReason", "end_turn"),
        )
    
    async def stream(
        self,
        messages: List[LLMMessage],
        tools: List[dict] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        client = self._get_client()
        
        system, converted_messages = self._convert_messages(messages)
        
        request = {
            "modelId": self.model,
            "messages": converted_messages,
            "inferenceConfig": {
                "maxTokens": 4096,
            },
        }
        
        if system:
            request["system"] = [{"text": system}]
        
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.converse_stream(**request)
        )
        
        for event in response.get("stream", []):
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"].get("delta", {})
                if "text" in delta:
                    yield delta["text"]
    
    @property
    def context_window(self) -> int:
        return self._model_info["context"]
    
    @property
    def cost_per_1k_input(self) -> float:
        return self._model_info["input_cost"]
    
    @property
    def cost_per_1k_output(self) -> float:
        return self._model_info["output_cost"]
