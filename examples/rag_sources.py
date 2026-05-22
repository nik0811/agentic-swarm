"""
Example: RAG with Multiple Sources

Demonstrates ingesting documents from files, web URLs, and GitHub repos.
"""

import asyncio
from agentic_swarm.rag import RAGPipeline, Chunker, Retriever
from agentic_swarm.rag.sources import FileSource, WebSource, GitHubSource
from agentic_swarm.vectordb import InMemoryVectorDB
from agentic_swarm.rag.embedder import MockEmbedder


async def main():
    vectordb = InMemoryVectorDB()
    embedder = MockEmbedder(dimension=128)
    chunker = Chunker(strategy="recursive", chunk_size=512, chunk_overlap=50)
    retriever = Retriever(vectordb=vectordb, embedder=embedder)

    pipeline = RAGPipeline(
        vectordb=vectordb,
        embedder=embedder,
        chunker=chunker,
        retriever=retriever,
    )

    print("--- Ingesting from Local Files ---")
    file_source = FileSource("./docs/", extensions=[".md", ".txt"], recursive=True)
    try:
        await pipeline.ingest_source(file_source, collection="docs")
        print("  Ingested local docs")
    except Exception as e:
        print(f"  Skipped (no ./docs/ directory): {e}")

    print("\n--- Ingesting from Web ---")
    web_source = WebSource(urls=["https://httpbin.org/html"])
    try:
        await pipeline.ingest_source(web_source, collection="web")
        print("  Ingested web content")
    except Exception as e:
        print(f"  Skipped: {e}")

    print("\n--- Ingesting from GitHub ---")
    github_source = GitHubSource(
        repo="nik0811/agentic-swarm",
        branch="main",
        path="agentic_swarm/",
        extensions=[".py"],
    )
    try:
        await pipeline.ingest_source(github_source, collection="source_code")
        print("  Ingested GitHub source code")
    except Exception as e:
        print(f"  Skipped (needs GITHUB_TOKEN): {e}")

    print("\n--- Querying ---")
    result = await pipeline.query("How does the agent work?", collection="docs")
    if result.chunks:
        print(f"  Found {len(result.chunks)} relevant chunks")
        print(f"  Context: {result.context[:200]}...")
    else:
        print("  No results (ingest sources first)")


if __name__ == "__main__":
    asyncio.run(main())
