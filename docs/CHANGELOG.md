# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-23

### 🎉 Initial Release

First public release of Agentic Swarm — a production-grade SDK for building immortal, self-healing multi-agent AI systems.

### Added

#### Core Agent System
- `Agent` class with ReAct execution pattern (Think → Act → Observe → Loop)
- `Swarm` orchestrator with parallel, sequential, and adaptive execution strategies
- `@tool` decorator for creating LLM-callable tools with auto-generated schemas
- Dynamic sub-agent spawning with depth and children limits
- Agent-to-agent messaging via `agent.send()`

#### LLM Providers (7 providers)
- `OpenAIProvider` — GPT-4o, GPT-4o-mini, o1, o1-mini
- `AnthropicProvider` — Claude Sonnet 4, Claude 3.5, Claude 3 Opus/Haiku
- `BedrockProvider` — AWS Bedrock (Claude, Llama, Titan, Mistral)
- `GeminiProvider` — Google Gemini 2.0 Flash, 1.5 Pro/Flash
- `GroqProvider` — Llama 3.3, Mixtral (fast inference)
- `OllamaProvider` — Local models via Ollama
- `VLLMProvider` — Self-hosted models via vLLM

#### Smart LLM Routing
- `LLMRouter` with pluggable routing strategies
- `CostOptimizedStrategy` — Minimize cost
- `SpeedOptimizedStrategy` — Minimize latency
- `QualityOptimizedStrategy` — Maximize quality
- `TaskClassifier` for automatic complexity detection
- Automatic fallback on provider failures

#### Memory System
- `CoreMemory` — Immutable agent identity (name, persona, capabilities)
- `RecallMemory` — Sliding window working context with auto-eviction
- `ArchivalMemory` — Vector-indexed long-term storage
- `MemoryController` — Unified interface with auto-archive and fact extraction
- Never-forget memory: compress, store, search, and inject memories across sessions

#### RAG Pipeline
- `RAGPipeline` — End-to-end document ingestion and retrieval
- `Chunker` — Fixed, recursive, semantic, and code-aware chunking strategies
- `Embedder` — OpenAI embeddings with MockEmbedder for testing
- `Retriever` — Dense, sparse (BM25), and hybrid (RRF fusion) retrieval
- `Reranker` — Cross-encoder, keyword, and LLM-based reranking
- `QueryEngine` — Query expansion and HyDE (Hypothetical Document Embedding)

#### RAG Sources
- `FileSource` — Local files and directories
- `WebSource` — Web URL scraping
- `GitHubSource` — GitHub repository files
- `APISource` — REST API endpoints

#### Vector Databases
- `InMemoryVectorDB` — Fast in-memory storage for development
- `QdrantClient` — Production-ready Qdrant integration

#### Lifecycle Management
- `Supervisor` — Health monitoring with configurable check intervals
- `Healer` — State snapshots and auto-recovery with exponential backoff
- `Spawner` — Dynamic sub-agent creation with depth/children limits
- `Sandbox` — Isolated execution with CPU, memory, and timeout limits

#### Security & Compliance
- `AuditLogger` — Immutable audit logging with tamper-proof checksums
- `Encryption` — AES-256 encryption at rest with key rotation
- `DataIsolation` — Namespace-based agent data isolation
- `AccessController` — Fine-grained RBAC with permission, tool, and model ACLs

#### Communication
- `MessageBus` — Pub/sub messaging between agents
- `Channel` — Bidirectional point-to-point channels
- `MessageRouter` — Unified routing for bus and channels
- Message types: TASK_DELEGATE, RESULT, STATUS_UPDATE, ERROR, HEARTBEAT

#### Storage
- `LocalStorage` — File-based JSON storage with TTL support
- `RedisStorage` — Distributed Redis backend for production

#### Token Management
- `TokenManager` — Token counting with tiktoken
- `ContextCompressor` — Context compression to fit token budgets
- `PromptCache` — SDK-level response caching
- `PrefixCache` — Provider-level prefix caching

#### Tool Discovery
- `ToolRegistry` — Global tool registry with semantic search
- `ToolSelector` — Automatic tool selection and retry on failure
- Auto-discovery via `auto_tools=True` parameter

#### Configuration
- `SDKConfig` — Centralized configuration for all SDK components
- Every hardcoded value can be overridden
- `set_config()`, `get_config()`, `reset_config()` functions

#### Utilities
- `crypto` — Hashing, ID generation, secure tokens
- `serialization` — JSON serialization with datetime support
- `validation` — Input validation helpers

#### Integrations
- `iii_bridge` — Run agents as iii workers for service composition

### Documentation
- Comprehensive README with quick start guide
- Full API reference in `docs/api-reference.md`
- Configuration guide in `docs/configuration.md`
- 19 working examples in `examples/`
- Architecture documentation in `ARCHITECTURE.md`

### Testing
- 364 unit and integration tests
- pytest + pytest-asyncio test suite
- Full test coverage for core components

### CI/CD
- GitHub Actions workflows for CI (test, lint, type-check, security)
- Automated release pipeline to PyPI
- Dependency review for PRs

---

## [Unreleased]

### Planned
- Agent-to-agent streaming
- Web UI dashboard for swarm monitoring
- Distributed multi-node swarms
- Plugin system for custom providers and tools
- OpenTelemetry tracing integration
