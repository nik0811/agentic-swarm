from dataclasses import dataclass
from .agent import Agent

@dataclass
class Swarm:
    """Swarm class for the agentic swarm."""
    agents: list[Agent]