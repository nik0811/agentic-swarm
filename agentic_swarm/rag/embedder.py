import hashlib
import os


class Embedder:
    """Generate embeddings for text."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str = None,
        dimensions: int = 1536,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.dimensions = dimensions
        self._client = None
        self._cache: dict[str, list[float]] = {}

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai") from None
        return self._client

    def _cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        cache_key = self._cache_key(text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        client = self._get_client()
        response = client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.dimensions,
        )

        embedding = response.data[0].embedding
        self._cache[cache_key] = embedding
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        uncached = []
        uncached_indices = []
        results = [None] * len(texts)

        for i, text in enumerate(texts):
            cache_key = self._cache_key(text)
            if cache_key in self._cache:
                results[i] = self._cache[cache_key]
            else:
                uncached.append(text)
                uncached_indices.append(i)

        if uncached:
            client = self._get_client()
            response = client.embeddings.create(
                model=self.model,
                input=uncached,
                dimensions=self.dimensions,
            )

            for j, embedding_data in enumerate(response.data):
                idx = uncached_indices[j]
                embedding = embedding_data.embedding
                results[idx] = embedding
                self._cache[self._cache_key(uncached[j])] = embedding

        return results

    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding optimized for queries."""
        return await self.embed(query)

    def clear_cache(self):
        """Clear embedding cache."""
        self._cache.clear()


class MockEmbedder:
    """Mock embedder for testing without API calls."""

    def __init__(self, dimensions: int = 1536):
        self.dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        """Generate deterministic mock embedding based on text hash."""
        import hashlib

        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = []
        for i in range(self.dimensions):
            byte_idx = i % len(hash_bytes)
            embedding.append((hash_bytes[byte_idx] - 128) / 128.0)
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(text) for text in texts]

    async def embed_query(self, query: str) -> list[float]:
        return await self.embed(query)

    def clear_cache(self):
        pass
