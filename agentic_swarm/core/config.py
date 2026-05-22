"""
Central configuration for the Agentic Swarm SDK.

All hardcoded defaults can be overridden here or when instantiating individual components.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class LLMConfig(BaseModel):
    """LLM-related configuration."""
    default_model: str = "gpt-4o-mini"
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    default_strategy: str = "cost_optimized"
    default_provider: str = "openai"
    reserved_output_tokens: int = 4000
    system_prompt_tokens: int = 500
    token_encoding: str = "cl100k_base"
    tokens_per_message_overhead: int = 4
    tokens_per_request_overhead: int = 2


class ClassifierConfig(BaseModel):
    """Task classifier configuration."""
    trivial_word_threshold: int = 10
    moderate_word_threshold: int = 30
    classification_temperature: float = 0.0
    keywords: Dict[str, List[str]] = {
        "trivial": [
            "yes", "no", "what is", "who is", "when", "where",
            "simple", "basic", "quick", "easy",
        ],
        "moderate": [
            "summarize", "explain", "describe", "list", "format",
            "convert", "translate", "write a short",
        ],
        "complex": [
            "analyze", "compare", "evaluate", "design", "implement",
            "create", "develop", "build", "multi-step", "reasoning",
        ],
        "expert": [
            "architecture", "research", "novel", "innovative", "complex system",
            "optimize", "security audit", "deep analysis",
        ],
    }


class MemoryConfig(BaseModel):
    """Memory system configuration."""
    recall_max_size: int = 100
    recall_max_tokens: int = 8000
    archival_collection_prefix: str = "archival"
    archival_list_limit: int = 100
    core_memory_version: str = "1.0.0"


class AgentConfig(BaseModel):
    """Agent configuration."""
    max_iterations: int = 10
    default_timeout: int = 300


class LifecycleConfig(BaseModel):
    """Lifecycle management configuration."""
    supervisor_check_interval: float = 5.0
    supervisor_max_errors: int = 3
    healer_max_retries: int = 3
    healer_backoff_factor: float = 2.0
    healer_max_backoff: float = 30.0
    spawner_max_depth: int = 3
    spawner_max_children: int = 10


class SandboxConfig(BaseModel):
    """Sandbox execution configuration."""
    cpu_limit: float = 1.0
    memory_limit_mb: int = 512
    timeout_seconds: int = 60
    allow_network: bool = True


class RAGConfig(BaseModel):
    """RAG pipeline configuration."""
    default_chunk_strategy: str = "recursive"
    chunk_size: int = 512
    chunk_overlap: int = 50
    chunk_separators: List[str] = ["\n\n", "\n", ". ", " "]
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    default_collection: str = "documents"
    ingest_extensions: List[str] = [".txt", ".md", ".py", ".js", ".ts"]
    retrieval_strategy: str = "dense"
    rerank_initial_limit: int = 20
    rerank_vector_weight: float = 0.7
    rerank_keyword_weight: float = 0.3


class CompressorConfig(BaseModel):
    """Context compressor configuration."""
    preserve_recent: int = 5
    summary_truncate_length: int = 100
    summary_safety_factor: float = 0.9
    min_fact_length: int = 20
    max_facts: int = 10
    relevance_threshold: float = 0.3


class VectorDBConfig(BaseModel):
    """Vector database configuration."""
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_prefer_grpc: bool = False


class ComplianceConfig(BaseModel):
    """Compliance and security configuration."""
    audit_query_limit: int = 100
    encryption_iterations: int = 480000
    encryption_key_length: int = 32
    encryption_salt_length: int = 16


class ToolsConfig(BaseModel):
    """Built-in tools configuration."""
    shell_timeout: int = 30
    web_fetch_timeout: int = 30
    web_fetch_max_chars: int = 10000
    web_search_max_results: int = 10
    memory_search_limit: int = 5
    memory_recall_depth: int = 10


class SDKConfig(BaseModel):
    """
    Master configuration for the entire Agentic Swarm SDK.
    
    All hardcoded values can be overridden here.
    
    Usage:
        from agentic_swarm.core.config import SDKConfig
        
        config = SDKConfig(
            llm=LLMConfig(default_temperature=0.5),
            agent=AgentConfig(max_iterations=20),
            rag=RAGConfig(chunk_size=1024),
        )
        
        # Or override individual values
        config.llm.default_max_tokens = 8192
        config.lifecycle.healer_max_retries = 5
    """
    llm: LLMConfig = LLMConfig()
    classifier: ClassifierConfig = ClassifierConfig()
    memory: MemoryConfig = MemoryConfig()
    agent: AgentConfig = AgentConfig()
    lifecycle: LifecycleConfig = LifecycleConfig()
    sandbox: SandboxConfig = SandboxConfig()
    rag: RAGConfig = RAGConfig()
    compressor: CompressorConfig = CompressorConfig()
    vectordb: VectorDBConfig = VectorDBConfig()
    compliance: ComplianceConfig = ComplianceConfig()
    tools: ToolsConfig = ToolsConfig()


# Global default config instance — override this to change defaults SDK-wide
_global_config: Optional[SDKConfig] = None


def get_config() -> SDKConfig:
    """Get the global SDK configuration."""
    global _global_config
    if _global_config is None:
        _global_config = SDKConfig()
    return _global_config


def set_config(config: SDKConfig) -> None:
    """Set the global SDK configuration.
    
    Usage:
        from agentic_swarm.core.config import set_config, SDKConfig, LLMConfig
        
        set_config(SDKConfig(
            llm=LLMConfig(default_temperature=0.3, default_max_tokens=8192),
        ))
    """
    global _global_config
    _global_config = config


def reset_config() -> None:
    """Reset to default configuration."""
    global _global_config
    _global_config = SDKConfig()
