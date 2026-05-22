"""GitHub repository RAG data source."""

from collections.abc import AsyncIterator

from .base import BaseSource, Document


class GitHubSource(BaseSource):
    """Load documents from a GitHub repository."""

    def __init__(
        self,
        repo: str,
        branch: str = "main",
        path: str = "",
        extensions: list[str] = None,
        token: str = None,
    ):
        self._repo = repo
        self._branch = branch
        self._path = path
        self._extensions = extensions or [".md", ".txt", ".py", ".js", ".ts"]
        self._token = token

    async def load(self) -> list[Document]:
        docs = []
        async for doc in self.load_lazy():
            docs.append(doc)
        return docs

    async def load_lazy(self) -> AsyncIterator[Document]:
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx package required for GitHubSource") from None

        headers = {"Accept": "application/vnd.github.v3+json"}
        if self._token:
            headers["Authorization"] = f"token {self._token}"

        base_api = f"https://api.github.com/repos/{self._repo}"
        tree_url = f"{base_api}/git/trees/{self._branch}?recursive=1"

        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            resp = await client.get(tree_url)
            resp.raise_for_status()
            tree = resp.json()

            for item in tree.get("tree", []):
                if item["type"] != "blob":
                    continue
                filepath = item["path"]

                if self._path and not filepath.startswith(self._path):
                    continue

                ext = "." + filepath.rsplit(".", 1)[-1] if "." in filepath else ""
                if ext not in self._extensions:
                    continue

                raw_url = (
                    f"https://raw.githubusercontent.com/{self._repo}/{self._branch}/{filepath}"
                )
                try:
                    file_resp = await client.get(raw_url)
                    file_resp.raise_for_status()
                    yield Document(
                        content=file_resp.text,
                        source=f"github://{self._repo}/{filepath}",
                        metadata={
                            "repo": self._repo,
                            "branch": self._branch,
                            "path": filepath,
                            "sha": item.get("sha", ""),
                        },
                    )
                except httpx.HTTPError:
                    continue

    @property
    def source_type(self) -> str:
        return "github"
