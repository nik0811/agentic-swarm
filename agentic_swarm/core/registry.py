"""Global agent registry for tracking all active agents in the system."""

import threading


class AgentRegistry:
    """Singleton registry that tracks all active agents across swarms."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._agents = {}
                cls._instance._swarms = {}
            return cls._instance

    def register(self, agent_id: str, agent) -> None:
        """Register an agent."""
        self._agents[agent_id] = agent

    def unregister(self, agent_id: str) -> None:
        """Remove an agent from registry."""
        self._agents.pop(agent_id, None)

    def get(self, agent_id: str) -> object | None:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> list[str]:
        """List all registered agent IDs."""
        return list(self._agents.keys())

    def list_by_state(self, state: str) -> list[str]:
        """List agents filtered by state."""
        return [
            aid
            for aid, agent in self._agents.items()
            if hasattr(agent, "state") and str(agent.state) == state
        ]

    def register_swarm(self, swarm_id: str, swarm) -> None:
        """Register a swarm."""
        self._swarms[swarm_id] = swarm

    def unregister_swarm(self, swarm_id: str) -> None:
        """Remove a swarm."""
        self._swarms.pop(swarm_id, None)

    def get_swarm(self, swarm_id: str) -> object | None:
        """Get a swarm by ID."""
        return self._swarms.get(swarm_id)

    def count(self) -> int:
        """Total registered agents."""
        return len(self._agents)

    def clear(self) -> None:
        """Clear all registrations."""
        self._agents.clear()
        self._swarms.clear()

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._agents.clear()
                cls._instance._swarms.clear()
                cls._instance = None
