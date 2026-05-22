import re


def validate_agent_name(name: str) -> str | None:
    """Validate agent name. Returns error message or None if valid."""
    if not name:
        return "Agent name cannot be empty"
    if len(name) > 64:
        return "Agent name cannot exceed 64 characters"
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
        return "Agent name must start with a letter and contain only alphanumeric, underscore, or hyphen"
    return None


def validate_model_name(model: str) -> str | None:
    """Validate model name. Returns error message or None if valid."""
    if not model:
        return "Model name cannot be empty"
    if len(model) > 128:
        return "Model name cannot exceed 128 characters"
    return None


def validate_temperature(temperature: float) -> str | None:
    """Validate temperature parameter."""
    if not 0.0 <= temperature <= 2.0:
        return "Temperature must be between 0.0 and 2.0"
    return None


def validate_max_tokens(max_tokens: int) -> str | None:
    """Validate max_tokens parameter."""
    if max_tokens < 1:
        return "max_tokens must be at least 1"
    if max_tokens > 1000000:
        return "max_tokens cannot exceed 1000000"
    return None
