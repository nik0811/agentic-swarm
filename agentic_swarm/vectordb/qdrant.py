from typing import List, Optional
import uuid

from .base import BaseVectorDB, VectorSearchResult


class QdrantClient(BaseVectorDB):
    """Qdrant vector database client."""
    
    def __init__(
        self,
        url: str = "localhost",
        port: int = 6333,
        api_key: str = None,
        prefer_grpc: bool = False,
    ):
        self.url = url
        self.port = port
        self.api_key = api_key
        self.prefer_grpc = prefer_grpc
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                from qdrant_client import QdrantClient as QC
                from qdrant_client.http import models
                self._models = models
                
                if self.url.startswith("http"):
                    self._client = QC(url=self.url, api_key=self.api_key, prefer_grpc=self.prefer_grpc)
                else:
                    self._client = QC(host=self.url, port=self.port, api_key=self.api_key, prefer_grpc=self.prefer_grpc)
            except ImportError:
                raise ImportError("qdrant-client package not installed. Run: pip install qdrant-client")
        return self._client
    
    async def create_collection(self, name: str, vector_size: int) -> None:
        """Create a new collection."""
        client = self._get_client()
        
        collections = client.get_collections().collections
        if any(c.name == name for c in collections):
            return
        
        client.create_collection(
            collection_name=name,
            vectors_config=self._models.VectorParams(
                size=vector_size,
                distance=self._models.Distance.COSINE,
            ),
        )
    
    async def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        client = self._get_client()
        client.delete_collection(collection_name=name)
    
    async def upsert(
        self,
        collection: str,
        ids: List[str],
        vectors: List[List[float]],
        payloads: List[dict] = None,
    ) -> None:
        """Insert or update vectors."""
        client = self._get_client()
        
        points = []
        for i, (id_, vector) in enumerate(zip(ids, vectors)):
            payload = payloads[i] if payloads else {}
            points.append(self._models.PointStruct(
                id=id_,
                vector=vector,
                payload=payload,
            ))
        
        client.upsert(collection_name=collection, points=points)
    
    async def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filters: dict = None,
    ) -> List[VectorSearchResult]:
        """Search for similar vectors."""
        client = self._get_client()
        
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, dict) and "$contains" in value:
                    conditions.append(self._models.FieldCondition(
                        key=key,
                        match=self._models.MatchText(text=value["$contains"]),
                    ))
                else:
                    conditions.append(self._models.FieldCondition(
                        key=key,
                        match=self._models.MatchValue(value=value),
                    ))
            query_filter = self._models.Filter(must=conditions)
        
        results = client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
        )
        
        return [
            VectorSearchResult(
                id=str(r.id),
                score=r.score,
                payload=r.payload or {},
                vector=r.vector,
            )
            for r in results
        ]
    
    async def delete(self, collection: str, ids: List[str]) -> None:
        """Delete vectors by ID."""
        client = self._get_client()
        client.delete(
            collection_name=collection,
            points_selector=self._models.PointIdsList(points=ids),
        )
    
    async def get(self, collection: str, ids: List[str]) -> List[dict]:
        """Get vectors by ID."""
        client = self._get_client()
        results = client.retrieve(collection_name=collection, ids=ids)
        return [{"id": str(r.id), "payload": r.payload, "vector": r.vector} for r in results]


class InMemoryVectorDB(BaseVectorDB):
    """In-memory vector database for testing."""
    
    def __init__(self):
        self._collections: dict[str, dict] = {}
    
    async def create_collection(self, name: str, vector_size: int) -> None:
        if name not in self._collections:
            self._collections[name] = {"vector_size": vector_size, "points": {}}
    
    async def delete_collection(self, name: str) -> None:
        self._collections.pop(name, None)
    
    async def upsert(
        self,
        collection: str,
        ids: List[str],
        vectors: List[List[float]],
        payloads: List[dict] = None,
    ) -> None:
        if collection not in self._collections:
            raise ValueError(f"Collection {collection} does not exist")
        
        for i, (id_, vector) in enumerate(zip(ids, vectors)):
            payload = payloads[i] if payloads else {}
            self._collections[collection]["points"][id_] = {
                "vector": vector,
                "payload": payload,
            }
    
    async def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        filters: dict = None,
    ) -> List[VectorSearchResult]:
        if collection not in self._collections:
            return []
        
        results = []
        for id_, data in self._collections[collection]["points"].items():
            if filters:
                match = True
                for key, value in filters.items():
                    if key not in data["payload"] or data["payload"][key] != value:
                        match = False
                        break
                if not match:
                    continue
            
            score = self._cosine_similarity(query_vector, data["vector"])
            results.append(VectorSearchResult(
                id=id_,
                score=score,
                payload=data["payload"],
                vector=data["vector"],
            ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    async def delete(self, collection: str, ids: List[str]) -> None:
        if collection in self._collections:
            for id_ in ids:
                self._collections[collection]["points"].pop(id_, None)
    
    async def get(self, collection: str, ids: List[str]) -> List[dict]:
        if collection not in self._collections:
            return []
        
        results = []
        for id_ in ids:
            if id_ in self._collections[collection]["points"]:
                data = self._collections[collection]["points"][id_]
                results.append({"id": id_, "payload": data["payload"], "vector": data["vector"]})
        return results
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        import math
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0
        return dot / (norm_a * norm_b)
