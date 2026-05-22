"""Web-based RAG data source."""

from collections.abc import AsyncIterator

from .base import BaseSource, Document


class WebSource(BaseSource):
    """Load documents from web URLs."""

    def __init__(self, urls: list[str], timeout: int = 30):
        self._urls = urls
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
            raise ImportError("httpx package required for WebSource") from None

        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            for url in self._urls:
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    content = response.text

                    if "text/html" in response.headers.get("content-type", ""):
                        content = self._strip_html(content)

                    yield Document(
                        content=content,
                        source=url,
                        metadata={
                            "url": url,
                            "status_code": response.status_code,
                            "content_type": response.headers.get("content-type", ""),
                        },
                    )
                except httpx.HTTPError:
                    continue

    @staticmethod
    def _strip_html(html: str) -> str:
        """Basic HTML tag stripping."""
        import re

        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @property
    def source_type(self) -> str:
        return "web"
