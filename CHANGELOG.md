# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-05-22

### Added

#### Core Foundation (Week 1)
- Base `Agent` class with lifecycle management
- `@tool` decorator for creating tools with auto-generated schemas
- `Tool` class with OpenAI function calling format support
- `ToolRegistry` for managing tools
- Core types: `AgentState`, `MessageType`, `TaskComplexity`, `AgentSpec`, `Message`
- Custom exceptions: `AgentError`, `ToolError`, `MemoryError`, `LLMError`
- `CoreMemory` - Immutable agent identity storage
- `RecallMemory` - Sliding window working context

#### LLM Router & Intelligence (Week 2)
- `BaseLLMProvider` interface for LLM providers
- `OpenAIProvider` - OpenAI API integration
- `AnthropicProvider` - Anthropic Claude API integration
- `TaskClassifier` - Classify task complexity (trivial/moderate/complex/expert)
- `TokenManager` - Token counting and budget management
- `ContextCompressor` - Compress context to fit token budgets
- `LLMRouter` - Smart routing to optimal model based on task complexity

#### RAG Pipeline & Archival Memory (Week 3)
- `BaseVectorDB` interface for vector databases
- `QdrantClient` - Qdrant vector database integration
- `InMemoryVectorDB` - In-memory vector DB for testing
- `Embedder` - OpenAI embeddings generation
- `MockEmbedder` - Mock embedder for testing
- `Chunker` - Document chunking (fixed, recursive, semantic strategies)
- `Retriever` - Vector similarity search with reranking
- `RAGPipeline` - End-to-end document ingestion and retrieval
- `ArchivalMemory` - Long-term vector-indexed memory
- `MemoryController` - Unified interface for all memory types

#### Swarm, Lifecycle & Compliance (Week 4)
- `Swarm` - Multi-agent orchestrator with sequential/parallel/adaptive strategies
- `Supervisor` - Agent health monitoring and lifecycle management
- `Healer` - Automatic recovery from agent failures
- `Spawner` - Dynamic sub-agent creation with depth limits
- `Sandbox` - Isolated execution environment with timeouts
- `AuditLogger` - Immutable audit logging for SOC2 compliance
- `Encryption` - AES-256 encryption at rest
- `DataIsolation` - Per-agent data namespacing
- `RBACManager` - Role-based access control
- Built-in tools: agent management, memory, filesystem, code execution, web

### Examples
- `simple_agent.py` - Basic agent with tools
- `multi_agent_swarm.py` - Multi-agent coordination
- `sub_agent_spawning.py` - Dynamic agent creation
- `memory_usage.py` - Tiered memory system
- `rag_pipeline.py` - Document retrieval

### Tests
- 111 tests covering all components
- Full test coverage for core functionality
