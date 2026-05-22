"""Fine-grained access control for agent operations."""

from enum import Enum

from pydantic import BaseModel


class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    SPAWN = "spawn"
    TERMINATE = "terminate"
    ADMIN = "admin"


class AccessPolicy(BaseModel):
    """Defines what an agent is allowed to do."""

    agent_id: str
    permissions: set[Permission] = set()
    allowed_tools: list[str] = []
    denied_tools: list[str] = []
    max_spawn_depth: int = 3
    allowed_models: list[str] = []
    rate_limit_per_minute: int = 60


class AccessController:
    """Manages access policies for agents."""

    def __init__(self):
        self._policies: dict[str, AccessPolicy] = {}
        self._default_permissions: set[Permission] = {
            Permission.READ,
            Permission.WRITE,
            Permission.EXECUTE,
        }

    def set_policy(self, agent_id: str, policy: AccessPolicy) -> None:
        """Set access policy for an agent."""
        self._policies[agent_id] = policy

    def get_policy(self, agent_id: str) -> AccessPolicy | None:
        """Get access policy for an agent."""
        return self._policies.get(agent_id)

    def check_permission(self, agent_id: str, permission: Permission) -> bool:
        """Check if agent has a specific permission."""
        policy = self._policies.get(agent_id)
        if policy is None:
            return permission in self._default_permissions
        return permission in policy.permissions

    def check_tool_access(self, agent_id: str, tool_name: str) -> bool:
        """Check if agent can use a specific tool."""
        policy = self._policies.get(agent_id)
        if policy is None:
            return True
        if policy.denied_tools and tool_name in policy.denied_tools:
            return False
        if policy.allowed_tools:
            return tool_name in policy.allowed_tools
        return True

    def check_model_access(self, agent_id: str, model_name: str) -> bool:
        """Check if agent can use a specific model."""
        policy = self._policies.get(agent_id)
        if policy is None:
            return True
        if not policy.allowed_models:
            return True
        return model_name in policy.allowed_models

    def remove_policy(self, agent_id: str) -> None:
        """Remove policy for an agent."""
        self._policies.pop(agent_id, None)

    def clear(self) -> None:
        """Clear all policies."""
        self._policies.clear()
