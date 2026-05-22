from typing import Optional, Any, Dict
from pydantic import BaseModel
import time
import json

from ..core.types import AgentState


class StateSnapshot(BaseModel):
    agent_id: str
    name: str
    state: AgentState
    recall_messages: list
    timestamp: float
    metadata: dict = {}


class Healer:
    """Automatic recovery from agent failures."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor
        self._snapshots: Dict[str, StateSnapshot] = {}
        self._retry_counts: Dict[str, int] = {}
    
    def snapshot(self, agent: "Agent") -> StateSnapshot:
        """Capture state snapshot of an agent."""
        snapshot = StateSnapshot(
            agent_id=agent.id,
            name=agent.name,
            state=agent.state,
            recall_messages=agent._recall_memory.to_messages(),
            timestamp=time.time(),
        )
        self._snapshots[agent.id] = snapshot
        return snapshot
    
    async def recover(self, agent: "Agent", error: Exception) -> bool:
        """Attempt to recover an agent from failure."""
        agent_id = agent.id
        
        retry_count = self._retry_counts.get(agent_id, 0)
        if retry_count >= self._max_retries:
            return False
        
        self._retry_counts[agent_id] = retry_count + 1
        
        backoff = self._backoff_factor ** retry_count
        
        import asyncio
        await asyncio.sleep(min(backoff, 30))
        
        snapshot = self._snapshots.get(agent_id)
        if snapshot:
            await self.restore(agent, snapshot)
        
        agent._state = AgentState.RUNNING
        
        return True
    
    async def restore(self, agent: "Agent", snapshot: StateSnapshot) -> None:
        """Restore agent state from snapshot."""
        agent._recall_memory.clear()
        
        for msg in snapshot.recall_messages:
            agent._recall_memory.push(
                msg.get("content", ""),
                role=msg.get("role", "user"),
            )
    
    def reset_retries(self, agent_id: str) -> None:
        """Reset retry count for an agent."""
        self._retry_counts.pop(agent_id, None)
    
    def get_snapshot(self, agent_id: str) -> Optional[StateSnapshot]:
        """Get the last snapshot for an agent."""
        return self._snapshots.get(agent_id)
    
    def clear_snapshots(self, agent_id: str = None) -> None:
        """Clear snapshots."""
        if agent_id:
            self._snapshots.pop(agent_id, None)
        else:
            self._snapshots.clear()
