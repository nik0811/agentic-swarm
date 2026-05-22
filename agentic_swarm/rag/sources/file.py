"""File-based RAG data source."""

from collections.abc import AsyncIterator
from pathlib import Path

from .base import BaseSource, Document


class FileSource(BaseSource):
    """Load documents from local files or directories."""

    def __init__(self, path: str, extensions: list[str] = None, recursive: bool = True):
        self._path = Path(path)
        self._extensions = extensions or [".txt", ".md", ".py", ".js", ".ts", ".html", ".json"]
        self._recursive = recursive

    async def load(self) -> list[Document]:
        docs = []
        async for doc in self.load_lazy():
            docs.append(doc)
        return docs

    async def load_lazy(self) -> AsyncIterator[Document]:
        if self._path.is_file():
            content = self._read_file(self._path)
            if content is not None:
                yield Document(
                    content=content,
                    source=str(self._path),
                    metadata={"filename": self._path.name, "size": self._path.stat().st_size},
                )
        elif self._path.is_dir():
            pattern = "**/*" if self._recursive else "*"
            for filepath in self._path.glob(pattern):
                if filepath.is_file() and filepath.suffix in self._extensions:
                    content = self._read_file(filepath)
                    if content is not None:
                        yield Document(
                            content=content,
                            source=str(filepath),
                            metadata={
                                "filename": filepath.name,
                                "relative_path": str(filepath.relative_to(self._path)),
                                "size": filepath.stat().st_size,
                            },
                        )

    def _read_file(self, path: Path) -> str | None:
        try:
            return path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            return None

    @property
    def source_type(self) -> str:
        return "file"
