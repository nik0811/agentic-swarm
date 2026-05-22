import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agentic_swarm.rag.query_engine import QueryEngine, QueryResult
from agentic_swarm.rag.retriever import Retriever, RetrievalResult


def _make_retrieval_result(content: str, score: float, metadata: dict = None):
    return RetrievalResult(content=content, score=score, metadata=metadata or {})


class TestQueryEngine:
    def setup_method(self):
        self.mock_retriever = MagicMock(spec=Retriever)
        self.mock_retriever.retrieve = AsyncMock(return_value=[])

    @pytest.mark.asyncio
    async def test_query_without_llm_returns_context(self):
        results = [
            _make_retrieval_result("doc one content", 0.9, {"source": "a.txt"}),
            _make_retrieval_result("doc two content", 0.7, {"source": "b.txt"}),
        ]
        self.mock_retriever.retrieve = AsyncMock(return_value=results)

        engine = QueryEngine(
            retriever=self.mock_retriever,
            llm_provider=None,
            enable_query_expansion=False,
        )
        result = await engine.query("test question")

        assert isinstance(result, QueryResult)
        assert "doc one content" in result.answer
        assert "doc two content" in result.answer
        assert result.context_used == result.answer
        assert len(result.sources) == 2

    @pytest.mark.asyncio
    async def test_query_without_llm_sources_have_metadata(self):
        results = [
            _make_retrieval_result("content", 0.8, {"source": "myfile.md"}),
        ]
        self.mock_retriever.retrieve = AsyncMock(return_value=results)

        engine = QueryEngine(
            retriever=self.mock_retriever,
            llm_provider=None,
            enable_query_expansion=False,
        )
        result = await engine.query("question")

        assert result.sources[0]["source"] == "myfile.md"
        assert "content_preview" in result.sources[0]

    @pytest.mark.asyncio
    async def test_deduplication(self):
        results = [
            _make_retrieval_result("same content here and more text to fill", 0.9),
            _make_retrieval_result("same content here and more text to fill", 0.8),
            _make_retrieval_result("different content entirely", 0.7),
        ]
        self.mock_retriever.retrieve = AsyncMock(return_value=results)

        engine = QueryEngine(
            retriever=self.mock_retriever,
            llm_provider=None,
            enable_query_expansion=False,
        )
        result = await engine.query("question")

        assert result.context_used.count("same content here") == 1
        assert "different content entirely" in result.context_used

    @pytest.mark.asyncio
    async def test_context_assembly_format(self):
        results = [
            _make_retrieval_result("first doc", 0.9, {"source": "file1.txt"}),
            _make_retrieval_result("second doc", 0.8, {"filename": "file2.txt"}),
        ]
        self.mock_retriever.retrieve = AsyncMock(return_value=results)

        engine = QueryEngine(
            retriever=self.mock_retriever,
            llm_provider=None,
            enable_query_expansion=False,
        )
        result = await engine.query("test")

        assert "[Source: file1.txt]" in result.context_used
        assert "[Source: file2.txt]" in result.context_used

    @pytest.mark.asyncio
    async def test_expanded_queries_without_llm(self):
        self.mock_retriever.retrieve = AsyncMock(return_value=[])

        engine = QueryEngine(
            retriever=self.mock_retriever,
            llm_provider=None,
            enable_query_expansion=True,
        )
        result = await engine.query("question")
        assert result.expanded_queries == ["question"]

    @pytest.mark.asyncio
    async def test_max_context_chunks_limit(self):
        results = [
            _make_retrieval_result(f"doc {i}", 0.9 - i * 0.1)
            for i in range(10)
        ]
        self.mock_retriever.retrieve = AsyncMock(return_value=results)

        engine = QueryEngine(
            retriever=self.mock_retriever,
            llm_provider=None,
            max_context_chunks=3,
            enable_query_expansion=False,
        )
        result = await engine.query("test")

        source_count = result.context_used.count("[Source:")
        assert source_count <= 3

    @pytest.mark.asyncio
    async def test_empty_results(self):
        self.mock_retriever.retrieve = AsyncMock(return_value=[])

        engine = QueryEngine(
            retriever=self.mock_retriever,
            llm_provider=None,
            enable_query_expansion=False,
        )
        result = await engine.query("something")

        assert result.answer == ""
        assert result.sources == []
