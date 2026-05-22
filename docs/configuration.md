# Configuration

Every hardcoded value in the SDK can be overridden via `SDKConfig`.

## Global Configuration

```python
from agentic_swarm import set_config, SDKConfig
from agentic_swarm.core.config import (
    LLMConfig, MemoryConfig, RAGConfig,
    LifecycleConfig, ComplianceConfig,
)

set_config(SDKConfig(
    llm=LLMConfig(
        default_temperature=0.5,
        default_max_tokens=8192,
        default_strategy="quality_optimized",
    ),
    memory=MemoryConfig(
        recall_max_size=200,
        recall_max_tokens=16000,
    ),
    rag=RAGConfig(
        chunk_size=1024,
        chunk_overlap=100,
        embedding_model="text-embedding-3-large",
    ),
    lifecycle=LifecycleConfig(
        healer_max_retries=5,
        spawner_max_depth=5,
        spawner_max_children=20,
    ),
))
```

## Reset Configuration

```python
from agentic_swarm import reset_config
reset_config()  # Restores all defaults
```

---

## LLM Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `default_model` | `"gpt-4o-mini"` | Default model when none specified |
| `default_temperature` | `0.7` | Default generation temperature |
| `default_max_tokens` | `4096` | Default max output tokens |
| `default_strategy` | `"cost_optimized"` | Routing strategy: `cost_optimized`, `speed_optimized`, `quality_optimized` |
| `default_provider` | `"openai"` | Default LLM provider |
| `reserved_output_tokens` | `4000` | Tokens reserved for output in budget calculation |
| `system_prompt_tokens` | `500` | Estimated system prompt token count |
| `token_encoding` | `"cl100k_base"` | Tiktoken encoding name |
| `tokens_per_message_overhead` | `4` | Token overhead per message |
| `tokens_per_request_overhead` | `2` | Token overhead per request |

---

## Task Classifier Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `trivial_word_threshold` | `10` | Max words for trivial classification |
| `moderate_word_threshold` | `30` | Max words for moderate classification |
| `classification_temperature` | `0.0` | Temperature for LLM-based classification |
| `keywords` | `{...}` | Keyword mapping for complexity detection |

Override keywords to customize task classification:

```python
from agentic_swarm.core.config import ClassifierConfig

ClassifierConfig(keywords={
    "trivial": ["hello", "hi", "yes", "no"],
    "moderate": ["summarize", "explain", "list"],
    "complex": ["design", "architect", "implement"],
    "expert": ["research", "novel", "breakthrough"],
})
```

---

## Memory Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `recall_max_size` | `100` | Maximum entries in recall memory |
| `recall_max_tokens` | `8000` | Token budget for recall memory |
| `archival_collection_prefix` | `"archival"` | Prefix for archival memory collections |
| `archival_list_limit` | `100` | Max entries returned from archival listing |
| `core_memory_version` | `"1.0.0"` | Version string for core memory schema |

---

## Agent Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_iterations` | `10` | Max ReAct loop iterations per task |
| `default_timeout` | `300` | Agent timeout in seconds |

---

## Lifecycle Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `supervisor_check_interval` | `5.0` | Seconds between health checks |
| `supervisor_max_errors` | `3` | Errors before marking agent unhealthy |
| `healer_max_retries` | `3` | Max auto-heal retry attempts |
| `healer_backoff_factor` | `2.0` | Exponential backoff multiplier |
| `healer_max_backoff` | `30.0` | Max backoff delay in seconds |
| `spawner_max_depth` | `3` | Max depth of agent spawn tree |
| `spawner_max_children` | `10` | Max children per agent |

---

## Sandbox Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `cpu_limit` | `1.0` | CPU cores available to sandbox |
| `memory_limit_mb` | `512` | Memory limit in MB |
| `timeout_seconds` | `60` | Sandbox execution timeout |
| `allow_network` | `True` | Whether sandbox has network access |

---

## RAG Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `default_chunk_strategy` | `"recursive"` | Chunking strategy: `fixed`, `recursive`, `semantic` |
| `chunk_size` | `512` | Target chunk size in characters |
| `chunk_overlap` | `50` | Overlap between chunks |
| `chunk_separators` | `["\n\n", "\n", ". ", " "]` | Separators for recursive chunking |
| `embedding_model` | `"text-embedding-3-small"` | OpenAI embedding model |
| `embedding_dimensions` | `1536` | Embedding vector dimensions |
| `default_collection` | `"documents"` | Default vector DB collection name |
| `ingest_extensions` | `[".txt", ".md", ".py", ...]` | File extensions to ingest |
| `retrieval_strategy` | `"dense"` | Strategy: `dense`, `sparse`, `hybrid` |
| `rerank_initial_limit` | `20` | Candidates to fetch before reranking |
| `rerank_vector_weight` | `0.7` | Vector score weight in hybrid reranking |
| `rerank_keyword_weight` | `0.3` | Keyword score weight in hybrid reranking |

---

## Context Compressor Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `preserve_recent` | `5` | Recent messages to always preserve |
| `summary_truncate_length` | `100` | Max chars per message in summary |
| `summary_safety_factor` | `0.9` | Safety margin for token budget |
| `min_fact_length` | `20` | Min chars for extracted facts |
| `max_facts` | `10` | Max key facts to extract |
| `relevance_threshold` | `0.3` | Min relevance score for filtering |

---

## Vector DB Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `qdrant_host` | `"localhost"` | Qdrant server host |
| `qdrant_port` | `6333` | Qdrant server port |
| `qdrant_prefer_grpc` | `False` | Use gRPC instead of HTTP |

---

## Compliance Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `audit_query_limit` | `100` | Max audit entries per query |
| `encryption_iterations` | `480000` | PBKDF2 iterations for key derivation |
| `encryption_key_length` | `32` | Encryption key length in bytes |
| `encryption_salt_length` | `16` | Salt length in bytes |

---

## Built-in Tools Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `shell_timeout` | `30` | Shell command timeout in seconds |
| `web_fetch_timeout` | `30` | HTTP fetch timeout in seconds |
| `web_fetch_max_chars` | `10000` | Max characters from web fetch |
| `web_search_max_results` | `10` | Max search results to return |
| `memory_search_limit` | `5` | Default memory search result limit |
| `memory_recall_depth` | `10` | Default recall history depth |
