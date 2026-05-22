"""Reranking strategies for RAG retrieval results."""
from typing import List, Optional
from pydantic import BaseModel

from ..llm.base import BaseLLMProvider, LLMMessage


class RerankResult(BaseModel):
    """A reranked result with updated score."""
    content: str
    original_score: float
    reranked_score: float
    metadata: dict = {}


class Reranker:
    """Reranks retrieval results for improved relevance."""

    def __init__(
        self,
        strategy: str = "cross_encoder",
        llm_provider: Optional[BaseLLMProvider] = None,
        vector_weight: float = 0.4,
        keyword_weight: float = 0.2,
        freshness_weight: float = 0.1,
        relevance_weight: float = 0.3,
    ):
        self._strategy = strategy
        self._llm = llm_provider
        self._vector_weight = vector_weight
        self._keyword_weight = keyword_weight
        self._freshness_weight = freshness_weight
        self._relevance_weight = relevance_weight

    async def rerank(
        self,
        query: str,
        results: List[dict],
        top_k: int = 5,
    ) -> List[RerankResult]:
        """Rerank results based on strategy."""
        if self._strategy == "llm" and self._llm:
            return await self._rerank_with_llm(query, results, top_k)
        elif self._strategy == "keyword":
            return self._rerank_keyword(query, results, top_k)
        else:
            return self._rerank_hybrid(query, results, top_k)

    def _rerank_hybrid(self, query: str, results: List[dict], top_k: int) -> List[RerankResult]:
        """Hybrid reranking combining vector score and keyword overlap."""
        query_terms = set(query.lower().split())
        scored = []

        for r in results:
            content = r.get("content", "")
            original_score = r.get("score", 0.0)
            content_terms = set(content.lower().split())

            overlap = len(query_terms & content_terms)
            keyword_score = overlap / max(len(query_terms), 1)

            combined = (
                self._vector_weight * original_score
                + self._keyword_weight * keyword_score
                + self._relevance_weight * min(original_score * 1.2, 1.0)
            )

            scored.append(RerankResult(
                content=content,
                original_score=original_score,
                reranked_score=combined,
                metadata=r.get("metadata", {}),
            ))

        scored.sort(key=lambda x: x.reranked_score, reverse=True)
        return scored[:top_k]

    def _rerank_keyword(self, query: str, results: List[dict], top_k: int) -> List[RerankResult]:
        """Keyword-based reranking using term frequency."""
        query_terms = query.lower().split()
        scored = []

        for r in results:
            content = r.get("content", "").lower()
            score = sum(content.count(term) for term in query_terms)
            normalized = score / max(len(content.split()), 1)

            scored.append(RerankResult(
                content=r.get("content", ""),
                original_score=r.get("score", 0.0),
                reranked_score=normalized,
                metadata=r.get("metadata", {}),
            ))

        scored.sort(key=lambda x: x.reranked_score, reverse=True)
        return scored[:top_k]

    async def _rerank_with_llm(self, query: str, results: List[dict], top_k: int) -> List[RerankResult]:
        """Use LLM to score relevance of each result."""
        scored = []

        for r in results:
            content = r.get("content", "")[:500]
            messages = [
                LLMMessage(
                    role="system",
                    content="Rate the relevance of the document to the query on a scale of 0.0 to 1.0. Reply with ONLY the number.",
                ),
                LLMMessage(
                    role="user",
                    content=f"Query: {query}\n\nDocument: {content}",
                ),
            ]

            try:
                response = await self._llm.chat(messages, temperature=0.0, max_tokens=10)
                score = float(response.content.strip())
                score = max(0.0, min(1.0, score))
            except (ValueError, Exception):
                score = r.get("score", 0.0)

            scored.append(RerankResult(
                content=r.get("content", ""),
                original_score=r.get("score", 0.0),
                reranked_score=score,
                metadata=r.get("metadata", {}),
            ))

        scored.sort(key=lambda x: x.reranked_score, reverse=True)
        return scored[:top_k]
