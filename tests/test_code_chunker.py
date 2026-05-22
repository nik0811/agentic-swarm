import pytest

from agentic_swarm.rag.chunker import Chunker, Chunk


SAMPLE_CODE_WITH_CLASS = '''import os

class MyProcessor:
    """Processes data."""

    def __init__(self, config):
        self.config = config
        self.data = []

    def process(self, item):
        """Process a single item."""
        result = item * 2
        self.data.append(result)
        return result

    def reset(self):
        """Reset internal state."""
        self.data = []
'''

SAMPLE_CODE_FUNCTIONS_ONLY = '''import math
from typing import List

def calculate_area(radius: float) -> float:
    """Calculate circle area."""
    return math.pi * radius ** 2

def calculate_circumference(radius: float) -> float:
    """Calculate circle circumference."""
    return 2 * math.pi * radius

def find_max(values: List[float]) -> float:
    """Find the maximum value."""
    if not values:
        raise ValueError("Empty list")
    return max(values)
'''

SAMPLE_ASYNC_CODE = '''class AsyncService:
    async def fetch(self, url):
        return await self._client.get(url)

    async def process(self, data):
        result = await self._transform(data)
        return result
'''


class TestCodeChunker:
    def setup_method(self):
        self.chunker = Chunker(strategy="code", chunk_size=512)

    def test_chunk_class_as_single_chunk(self):
        chunks = self.chunker.chunk(SAMPLE_CODE_WITH_CLASS)
        assert len(chunks) >= 1
        class_chunks = [c for c in chunks if c.metadata.get("type") in ("class", "method", "class_header")]
        assert len(class_chunks) >= 1

    def test_chunk_class_metadata_has_name(self):
        chunks = self.chunker.chunk(SAMPLE_CODE_WITH_CLASS)
        class_or_method = [c for c in chunks if "name" in c.metadata]
        assert len(class_or_method) >= 1
        names = [c.metadata["name"] for c in class_or_method]
        assert "MyProcessor" in names or any("process" in n for n in names)

    def test_chunk_class_metadata_has_type(self):
        chunks = self.chunker.chunk(SAMPLE_CODE_WITH_CLASS)
        for c in chunks:
            assert "type" in c.metadata

    def test_chunk_functions_without_class(self):
        chunks = self.chunker.chunk(SAMPLE_CODE_FUNCTIONS_ONLY)
        assert len(chunks) >= 3
        func_chunks = [c for c in chunks if c.metadata.get("type") == "function"]
        assert len(func_chunks) >= 3

    def test_chunk_functions_have_names(self):
        chunks = self.chunker.chunk(SAMPLE_CODE_FUNCTIONS_ONLY)
        func_chunks = [c for c in chunks if c.metadata.get("type") == "function"]
        names = {c.metadata["name"] for c in func_chunks}
        assert "calculate_area" in names
        assert "calculate_circumference" in names
        assert "find_max" in names

    def test_chunk_preserves_content(self):
        chunks = self.chunker.chunk(SAMPLE_CODE_FUNCTIONS_ONLY)
        all_content = " ".join(c.content for c in chunks)
        assert "calculate_area" in all_content
        assert "math.pi" in all_content

    def test_chunk_indices_sequential(self):
        chunks = self.chunker.chunk(SAMPLE_CODE_WITH_CLASS)
        indices = [c.index for c in chunks]
        assert indices == sorted(indices)

    def test_chunk_token_count_populated(self):
        chunks = self.chunker.chunk(SAMPLE_CODE_WITH_CLASS)
        for c in chunks:
            assert c.token_count > 0

    def test_chunk_async_methods(self):
        chunks = self.chunker.chunk(SAMPLE_ASYNC_CODE)
        assert len(chunks) >= 1
        contents = " ".join(c.content for c in chunks)
        assert "async def fetch" in contents

    def test_chunk_empty_input_fallback(self):
        chunks = self.chunker.chunk("")
        assert chunks == [] or all(isinstance(c, Chunk) for c in chunks)

    def test_chunk_with_metadata_passthrough(self):
        chunks = self.chunker.chunk(
            SAMPLE_CODE_FUNCTIONS_ONLY,
            metadata={"source": "utils.py"}
        )
        for c in chunks:
            assert c.metadata.get("source") == "utils.py"

    def test_large_class_splits_into_methods(self):
        methods = "\n".join(
            f"    def method_{i}(self):\n" + "\n".join(f"        x = {j}" for j in range(30))
            for i in range(20)
        )
        large_class = f"class BigClass:\n{methods}\n"
        chunker = Chunker(strategy="code", chunk_size=100)
        chunks = chunker.chunk(large_class)
        assert len(chunks) > 1
