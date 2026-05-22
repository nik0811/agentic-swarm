class AgenticSwarmError(Exception):
    """Base exception for all SDK errors."""
    pass

class AgentError(AgenticSwarmError):
    """Agent-related errors."""
    pass

class AgentNotFoundError(AgentError):
    """Agent not found in registry."""
    pass

class AgentCreationError(AgentError):
    """Failed to create agent."""
    pass

class ToolError(AgenticSwarmError):
    """Tool-related errors."""
    pass

class ToolNotFoundError(ToolError):
    """Tool not found in registry."""
    pass

class ToolExecutionError(ToolError):
    """Tool execution failed."""
    pass

class MemoryError(AgenticSwarmError):
    """Memory-related errors."""
    pass

class LLMError(AgenticSwarmError):
    """LLM-related errors."""
    pass

class LLMProviderError(LLMError):
    """LLM provider unavailable or failed."""
    pass

class TokenBudgetExceededError(LLMError):
    """Token budget exceeded."""
    pass