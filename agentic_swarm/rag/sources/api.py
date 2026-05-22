"""REST API RAG data source."""

from collections.abc import AsyncIterator
from typing import Any

from .base import BaseSource, Document


class APISource(BaseSource):
    """Load documents from REST API endpoints."""

    def __init__(
        self,
        endpoints: list[dict[str, Any]],
        headers: dict[str, str] | None = None,
        timeout: int = 30,
    ):
        """
        Args:
            endpoints: List of endpoint configs, each with:
                - url (str): The API endpoint URL
                - method (str): HTTP method (default: GET)
                - body (dict): Request body for POST/PUT
                - content_field (str): JSON field containing the text content (default: "content")
                - source_field (str): JSON field for source identifier (default: "id")
            headers: Default headers for all requests
            timeout: Request timeout in seconds
        """
        self._endpoints = endpoints
        self._headers = headers or {}
        self._timeout = timeout

    async def load(self) -> list[Document]:
        docs = []
        async for doc in self.load_lazy():
            docs.append(doc)
        return docs

    async def load_lazy(self) -> AsyncIterator[Document]:
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx package required for APISource") from None

        async with httpx.AsyncClient(timeout=self._timeout, headers=self._headers) as client:
            for endpoint in self._endpoints:
                url = endpoint["url"]
                method = endpoint.get("method", "GET").upper()
                body = endpoint.get("body")
                content_field = endpoint.get("content_field", "content")
                source_field = endpoint.get("source_field", "id")

                try:
                    if method == "GET":
                        response = await client.get(url)
                    elif method == "POST":
                        response = await client.post(url, json=body)
                    else:
                        response = await client.request(method, url, json=body)

                    response.raise_for_status()
                    data = response.json()

                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        content = self._extract_field(item, content_field)
                        if not content:
                            continue
                        source_id = self._extract_field(item, source_field) or url

                        yield Document(
                            content=str(content),
                            source=f"api://{url}#{source_id}",
                            metadata={"url": url, "method": method, "source_id": source_id},
                        )
                except (httpx.HTTPError, ValueError, KeyError):
                    continue

    @staticmethod
    def _extract_field(data: dict, field: str) -> Any:
        """Extract a possibly nested field using dot notation."""
        parts = field.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    @property
    def source_type(self) -> str:
        return "api"
