import pytest
from pathlib import Path

from agentic_swarm.rag.sources.file import FileSource


class TestFileSource:
    @pytest.mark.asyncio
    async def test_load_single_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello, world!", encoding="utf-8")

        source = FileSource(path=str(f))
        docs = await source.load()

        assert len(docs) == 1
        assert docs[0].content == "Hello, world!"
        assert docs[0].source == str(f)
        assert docs[0].metadata["filename"] == "test.txt"
        assert docs[0].metadata["size"] == f.stat().st_size

    @pytest.mark.asyncio
    async def test_load_directory(self, tmp_path):
        (tmp_path / "a.txt").write_text("file a", encoding="utf-8")
        (tmp_path / "b.md").write_text("file b", encoding="utf-8")
        (tmp_path / "c.py").write_text("file c", encoding="utf-8")

        source = FileSource(path=str(tmp_path))
        docs = await source.load()

        assert len(docs) == 3
        contents = {d.content for d in docs}
        assert "file a" in contents
        assert "file b" in contents
        assert "file c" in contents

    @pytest.mark.asyncio
    async def test_load_directory_recursive(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "top.txt").write_text("top level", encoding="utf-8")
        (sub / "nested.txt").write_text("nested", encoding="utf-8")

        source = FileSource(path=str(tmp_path), recursive=True)
        docs = await source.load()

        assert len(docs) == 2
        contents = {d.content for d in docs}
        assert "top level" in contents
        assert "nested" in contents

    @pytest.mark.asyncio
    async def test_load_directory_non_recursive(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (tmp_path / "top.txt").write_text("top level", encoding="utf-8")
        (sub / "nested.txt").write_text("nested", encoding="utf-8")

        source = FileSource(path=str(tmp_path), recursive=False)
        docs = await source.load()

        assert len(docs) == 1
        assert docs[0].content == "top level"

    @pytest.mark.asyncio
    async def test_respects_extensions_filter(self, tmp_path):
        (tmp_path / "include.py").write_text("python code", encoding="utf-8")
        (tmp_path / "include.txt").write_text("text content", encoding="utf-8")
        (tmp_path / "exclude.csv").write_text("a,b,c", encoding="utf-8")
        (tmp_path / "exclude.bin").write_text("binary", encoding="utf-8")

        source = FileSource(path=str(tmp_path), extensions=[".py", ".txt"])
        docs = await source.load()

        assert len(docs) == 2
        filenames = {d.metadata["filename"] for d in docs}
        assert "include.py" in filenames
        assert "include.txt" in filenames
        assert "exclude.csv" not in filenames

    @pytest.mark.asyncio
    async def test_empty_directory(self, tmp_path):
        source = FileSource(path=str(tmp_path))
        docs = await source.load()
        assert docs == []

    @pytest.mark.asyncio
    async def test_metadata_has_relative_path(self, tmp_path):
        sub = tmp_path / "docs"
        sub.mkdir()
        (sub / "readme.md").write_text("content", encoding="utf-8")

        source = FileSource(path=str(tmp_path))
        docs = await source.load()

        assert len(docs) == 1
        assert docs[0].metadata["relative_path"] == "docs/readme.md"

    @pytest.mark.asyncio
    async def test_source_type(self):
        source = FileSource(path="/tmp/fake")
        assert source.source_type == "file"

    @pytest.mark.asyncio
    async def test_skips_unreadable_files(self, tmp_path):
        f = tmp_path / "binary.txt"
        f.write_bytes(b'\x80\x81\x82\x83' * 100)

        (tmp_path / "good.txt").write_text("readable", encoding="utf-8")

        source = FileSource(path=str(tmp_path), extensions=[".txt"])
        docs = await source.load()

        readable_docs = [d for d in docs if d.content == "readable"]
        assert len(readable_docs) == 1
