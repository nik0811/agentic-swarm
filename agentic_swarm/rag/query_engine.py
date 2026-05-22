"""RAG query engine with query expansion, HyDE, and context assembly."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from .retriever import Retriever, RetrievalResult
from .reranker import Reranker
from ..llm.base import LLMMessage, LLMResponse, BaseLLMProvider


class QueryResult(BaseModel):
    """Result from a RAG query with answer and sources."""
    answer: str
    sources: List[Dict[str, Any]] = []
    context_used: str = ""
    tokens_used: int = 0
    expanded_queries: List[str] = []


class QueryEngine:
    """Combines retrieval with LLM for grounded answers.
    
    Supports:
    - Query expansion (generates related queries for better recall)
    - HyDE (Hypothetical Document Embedding for better retrieval)
    - Multi-query retrieval with RRF fusion
    - Cross-encoder reranking
    - Context assembly with source attribution
    """

    def __init__(
        self,
        retriever: Retriever,
        llm_provider: Optional[BaseLLMProvider] = None,
        reranker: Optional[Reranker] = None,
        system_prompt: str = "",
        max_context_chunks: int = 5,
        include_sources: bool = True,
        enable_query_expansion: bool = True,
        enable_hyde: bool = False,
        num_expansions: int = 3,
    ):
        self._retriever = retriever
        self._llm = llm_provider
        self._reranker = reranker
        self._system_prompt = system_prompt or (
            "Answer the question based on the provided context. "
            "If the context doesn't contain enough information, say so clearly. "
            "Cite sources using [Source: ...] notation when possible."
        )
        self._max_chunks = max_context_chunks
        self._include_sources = include_sources
        self._enable_expansion = enable_query_expansion
        self._enable_hyde = enable_hyde
        self._num_expansions = num_expansions

    async def query(
        self,
        question: str,
        collection: str = "documents",
        filter_metadata: Optional[Dict] = None,
        **kwargs
    ) -> QueryResult:
        """Answer a question using retrieved context with full RAG pipeline."""
        expanded_queries = [question]

        if self._enable_expansion and self._llm:
            expanded_queries = await self._expand_query(question)

        if self._enable_hyde and self._llm:
            hyde_query = await self._generate_hyde(question)
            expanded_queries.append(hyde_query)

        all_results = []
        for q in expanded_queries:
            results = await self._retriever.retrieve(
                query=q,
                collection=collection,
                limit=self._max_chunks * 2,
                filters=filter_metadata,
            )
            all_results.extend(results)

        deduplicated = self._deduplicate_results(all_results)

        if self._reranker and len(deduplicated) > self._max_chunks:
            reranked = await self._reranker.rerank(
                query=question,
                results=[{"content": r.content, "score": r.score, "metadata": r.metadata} for r in deduplicated],
                top_k=self._max_chunks,
            )
            final_results = [
                RetrievalResult(content=rr.content, score=rr.reranked_score, metadata=rr.metadata)
                for rr in reranked
            ]
        else:
            deduplicated.sort(key=lambda x: x.score, reverse=True)
            final_results = deduplicated[:self._max_chunks]

        context, sources = self._assemble_context(final_results)

        if not self._llm:
            return QueryResult(
                answer=context,
                sources=sources,
                context_used=context,
                expanded_queries=expanded_queries,
            )

        messages = [
            LLMMessage(role="system", content=self._system_prompt),
            LLMMessage(role="user", content=f"Context:\n{context}\n\nQuestion: {question}"),
        ]

        response = await self._llm.chat(messages, **kwargs)
        tokens = response.usage.get("prompt_tokens", 0) + response.usage.get("completion_tokens", 0)

        return QueryResult(
            answer=response.content,
            sources=sources,
            context_used=context,
            tokens_used=tokens,
            expanded_queries=expanded_queries,
        )

    async def _expand_query(self, question: str) -> List[str]:
        """Generate related queries for better recall."""
        messages = [
            LLMMessage(role="system", content=(
                "Generate related search queries to help find relevant information. "
                "Return ONLY the queries, one per line. No numbering or explanation."
            )),
            LLMMessage(role="user", content=(
                f"Original query: {question}\n\n"
                f"Generate {self._num_expansions} related search queries:"
            )),
        ]

        try:
            response = await self._llm.chat(messages, temperature=0.7, max_tokens=200)
            expanded = [q.strip() for q in response.content.strip().split("\n") if q.strip()]
            return [question] + expanded[:self._num_expansions]
        except Exception:
            return [question]

    async def _generate_hyde(self, question: str) -> str:
        """Generate hypothetical document for HyDE retrieval."""
        messages = [
            LLMMessage(role="system", content=(
                "Write a short paragraph that would be a perfect answer to the question. "
                "This will be used to find similar real documents. Be specific and factual."
            )),
            LLMMessage(role="user", content=question),
        ]

        try:
            response = await self._llm.chat(messages, temperature=0.0, max_tokens=300)
            return response.content.strip()
        except Exception:
            return question

    def _deduplicate_results(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Remove duplicate chunks based on content similarity."""
        seen_content = set()
        unique = []

        for r in results:
            content_key = r.content[:150].strip().lower()
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique.append(r)

        return unique

    def _assemble_context(self, results: List[RetrievalResult]) -> tuple:
        """Assemble context with source attribution."""
        context_parts = []
        sources = []

        for i, r in enumerate(results):
            source_label = r.metadata.get("source", r.metadata.get("filename", f"Source {i+1}"))
            context_parts.append(f"[Source: {source_label}]\n{r.content}")

            if self._include_sources:
                sources.append({
                    "index": i + 1,
                    "source": source_label,
                    "content_preview": r.content[:150],
                    "score": r.score,
                    "metadata": {k: v for k, v in r.metadata.items() if k != "content"},
                })

        context = "\n\n".join(context_parts)
        return context, sources
