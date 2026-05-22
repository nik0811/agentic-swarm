from typing import List, Literal, Optional
from pydantic import BaseModel
import math
from collections import Counter

from ..vectordb.base import BaseVectorDB, VectorSearchResult
from .embedder import Embedder


class RetrievalResult(BaseModel):
    content: str
    score: float
    metadata: dict = {}


class BM25:
    """BM25 sparse retrieval implementation."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._corpus: List[List[str]] = []
        self._doc_payloads: List[dict] = []
        self._df: Counter = Counter()
        self._avg_dl: float = 0.0
        self._n_docs: int = 0

    def index(self, documents: List[dict]) -> None:
        """Index documents for BM25 search."""
        self._corpus = []
        self._doc_payloads = documents
        self._df = Counter()
        self._n_docs = len(documents)

        total_len = 0
        for doc in documents:
            tokens = self._tokenize(doc.get("content", ""))
            self._corpus.append(tokens)
            total_len += len(tokens)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self._df[token] += 1

        self._avg_dl = total_len / max(self._n_docs, 1)

    def search(self, query: str, limit: int = 10) -> List[tuple]:
        """Search using BM25 scoring. Returns (score, doc_index) pairs."""
        query_tokens = self._tokenize(query)
        scores = []

        for i, doc_tokens in enumerate(self._corpus):
            score = self._score_document(query_tokens, doc_tokens)
            if score > 0:
                scores.append((score, i))

        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:limit]

    def _score_document(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        dl = len(doc_tokens)
        tf_counter = Counter(doc_tokens)
        score = 0.0

        for term in query_tokens:
            if term not in tf_counter:
                continue

            tf = tf_counter[term]
            df = self._df.get(term, 0)
            idf = math.log((self._n_docs - df + 0.5) / (df + 0.5) + 1.0)
            tf_norm = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / self._avg_dl))
            score += idf * tf_norm

        return score

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple whitespace + lowercase tokenization."""
        import re
        return re.findall(r'\w+', text.lower())


class Retriever:
    """Retrieve relevant chunks from vector DB with multi-strategy support."""

    def __init__(
        self,
        vectordb: BaseVectorDB,
        embedder: Embedder,
        strategy: Literal["dense", "sparse", "hybrid"] = "dense",
    ):
        self.vectordb = vectordb
        self.embedder = embedder
        self.strategy = strategy
        self._bm25 = BM25()
        self._indexed_collection: Optional[str] = None

    async def retrieve(
        self,
        query: str,
        collection: str,
        limit: int = 5,
        filters: dict = None,
    ) -> List[RetrievalResult]:
        """Retrieve relevant chunks using configured strategy."""
        if self.strategy == "dense":
            return await self._retrieve_dense(query, collection, limit, filters)
        elif self.strategy == "sparse":
            return await self._retrieve_sparse(query, collection, limit, filters)
        elif self.strategy == "hybrid":
            return await self._retrieve_hybrid(query, collection, limit, filters)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    async def _retrieve_dense(
        self,
        query: str,
        collection: str,
        limit: int,
        filters: dict = None,
    ) -> List[RetrievalResult]:
        """Dense retrieval using vector similarity."""
        query_vector = await self.embedder.embed_query(query)

        results = await self.vectordb.search(
            collection=collection,
            query_vector=query_vector,
            limit=limit,
            filters=filters,
        )

        return [
            RetrievalResult(
                content=r.payload.get("content", ""),
                score=r.score,
                metadata=r.payload,
            )
            for r in results
        ]

    async def _retrieve_sparse(
        self,
        query: str,
        collection: str,
        limit: int,
        filters: dict = None,
    ) -> List[RetrievalResult]:
        """BM25-based sparse retrieval."""
        await self._ensure_bm25_index(collection, filters)

        bm25_results = self._bm25.search(query, limit)
        results = []

        max_score = bm25_results[0][0] if bm25_results else 1.0
        for score, idx in bm25_results:
            doc = self._bm25._doc_payloads[idx]
            results.append(RetrievalResult(
                content=doc.get("content", ""),
                score=score / max_score,
                metadata=doc,
            ))

        return results

    async def _retrieve_hybrid(
        self,
        query: str,
        collection: str,
        limit: int,
        filters: dict = None,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
    ) -> List[RetrievalResult]:
        """Hybrid retrieval using Reciprocal Rank Fusion (RRF) of dense + sparse."""
        dense_limit = limit * 3
        sparse_limit = limit * 3

        dense_results = await self._retrieve_dense(query, collection, dense_limit, filters)
        sparse_results = await self._retrieve_sparse(query, collection, sparse_limit, filters)

        fused = self._reciprocal_rank_fusion(
            [dense_results, sparse_results],
            weights=[dense_weight, sparse_weight],
            k=60,
        )

        return fused[:limit]

    def _reciprocal_rank_fusion(
        self,
        result_lists: List[List[RetrievalResult]],
        weights: List[float] = None,
        k: int = 60,
    ) -> List[RetrievalResult]:
        """Combine multiple ranked lists using RRF."""
        if weights is None:
            weights = [1.0] * len(result_lists)

        scores: dict = {}
        content_map: dict = {}

        for list_idx, results in enumerate(result_lists):
            weight = weights[list_idx]
            for rank, result in enumerate(results):
                doc_key = result.content[:200]
                rrf_score = weight / (k + rank + 1)

                if doc_key in scores:
                    scores[doc_key] += rrf_score
                else:
                    scores[doc_key] = rrf_score
                    content_map[doc_key] = result

        sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        fused_results = []
        for key in sorted_keys:
            original = content_map[key]
            fused_results.append(RetrievalResult(
                content=original.content,
                score=scores[key],
                metadata=original.metadata,
            ))

        return fused_results

    async def retrieve_with_rerank(
        self,
        query: str,
        collection: str,
        limit: int = 5,
        initial_limit: int = 20,
        filters: dict = None,
    ) -> List[RetrievalResult]:
        """Retrieve and rerank using hybrid scoring."""
        initial_results = await self.retrieve(query, collection, initial_limit, filters)

        query_words = set(query.lower().split())
        scored = []

        for r in initial_results:
            content_words = set(r.content.lower().split())
            keyword_overlap = len(query_words & content_words) / max(len(query_words), 1)

            length_bonus = min(len(r.content) / 500, 1.0) * 0.05
            combined_score = r.score * 0.65 + keyword_overlap * 0.25 + length_bonus + 0.05
            scored.append((combined_score, r))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            RetrievalResult(
                content=r.content,
                score=score,
                metadata=r.metadata,
            )
            for score, r in scored[:limit]
        ]

    async def _ensure_bm25_index(self, collection: str, filters: dict = None) -> None:
        """Load all documents from vector DB into BM25 index."""
        if self._indexed_collection == collection:
            return

        all_docs = await self.vectordb.get(collection, limit=10000, filters=filters)
        documents = []
        for doc in all_docs:
            payload = doc.payload if hasattr(doc, 'payload') else doc
            documents.append(payload)

        self._bm25.index(documents)
        self._indexed_collection = collection
