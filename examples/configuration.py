"""
Example: SDK Configuration

Demonstrates how to override all hardcoded defaults via SDKConfig.
Every configurable value in the SDK can be changed here.
"""

from agentic_swarm.core.config import (
    SDKConfig, LLMConfig, MemoryConfig, AgentConfig,
    LifecycleConfig, RAGConfig, CompressorConfig,
    ClassifierConfig, SandboxConfig, VectorDBConfig,
    ComplianceConfig, ToolsConfig,
    get_config, set_config, reset_config,
)


def main():
    print("=== Default Configuration ===")
    config = SDKConfig()
    print(f"  llm.default_model: {config.llm.default_model}")
    print(f"  llm.default_temperature: {config.llm.default_temperature}")
    print(f"  llm.default_max_tokens: {config.llm.default_max_tokens}")
    print(f"  llm.default_strategy: {config.llm.default_strategy}")
    print(f"  agent.max_iterations: {config.agent.max_iterations}")
    print(f"  memory.recall_max_size: {config.memory.recall_max_size}")
    print(f"  memory.recall_max_tokens: {config.memory.recall_max_tokens}")
    print(f"  rag.chunk_size: {config.rag.chunk_size}")
    print(f"  rag.retrieval_strategy: {config.rag.retrieval_strategy}")
    print(f"  lifecycle.spawner_max_depth: {config.lifecycle.spawner_max_depth}")
    print(f"  lifecycle.spawner_max_children: {config.lifecycle.spawner_max_children}")
    print(f"  sandbox.timeout_seconds: {config.sandbox.timeout_seconds}")

    print("\n=== Custom Configuration ===")
    custom = SDKConfig(
        llm=LLMConfig(
            default_model="claude-sonnet-4-20250514",
            default_temperature=0.9,
            default_max_tokens=8192,
            default_strategy="quality_optimized",
        ),
        agent=AgentConfig(
            max_iterations=20,
            default_timeout=600,
        ),
        memory=MemoryConfig(
            recall_max_size=200,
            recall_max_tokens=16000,
        ),
        lifecycle=LifecycleConfig(
            supervisor_max_errors=5,
            healer_max_retries=5,
            spawner_max_depth=5,
            spawner_max_children=20,
        ),
        rag=RAGConfig(
            chunk_size=1024,
            chunk_overlap=100,
            default_chunk_strategy="semantic",
            retrieval_strategy="hybrid",
            embedding_model="text-embedding-3-large",
            embedding_dimensions=3072,
        ),
        sandbox=SandboxConfig(
            timeout_seconds=120,
            memory_limit_mb=1024,
        ),
    )
    print(f"  llm.default_model: {custom.llm.default_model}")
    print(f"  llm.default_temperature: {custom.llm.default_temperature}")
    print(f"  llm.default_max_tokens: {custom.llm.default_max_tokens}")
    print(f"  agent.max_iterations: {custom.agent.max_iterations}")
    print(f"  memory.recall_max_size: {custom.memory.recall_max_size}")
    print(f"  rag.chunk_size: {custom.rag.chunk_size}")
    print(f"  rag.retrieval_strategy: {custom.rag.retrieval_strategy}")
    print(f"  lifecycle.spawner_max_depth: {custom.lifecycle.spawner_max_depth}")
    print(f"  sandbox.timeout_seconds: {custom.sandbox.timeout_seconds}")

    print("\n=== Global Config (SDK-wide override) ===")
    set_config(SDKConfig(
        llm=LLMConfig(default_temperature=0.3),
        agent=AgentConfig(max_iterations=15),
    ))
    global_conf = get_config()
    print(f"  Global temperature: {global_conf.llm.default_temperature}")
    print(f"  Global max_iterations: {global_conf.agent.max_iterations}")

    reset_config()
    print(f"  After reset, temperature: {get_config().llm.default_temperature}")

    print("\n=== All Configurable Sections ===")
    sections = [
        ("llm", "Model, temperature, tokens, strategy, provider, encoding"),
        ("classifier", "Word thresholds, keywords for trivial/moderate/complex/expert"),
        ("memory", "Recall size/tokens, archival collection, core version"),
        ("agent", "Max iterations, default timeout"),
        ("lifecycle", "Supervisor interval/errors, healer retries/backoff, spawner limits"),
        ("sandbox", "CPU/memory limits, timeout, network access"),
        ("rag", "Chunk strategy/size/overlap, embedding model/dim, retrieval, rerank"),
        ("compressor", "Preserve recent, summary length, facts limit"),
        ("vectordb", "Qdrant host/port/grpc"),
        ("compliance", "Audit limit, encryption iterations/key/salt length"),
        ("tools", "Shell timeout, web fetch timeout/chars, search results, memory limits"),
    ]
    for name, desc in sections:
        print(f"  {name:12s} → {desc}")


if __name__ == "__main__":
    main()
