from typing import List, Literal, Optional
from pydantic import BaseModel

from ..vectordb.base import BaseVectorDB, VectorSearchResult
from .embedder import Embedder


class RetrievalResult(BaseModel):
    content: str
    score: float
    metadata: dict = {}


class Retriever:
    """Retrieve relevant chunks from vector DB."""
    
    def __init__(
        self,
        vectordb: BaseVectorDB,
        embedder: Embedder,
        strategy: Literal["dense", "sparse", "hybrid"] = "dense",
    ):
        self.vectordb = vectordb
        self.embedder = embedder
        self.strategy = strategy
    
    async def retrieve(
        self,
        query: str,
        collection: str,
        limit: int = 5,
        filters: dict = None,
    ) -> List[RetrievalResult]:
        """Retrieve relevant chunks."""
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
        """Dense retrieval using embeddings."""
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
        """Sparse retrieval using keyword matching (BM25-like)."""
        return await self._retrieve_dense(query, collection, limit, filters)
    
    async def _retrieve_hybrid(
        self,
        query: str,
        collection: str,
        limit: int,
        filters: dict = None,
    ) -> List[RetrievalResult]:
        """Hybrid retrieval combining dense and sparse."""
        dense_results = await self._retrieve_dense(query, collection, limit * 2, filters)
        
        seen = set()
        unique_results = []
        for r in dense_results:
            key = r.content[:100]
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        return unique_results[:limit]
    
    async def retrieve_with_rerank(
        self,
        query: str,
        collection: str,
        limit: int = 5,
        initial_limit: int = 20,
        filters: dict = None,
    ) -> List[RetrievalResult]:
        """Retrieve and rerank results."""
        initial_results = await self.retrieve(query, collection, initial_limit, filters)
        
        query_words = set(query.lower().split())
        
        scored = []
        for r in initial_results:
            content_words = set(r.content.lower().split())
            keyword_score = len(query_words & content_words) / len(query_words) if query_words else 0
            combined_score = r.score * 0.7 + keyword_score * 0.3
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
