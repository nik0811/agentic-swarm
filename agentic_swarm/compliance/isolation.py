class DataIsolation:
    """Ensure agents cannot access each other's data."""

    def __init__(self):
        self._namespaces: dict[str, str] = {}
        self._permissions: dict[str, set[str]] = {}

    def register_agent(self, agent_id: str, tenant_id: str = None) -> str:
        """Register an agent and create its namespace."""
        namespace = f"agent:{agent_id}"
        if tenant_id:
            namespace = f"tenant:{tenant_id}:agent:{agent_id}"

        self._namespaces[agent_id] = namespace
        self._permissions[agent_id] = {namespace}

        return namespace

    def get_namespace(self, agent_id: str) -> str:
        """Get the namespace for an agent."""
        return self._namespaces.get(agent_id, f"agent:{agent_id}")

    def grant_access(self, agent_id: str, resource: str) -> None:
        """Grant an agent access to a resource."""
        if agent_id not in self._permissions:
            self._permissions[agent_id] = set()
        self._permissions[agent_id].add(resource)

    def revoke_access(self, agent_id: str, resource: str) -> None:
        """Revoke an agent's access to a resource."""
        if agent_id in self._permissions:
            self._permissions[agent_id].discard(resource)

    def validate_access(self, agent_id: str, resource: str) -> bool:
        """Check if an agent can access a resource."""
        if agent_id not in self._permissions:
            return False

        agent_namespace = self.get_namespace(agent_id)
        if resource.startswith(agent_namespace):
            return True

        return resource in self._permissions[agent_id]

    def isolate_data(self, data: dict, agent_id: str) -> dict:
        """Add isolation metadata to data."""
        namespace = self.get_namespace(agent_id)
        return {
            "_namespace": namespace,
            "_agent_id": agent_id,
            **data,
        }

    def filter_data(self, data: dict, agent_id: str) -> dict | None:
        """Filter data based on agent's access."""
        data_namespace = data.get("_namespace", "")
        data_agent_id = data.get("_agent_id", "")

        if data_agent_id == agent_id:
            return data

        if self.validate_access(agent_id, data_namespace):
            return data

        return None

    def unregister_agent(self, agent_id: str) -> None:
        """Remove an agent's namespace and permissions."""
        self._namespaces.pop(agent_id, None)
        self._permissions.pop(agent_id, None)


class RBACManager:
    """Role-Based Access Control."""

    def __init__(self):
        self._roles: dict[str, set[str]] = {}
        self._agent_roles: dict[str, set[str]] = {}

    def create_role(self, role: str, permissions: set[str]) -> None:
        """Create a role with permissions."""
        self._roles[role] = permissions

    def assign_role(self, agent_id: str, role: str) -> None:
        """Assign a role to an agent."""
        if agent_id not in self._agent_roles:
            self._agent_roles[agent_id] = set()
        self._agent_roles[agent_id].add(role)

    def remove_role(self, agent_id: str, role: str) -> None:
        """Remove a role from an agent."""
        if agent_id in self._agent_roles:
            self._agent_roles[agent_id].discard(role)

    def has_permission(self, agent_id: str, permission: str) -> bool:
        """Check if an agent has a permission."""
        roles = self._agent_roles.get(agent_id, set())

        for role in roles:
            role_permissions = self._roles.get(role, set())
            if permission in role_permissions or "*" in role_permissions:
                return True

        return False

    def get_permissions(self, agent_id: str) -> set[str]:
        """Get all permissions for an agent."""
        permissions = set()
        roles = self._agent_roles.get(agent_id, set())

        for role in roles:
            permissions.update(self._roles.get(role, set()))

        return permissions
