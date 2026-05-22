import asyncio
from typing import Any, List, Literal
from dataclasses import dataclass, field

from .agent import Agent


@dataclass
class SwarmResult:
    """Result from swarm execution."""
    results: List[Any] = field(default_factory=list)
    errors: List[Exception] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        return len(self.errors) == 0


class Swarm:
    """
    Swarm orchestrator that coordinates multiple agents.
    """
    
    def __init__(self, agents: List[Agent] = None):
        self._agents: dict[str, Agent] = {}
        for agent in (agents or []):
            self.add_agent(agent)
    
    @property
    def agents(self) -> List[Agent]:
        return list(self._agents.values())
    
    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the swarm."""
        self._agents[agent.id] = agent
    
    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the swarm."""
        self._agents.pop(agent_id, None)
    
    def get_agent(self, agent_id: str) -> Agent | None:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    async def run(
        self,
        task: str,
        strategy: Literal["sequential", "parallel", "adaptive"] = "sequential"
    ) -> SwarmResult:
        """
        Run a task across all agents.
        
        Strategies:
        - sequential: agents run one after another
        - parallel: all agents run simultaneously
        - adaptive: decompose task and assign to best agent
        """
        if strategy == "sequential":
            return await self._run_sequential(task)
        elif strategy == "parallel":
            return await self._run_parallel(task)
        elif strategy == "adaptive":
            return await self._run_adaptive(task)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    async def _run_sequential(self, task: str) -> SwarmResult:
        """Run agents sequentially, passing results to next agent."""
        result = SwarmResult()
        current_task = task
        
        for agent in self._agents.values():
            try:
                output = await agent.run(current_task)
                result.results.append(output)
                current_task = f"Previous agent output: {output}\n\nContinue with: {task}"
            except Exception as e:
                result.errors.append(e)
        
        return result
    
    async def _run_parallel(self, task: str) -> SwarmResult:
        """Run all agents in parallel."""
        result = SwarmResult()
        
        async def run_agent(agent: Agent):
            try:
                return await agent.run(task)
            except Exception as e:
                return e
        
        outputs = await asyncio.gather(
            *[run_agent(agent) for agent in self._agents.values()],
            return_exceptions=True
        )
        
        for output in outputs:
            if isinstance(output, Exception):
                result.errors.append(output)
            else:
                result.results.append(output)
        
        return result
    
    async def _run_adaptive(self, task: str) -> SwarmResult:
        """Decompose task and assign to best agent."""
        # For now, just run sequentially
        # TODO: Implement task decomposition with LLM
        return await self._run_sequential(task)
    
    async def broadcast(self, message: str) -> None:
        """Send message to all agents."""
        for agent in self._agents.values():
            agent._recall_memory.push(f"Broadcast: {message}", role="system")
    
    async def terminate_all(self) -> None:
        """Terminate all agents."""
        for agent in self._agents.values():
            await agent.terminate()
        self._agents.clear()
