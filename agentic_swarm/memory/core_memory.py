from typing import Any
from pydantic import BaseModel
import time


class CoreMemoryData(BaseModel):
    """Immutable agent identity."""
    model_config = {"frozen": True}
    
    agent_id: str
    name: str
    persona: str
    capabilities: list[str] = []
    created_at: float
    version: str = "1.0.0"


class CoreMemory:
    """
    Immutable memory storing agent identity.
    Once set, cannot be modified (only read).
    """
    
    def __init__(self, agent_id: str, name: str, persona: str, capabilities: list[str] = None):
        self._data = CoreMemoryData(
            agent_id=agent_id,
            name=name,
            persona=persona,
            capabilities=capabilities or [],
            created_at=time.time(),
        )
        self._frozen = True
    
    @property
    def agent_id(self) -> str:
        return self._data.agent_id
    
    @property
    def name(self) -> str:
        return self._data.name
    
    @property
    def persona(self) -> str:
        return self._data.persona
    
    @property
    def capabilities(self) -> list[str]:
        return self._data.capabilities.copy()
    
    def to_prompt(self) -> str:
        """Convert to system prompt format."""
        caps = ', '.join(self.capabilities) if self.capabilities else 'General assistant'
        return f"""You are {self.name}.

{self.persona}

Your capabilities: {caps}
"""
    
    def to_dict(self) -> dict:
        return self._data.model_dump()
