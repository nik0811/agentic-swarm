from typing import List, Optional
from pydantic import BaseModel
import uuid
import os

from ..vectordb.base import BaseVectorDB
from .embedder import Embedder
from .chunker import Chunker, Chunk
from .retriever import Retriever, RetrievalResult


class RAGResult(BaseModel):
    context: str
    sources: List[dict] = []
    num_chunks: int = 0


class RAGPipeline:
    """End-to-end RAG pipeline for document ingestion and retrieval."""
    
    def __init__(
        self,
        vectordb: BaseVectorDB,
        embedder: Embedder = None,
        chunker: Chunker = None,
        default_collection: str = "documents",
    ):
        self.vectordb = vectordb
        self.embedder = embedder or Embedder()
        self.chunker = chunker or Chunker()
        self.retriever = Retriever(vectordb, self.embedder)
        self.default_collection = default_collection
    
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
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        
        return await self.ingest(
            text,
            collection=collection,
            metadata={"source": path, "filename": os.path.basename(path)},
        )
    
    async def ingest_directory(
        self,
        path: str,
        collection: str = None,
        extensions: List[str] = None,
    ) -> int:
        """Ingest all files in a directory."""
        extensions = extensions or [".txt", ".md", ".py", ".js", ".ts"]
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
    
    async def query(
        self,
        question: str,
        collection: str = None,
        limit: int = 5,
        filters: dict = None,
    ) -> RAGResult:
        """Query the RAG pipeline."""
        collection = collection or self.default_collection
        
        results = await self.retriever.retrieve_with_rerank(
            query=question,
            collection=collection,
            limit=limit,
            filters=filters,
        )
        
        context_parts = []
        sources = []
        
        for i, result in enumerate(results):
            source_info = {
                "index": i,
                "score": result.score,
                "source": result.metadata.get("source", "unknown"),
            }
            sources.append(source_info)
            
            source_label = result.metadata.get("source", f"Source {i+1}")
            context_parts.append(f"[{source_label}]\n{result.content}")
        
        context = "\n\n".join(context_parts)
        
        return RAGResult(
            context=context,
            sources=sources,
            num_chunks=len(results),
        )
    
    async def delete_collection(self, collection: str = None) -> None:
        """Delete a collection."""
        collection = collection or self.default_collection
        await self.vectordb.delete_collection(collection)
