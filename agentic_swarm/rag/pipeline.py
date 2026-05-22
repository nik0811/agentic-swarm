import os
import uuid

from pydantic import BaseModel

from ..vectordb.base import BaseVectorDB
from .chunker import Chunker
from .embedder import Embedder
from .query_engine import QueryEngine
from .reranker import Reranker
from .retriever import RetrievalResult, Retriever
from .sources.base import BaseSource


class RAGResult(BaseModel):
    context: str
    sources: list[dict] = []
    num_chunks: int = 0
    chunks: list[dict] = []


class RAGPipeline:
    """End-to-end RAG pipeline for document ingestion and retrieval.

    Supports:
    - Multi-source ingestion (files, web, GitHub, API)
    - Multiple chunking strategies (fixed, recursive, semantic, code-aware)
    - Dense, sparse, and hybrid retrieval with RRF fusion
    - Cross-encoder reranking
    - Query expansion and HyDE
    - Context assembly with source attribution
    """

    def __init__(
        self,
        vectordb: BaseVectorDB,
        embedder: Embedder = None,
        chunker: Chunker = None,
        retriever: Retriever = None,
        reranker: Reranker = None,
        llm_provider=None,
        default_collection: str = "documents",
        retrieval_strategy: str = "dense",
        enable_query_expansion: bool = False,
        enable_hyde: bool = False,
    ):
        self.vectordb = vectordb
        self.embedder = embedder or Embedder()
        self.chunker = chunker or Chunker()
        self.retriever = retriever or Retriever(
            vectordb, self.embedder, strategy=retrieval_strategy
        )
        self.reranker = reranker
        self.llm_provider = llm_provider
        self.default_collection = default_collection

        self.query_engine = QueryEngine(
            retriever=self.retriever,
            llm_provider=llm_provider,
            reranker=reranker,
            enable_query_expansion=enable_query_expansion,
            enable_hyde=enable_hyde,
        )

    async def ingest(
        self,
        text: str,
        collection: str = None,
        metadata: dict = None,
    ) -> int:
        """Ingest text into the vector database."""
        collection = collection or self.default_collection

        await self.vectordb.create_collection(collection, self.embedder.dimensions)

        chunks = self.chunker.chunk(text, metadata)

        if not chunks:
            return 0

        ids = [str(uuid.uuid4()) for _ in chunks]
        texts = [c.content for c in chunks]
        vectors = await self.embedder.embed_batch(texts)

        payloads = []
        for chunk in chunks:
            payload = {
                "content": chunk.content,
                "index": chunk.index,
                "token_count": chunk.token_count,
                **(chunk.metadata or {}),
                **(metadata or {}),
            }
            payloads.append(payload)

        await self.vectordb.upsert(collection, ids, vectors, payloads)

        return len(chunks)

    async def ingest_file(
        self,
        path: str,
        collection: str = None,
    ) -> int:
        """Ingest a file into the vector database."""
        with open(path, encoding="utf-8") as f:
            text = f.read()

        file_ext = os.path.splitext(path)[1]
        chunker = self.chunker

        if file_ext in (".py", ".js", ".ts", ".go", ".rs", ".java"):
            chunker = Chunker(
                strategy="code", chunk_size=self.chunker.chunk_size, overlap=self.chunker.overlap
            )

        original_chunker = self.chunker
        self.chunker = chunker
        try:
            result = await self.ingest(
                text,
                collection=collection,
                metadata={
                    "source": path,
                    "filename": os.path.basename(path),
                    "extension": file_ext,
                },
            )
        finally:
            self.chunker = original_chunker

        return result

    async def ingest_directory(
        self,
        path: str,
        collection: str = None,
        extensions: list[str] = None,
    ) -> int:
        """Ingest all files in a directory."""
        extensions = extensions or [
            ".txt",
            ".md",
            ".py",
            ".js",
            ".ts",
            ".go",
            ".rs",
            ".java",
            ".html",
        ]
        total_chunks = 0

        for root, _, files in os.walk(path):
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    try:
                        chunks = await self.ingest_file(file_path, collection)
                        total_chunks += chunks
                    except Exception:
                        continue

        return total_chunks

    async def ingest_source(
        self,
        source: BaseSource,
        collection: str = None,
    ) -> int:
        """Ingest from a data source (file, web, GitHub, API)."""
        collection = collection or self.default_collection
        total_chunks = 0

        documents = await source.load()
        for doc in documents:
            metadata = {"source": doc.source, "source_type": source.source_type, **doc.metadata}
            chunks = await self.ingest(doc.content, collection=collection, metadata=metadata)
            total_chunks += chunks

        return total_chunks

    async def query(
        self,
        question: str,
        collection: str = None,
        limit: int = 5,
        filters: dict = None,
        use_query_engine: bool = False,
    ) -> RAGResult:
        """Query the RAG pipeline.

        Args:
            question: The query string
            collection: Vector DB collection to search
            limit: Max chunks to return
            filters: Metadata filters for retrieval
            use_query_engine: If True, uses full query engine with expansion/HyDE/LLM answer
        """
        collection = collection or self.default_collection

        if use_query_engine and self.llm_provider:
            result = await self.query_engine.query(
                question=question,
                collection=collection,
                filter_metadata=filters,
            )
            return RAGResult(
                context=result.answer,
                sources=result.sources,
                num_chunks=len(result.sources),
                chunks=[
                    {"content": s.get("content_preview", ""), "score": s.get("score", 0)}
                    for s in result.sources
                ],
            )

        results = await self.retriever.retrieve_with_rerank(
            query=question,
            collection=collection,
            limit=limit,
            filters=filters,
        )

        if self.reranker and len(results) > 0:
            reranked = await self.reranker.rerank(
                query=question,
                results=[
                    {"content": r.content, "score": r.score, "metadata": r.metadata}
                    for r in results
                ],
                top_k=limit,
            )
            results = [
                RetrievalResult(content=rr.content, score=rr.reranked_score, metadata=rr.metadata)
                for rr in reranked
            ]

        context_parts = []
        sources = []
        chunks = []

        for i, result in enumerate(results):
            source_info = {
                "index": i,
                "score": result.score,
                "source": result.metadata.get("source", "unknown"),
            }
            sources.append(source_info)
            chunks.append(
                {"content": result.content, "score": result.score, "metadata": result.metadata}
            )

            source_label = result.metadata.get("source", f"Source {i + 1}")
            context_parts.append(f"[{source_label}]\n{result.content}")

        context = "\n\n".join(context_parts)

        return RAGResult(
            context=context,
            sources=sources,
            num_chunks=len(results),
            chunks=chunks,
        )

    async def delete_collection(self, collection: str = None) -> None:
        """Delete a collection."""
        collection = collection or self.default_collection
        await self.vectordb.delete_collection(collection)

    async def get_stats(self, collection: str = None) -> dict:
        """Get pipeline statistics."""
        collection = collection or self.default_collection
        return {
            "collection": collection,
            "embedder_model": self.embedder.model,
            "embedder_dimensions": self.embedder.dimensions,
            "chunker_strategy": self.chunker.strategy,
            "chunk_size": self.chunker.chunk_size,
            "retrieval_strategy": self.retriever.strategy,
            "reranker_enabled": self.reranker is not None,
            "llm_enabled": self.llm_provider is not None,
        }
