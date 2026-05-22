class AgenticSwarmError(Exception):
    """Base exception for all SDK errors."""

    pass


# -- Agent errors --


class AgentError(AgenticSwarmError):
    """Agent-related errors."""

    pass


class AgentNotFoundError(AgentError):
    """Agent not found in registry."""

    pass


class AgentCreationError(AgentError, RuntimeError):
    """Failed to create agent (e.g. spawn limits exceeded)."""

    pass


class AgentTerminatedError(AgentError):
    """Operation attempted on a terminated agent."""

    pass


# -- Tool errors --


class ToolError(AgenticSwarmError):
    """Tool-related errors."""

    pass


class ToolNotFoundError(ToolError):
    """Tool not found in agent's tool registry."""

    pass


class ToolExecutionError(ToolError):
    """Tool execution failed at runtime."""

    pass


# -- Memory errors --


class MemoryError(AgenticSwarmError):
    """Memory-related errors."""

    pass


class MemoryCapacityError(MemoryError):
    """Memory capacity exceeded (recall window full, archival write failed)."""

    pass


# -- LLM errors --


class LLMError(AgenticSwarmError):
    """LLM-related errors."""

    pass


class LLMProviderError(LLMError):
    """LLM provider unavailable, misconfigured, or returned an error."""

    pass


class TokenBudgetExceededError(LLMError):
    """Token budget exceeded for the given context window."""

    pass


class ModelNotAvailableError(LLMError):
    """Requested model is not registered or accessible."""

    pass


# -- Configuration errors --


class ConfigurationError(AgenticSwarmError):
    """Invalid or missing configuration."""

    pass


class MissingAPIKeyError(ConfigurationError):
    """Required API key not found in environment or config."""

    pass


class InvalidStrategyError(ConfigurationError):
    """Unknown or unsupported strategy specified."""

    pass


# -- Communication errors --


class CommunicationError(AgenticSwarmError):
    """Inter-agent communication errors."""

    pass


class ChannelClosedError(CommunicationError, RuntimeError):
    """Attempted to use a closed channel."""

    pass


class MessageDeliveryError(CommunicationError):
    """Message could not be delivered to the target agent."""

    pass


# -- Lifecycle errors --


class LifecycleError(AgenticSwarmError):
    """Lifecycle management errors."""

    pass


class SandboxTimeoutError(LifecycleError, TimeoutError):
    """Sandboxed execution exceeded the configured timeout."""

    pass


class RecoveryFailedError(LifecycleError):
    """Agent recovery failed after max retries."""

    pass


# -- RAG errors --


class RAGError(AgenticSwarmError):
    """RAG pipeline errors."""

    pass


class EmbeddingError(RAGError):
    """Failed to generate embeddings."""

    pass


class RetrievalError(RAGError):
    """Failed to retrieve documents from vector store."""

    pass


class IngestionError(RAGError):
    """Failed to ingest documents into the pipeline."""

    pass


# -- Compliance errors --


class ComplianceError(AgenticSwarmError):
    """Compliance and security errors."""

    pass


class EncryptionError(ComplianceError):
    """Encryption/decryption operation failed."""

    pass


class AccessDeniedError(ComplianceError):
    """Agent does not have permission for the requested operation."""

    pass


# -- Dependency errors --


class DependencyError(AgenticSwarmError):
    """Optional dependency not installed."""

    pass
