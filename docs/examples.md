# Examples

## Available Examples

| Example | Description |
|---------|-------------|
| [`simple_agent.py`](../examples/simple_agent.py) | Basic agent with tools |
| [`multi_agent_swarm.py`](../examples/multi_agent_swarm.py) | Multi-agent parallel and sequential coordination |
| [`sub_agent_spawning.py`](../examples/sub_agent_spawning.py) | Dynamic sub-agent creation at runtime |
| [`memory_usage.py`](../examples/memory_usage.py) | All three memory tiers in action |
| [`rag_pipeline.py`](../examples/rag_pipeline.py) | Document ingestion and retrieval |
| [`full_showcase.py`](../examples/full_showcase.py) | Complete SDK showcase with all providers |
| [`full_showcase_bedrock.py`](../examples/full_showcase_bedrock.py) | Full SDK showcase for AWS Bedrock |
| [`immortal_swarm_bedrock.py`](../examples/immortal_swarm_bedrock.py) | Immortal swarm with auto-healing |
| [`agent_collaboration_bedrock.py`](../examples/agent_collaboration_bedrock.py) | Parent-child agent collaboration |
| [`auto_tools.py`](../examples/auto_tools.py) | Automatic tool discovery and retry |
| [`custom_tools.py`](../examples/custom_tools.py) | Creating and registering custom tools |
| [`communication.py`](../examples/communication.py) | Message bus and channels |
| [`storage_example.py`](../examples/storage_example.py) | Persistent state with local and Redis |
| [`rag_sources.py`](../examples/rag_sources.py) | Ingest from GitHub, web, and files |
| [`rag_memory_context.py`](../examples/rag_memory_context.py) | RAG + Memory + Context combined |
| [`vectordb_persistent.py`](../examples/vectordb_persistent.py) | Vector database + persistent storage |
| [`sandbox_isolation.py`](../examples/sandbox_isolation.py) | Sandbox execution + data isolation |
| [`never_forget_memory.py`](../examples/never_forget_memory.py) | Never-forget memory system |
| [`iii_integration.py`](../examples/iii_integration.py) | Run agents as iii workers |

## Running the Full Showcase

```bash
# Run with OpenAI (default)
python examples/full_showcase.py --provider openai

# Run with Anthropic
python examples/full_showcase.py --provider anthropic --model claude-3-5-sonnet-latest

# Run with AWS Bedrock
python examples/full_showcase.py --provider bedrock --model us.anthropic.claude-sonnet-4-6

# Run with Groq (fast inference)
python examples/full_showcase.py --provider groq --model llama-3.1-70b-versatile

# Run with Ollama (local)
python examples/full_showcase.py --provider ollama --model llama3.2

# Run with Google Gemini
python examples/full_showcase.py --provider gemini --model gemini-1.5-pro

# Run in demo mode (no LLM calls)
python examples/full_showcase.py --skip-llm
```

## Features Demonstrated

1. SDKConfig - Custom configuration
2. LLM Providers - All 7 supported providers
3. Prompt Cache - Response caching
4. Agent Spawning - Parent/child agents
5. Tool Calling - Custom tools
6. Memory - Core + Recall + Archival
7. RAG Pipeline - Document ingestion & retrieval
8. Communication - Message bus
9. Swarm - Parallel execution
10. Lifecycle - Supervisor, Healer, Sandbox
11. Security Features - Audit, Encryption, Access Control
12. Storage - Persistent local storage
13. Token Management - Budget & compression
14. Utilities - Crypto, validation, serialization
15. Registry - Agent tracking
16. Auto Tool Discovery - Dynamic tool loading
17. Sandbox & Data Isolation - Resource limits
18. Never-Forget Memory - Persistent memory
19. iii Integration - Service composition
