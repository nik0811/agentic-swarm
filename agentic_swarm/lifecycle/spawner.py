from typing import List, Optional, Dict, Any
import uuid

from ..core.types import AgentSpec
from ..core.exceptions import AgentCreationError


class Spawner:
    """Dynamic sub-agent creation."""
    
    def __init__(self, max_depth: int = 3, max_children: int = 10):
        self._max_depth = max_depth
        self._max_children = max_children
        self._agent_tree: Dict[str, List[str]] = {}
        self._agent_depth: Dict[str, int] = {}
    
    def can_spawn(self, parent_id: str) -> bool:
        """Check if parent can spawn more children."""
        depth = self._agent_depth.get(parent_id, 0)
        if depth >= self._max_depth:
            return False
        
        children = self._agent_tree.get(parent_id, [])
        if len(children) >= self._max_children:
            return False
        
        return True
    
    async def spawn(
        self,
        parent: "Agent",
        name: str,
        role: str,
        tools: List = None,
        **kwargs
    ) -> "Agent":
        """Spawn a new child agent."""
        from ..agent import Agent
        
        if not self.can_spawn(parent.id):
            raise AgentCreationError(f"Cannot spawn more children for agent {parent.id}: max_depth={self._max_depth}, max_children={self._max_children}")
        
        child = Agent(
            name=name,
            role=role,
            tools=tools,
            llm_router=parent.llm_router,
            parent=parent,
            **kwargs
        )
        
        parent._children.append(child)
        
        if parent.id not in self._agent_tree:
            self._agent_tree[parent.id] = []
        self._agent_tree[parent.id].append(child.id)
        
        parent_depth = self._agent_depth.get(parent.id, 0)
        self._agent_depth[child.id] = parent_depth + 1
        
        return child
    
    def register_root(self, agent_id: str) -> None:
        """Register an agent as a root (depth 0)."""
        self._agent_depth[agent_id] = 0
    
    def get_children(self, agent_id: str) -> List[str]:
        """Get list of child agent IDs."""
        return self._agent_tree.get(agent_id, []).copy()
    
    def get_depth(self, agent_id: str) -> int:
        """Get depth of an agent in the tree."""
        return self._agent_depth.get(agent_id, 0)
    
    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from tracking."""
        self._agent_tree.pop(agent_id, None)
        self._agent_depth.pop(agent_id, None)
        
        for parent_id, children in self._agent_tree.items():
            if agent_id in children:
                children.remove(agent_id)
