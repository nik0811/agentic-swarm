import asyncio
from typing import Dict, Optional, Callable
from enum import Enum
from pydantic import BaseModel
import time

from ..core.types import AgentState


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AgentHealth(BaseModel):
    agent_id: str
    status: HealthStatus
    last_check: float
    error_count: int = 0
    last_error: Optional[str] = None
    uptime: float = 0


class Supervisor:
    """Health monitoring and lifecycle management for agents."""
    
    def __init__(
        self,
        check_interval: float = 5.0,
        max_errors: int = 3,
        on_failure: Callable = None,
    ):
        self._agents: Dict[str, "Agent"] = {}
        self._health: Dict[str, AgentHealth] = {}
        self._check_interval = check_interval
        self._max_errors = max_errors
        self._on_failure = on_failure
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    def register(self, agent: "Agent") -> None:
        """Register an agent for monitoring."""
        self._agents[agent.id] = agent
        self._health[agent.id] = AgentHealth(
            agent_id=agent.id,
            status=HealthStatus.HEALTHY,
            last_check=time.time(),
        )
    
    def unregister(self, agent_id: str) -> None:
        """Unregister an agent."""
        self._agents.pop(agent_id, None)
        self._health.pop(agent_id, None)
    
    def health_check(self, agent_id: str) -> AgentHealth:
        """Check health of a specific agent."""
        if agent_id not in self._agents:
            return AgentHealth(
                agent_id=agent_id,
                status=HealthStatus.UNKNOWN,
                last_check=time.time(),
            )
        
        agent = self._agents[agent_id]
        health = self._health[agent_id]
        
        if agent.state == AgentState.TERMINATED:
            health.status = HealthStatus.UNHEALTHY
        elif agent.state == AgentState.RECOVERING:
            health.status = HealthStatus.DEGRADED
        elif health.error_count >= self._max_errors:
            health.status = HealthStatus.UNHEALTHY
        else:
            health.status = HealthStatus.HEALTHY
        
        health.last_check = time.time()
        return health
    
    async def monitor_all(self) -> None:
        """Start monitoring all registered agents."""
        self._running = True
        
        while self._running:
            for agent_id in list(self._agents.keys()):
                health = self.health_check(agent_id)
                
                if health.status == HealthStatus.UNHEALTHY:
                    if self._on_failure:
                        await self._on_failure(self._agents[agent_id], health)
            
            await asyncio.sleep(self._check_interval)
    
    def start_monitoring(self) -> asyncio.Task:
        """Start monitoring in background."""
        self._monitor_task = asyncio.create_task(self.monitor_all())
        return self._monitor_task
    
    def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
    
    def record_error(self, agent_id: str, error: str) -> None:
        """Record an error for an agent."""
        if agent_id in self._health:
            self._health[agent_id].error_count += 1
            self._health[agent_id].last_error = error
    
    def reset_errors(self, agent_id: str) -> None:
        """Reset error count for an agent."""
        if agent_id in self._health:
            self._health[agent_id].error_count = 0
            self._health[agent_id].last_error = None
    
    def get_status(self) -> Dict[str, AgentHealth]:
        """Get health status of all agents."""
        for agent_id in self._agents:
            self.health_check(agent_id)
        return self._health.copy()
