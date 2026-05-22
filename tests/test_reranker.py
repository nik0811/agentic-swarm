import pytest

from agentic_swarm.rag.reranker import Reranker, RerankResult


class TestRerankerHybrid:
    def setup_method(self):
        self.reranker = Reranker(strategy="cross_encoder")

    @pytest.mark.asyncio
    async def test_hybrid_reranking_returns_results(self):
        results = [
            {"content": "python programming language", "score": 0.9},
            {"content": "java enterprise framework", "score": 0.8},
            {"content": "python data science tools", "score": 0.7},
        ]
        reranked = await self.reranker.rerank("python programming", results, top_k=3)
        assert len(reranked) == 3
        assert all(isinstance(r, RerankResult) for r in reranked)

    @pytest.mark.asyncio
    async def test_hybrid_reranking_ordering(self):
        results = [
            {"content": "unrelated topic about cooking", "score": 0.5},
            {"content": "python machine learning tutorial", "score": 0.8},
            {"content": "python programming basics guide", "score": 0.9},
        ]
        reranked = await self.reranker.rerank("python programming", results, top_k=3)
        assert reranked[0].reranked_score >= reranked[1].reranked_score
        assert reranked[1].reranked_score >= reranked[2].reranked_score

    @pytest.mark.asyncio
    async def test_hybrid_top_k_limits(self):
        results = [
            {"content": f"document {i}", "score": 0.5}
            for i in range(10)
        ]
        reranked = await self.reranker.rerank("document", results, top_k=3)
        assert len(reranked) == 3

    @pytest.mark.asyncio
    async def test_hybrid_preserves_metadata(self):
        results = [
            {"content": "test content", "score": 0.8, "metadata": {"source": "file.txt"}},
        ]
        reranked = await self.reranker.rerank("test", results, top_k=5)
        assert reranked[0].metadata == {"source": "file.txt"}

    @pytest.mark.asyncio
    async def test_hybrid_keyword_overlap_boosts(self):
        results = [
            {"content": "no overlap here at all", "score": 0.85},
            {"content": "python programming is great for python developers", "score": 0.80},
        ]
        reranked = await self.reranker.rerank("python programming", results, top_k=2)
        python_result = next(r for r in reranked if "python" in r.content)
        assert python_result.reranked_score > 0


class TestRerankerKeyword:
    def setup_method(self):
        self.reranker = Reranker(strategy="keyword")

    @pytest.mark.asyncio
    async def test_keyword_reranking(self):
        results = [
            {"content": "cats and dogs are great pets", "score": 0.5},
            {"content": "python python python code python", "score": 0.3},
            {"content": "java enterprise application", "score": 0.9},
        ]
        reranked = await self.reranker.rerank("python code", results, top_k=3)
        assert reranked[0].content == "python python python code python"

    @pytest.mark.asyncio
    async def test_keyword_empty_query(self):
        results = [
            {"content": "some content", "score": 0.5},
        ]
        reranked = await self.reranker.rerank("", results, top_k=5)
        assert len(reranked) == 1

    @pytest.mark.asyncio
    async def test_keyword_normalized_scoring(self):
        results = [
            {"content": "short python", "score": 0.5},
            {"content": "a very long document with many words but only one mention of python among all the other filler text", "score": 0.5},
        ]
        reranked = await self.reranker.rerank("python", results, top_k=2)
        assert reranked[0].content == "short python"

    @pytest.mark.asyncio
    async def test_keyword_ordering_descending(self):
        results = [
            {"content": "alpha beta", "score": 0.5},
            {"content": "alpha alpha alpha", "score": 0.4},
            {"content": "gamma delta", "score": 0.9},
        ]
        reranked = await self.reranker.rerank("alpha", results, top_k=3)
        for i in range(len(reranked) - 1):
            assert reranked[i].reranked_score >= reranked[i + 1].reranked_score
