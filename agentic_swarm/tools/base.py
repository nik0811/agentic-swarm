from typing import Any, Callable, get_type_hints, List
from pydantic import BaseModel
import inspect


class ToolSchema(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]
    required: list[str]


class Tool:
    def __init__(
        self,
        func: Callable,
        name: str | None = None,
        description: str | None = None,
    ):
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or ""
        self.schema = self._generate_schema()
        self.is_async = inspect.iscoroutinefunction(func)
    
    def _generate_schema(self) -> ToolSchema:
        """Generate JSON schema from function signature."""
        hints = get_type_hints(self.func)
        sig = inspect.signature(self.func)
        
        parameters = {"type": "object", "properties": {}}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            
            param_type = hints.get(param_name, str)
            param_schema = self._type_to_schema(param_type)
            parameters["properties"][param_name] = param_schema
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return ToolSchema(
            name=self.name,
            description=self.description.strip(),
            parameters=parameters,
            required=required,
        )
    
    def _type_to_schema(self, t) -> dict:
        """Convert Python type to JSON schema."""
        type_map = {
            str: {"type": "string"},
            int: {"type": "integer"},
            float: {"type": "number"},
            bool: {"type": "boolean"},
            list: {"type": "array"},
            dict: {"type": "object"},
        }
        origin = getattr(t, "__origin__", None)
        if origin is list:
            return {"type": "array"}
        if origin is dict:
            return {"type": "object"}
        return type_map.get(t, {"type": "string"})
    
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with given arguments."""
        if self.is_async:
            return await self.func(**kwargs)
        return self.func(**kwargs)
    
    def to_openai_schema(self) -> dict:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema.parameters,
            }
        }
