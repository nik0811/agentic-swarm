import pytest
from agentic_swarm import tool
from agentic_swarm.tools.base import Tool


def test_tool_decorator_sync():
    @tool
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b
    
    assert isinstance(add, Tool)
    assert add.name == "add"
    assert "Add two numbers" in add.description


def test_tool_decorator_async():
    @tool
    async def fetch(url: str) -> str:
        """Fetch URL content."""
        return f"Content from {url}"
    
    assert fetch.is_async
    assert "url" in fetch.schema.required


def test_tool_schema_generation():
    @tool
    def search(query: str, limit: int = 10) -> list:
        """Search for items."""
        return []
    
    schema = search.schema
    assert schema.name == "search"
    assert "query" in schema.required
    assert "limit" not in schema.required


def test_tool_openai_schema():
    @tool
    def greet(name: str) -> str:
        """Greet someone."""
        return f"Hello {name}"
    
    openai_schema = greet.to_openai_schema()
    assert openai_schema["type"] == "function"
    assert openai_schema["function"]["name"] == "greet"
    assert "name" in openai_schema["function"]["parameters"]["properties"]


@pytest.mark.asyncio
async def test_tool_execution_sync():
    @tool
    def multiply(x: int, y: int) -> int:
        return x * y
    
    result = await multiply.execute(x=3, y=4)
    assert result == 12


@pytest.mark.asyncio
async def test_tool_execution_async():
    @tool
    async def async_add(a: int, b: int) -> int:
        return a + b
    
    result = await async_add.execute(a=5, b=3)
    assert result == 8


def test_tool_with_custom_name():
    @tool(name="custom_search", description="Custom search tool")
    def my_search(query: str) -> list:
        return []
    
    assert my_search.name == "custom_search"
    assert my_search.description == "Custom search tool"
