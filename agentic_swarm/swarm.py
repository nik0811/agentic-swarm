import asyncio
from typing import Any, List, Literal, Optional
from dataclasses import dataclass, field

from .agent import Agent
from .core.exceptions import InvalidStrategyError
from .communication.bus import MessageBus
from .communication.protocols import Message, MessageType


@dataclass
class SwarmResult:
    """Result from swarm execution."""
    results: List[Any] = field(default_factory=list)
    errors: List[Exception] = field(default_factory=list)
    agent_results: dict = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


class Swarm:
    """
    Swarm orchestrator that coordinates multiple agents.
    
    Features per Architecture.md:
    - Task decomposition and delegation
    - Agent lifecycle management
    - Load balancing across agents
    - Health monitoring integration
    - Failure recovery
    - Encrypted message bus communication
    """

    def __init__(
        self,
        agents: List[Agent] = None,
        message_bus: MessageBus = None,
        max_retries: int = 3,
    ):
        self._agents: dict[str, Agent] = {}
        self._message_bus = message_bus or MessageBus()
        self._max_retries = max_retries

        for agent in (agents or []):
            self.add_agent(agent)

    @property
    def agents(self) -> List[Agent]:
        return list(self._agents.values())

    @property
    def bus(self) -> MessageBus:
        return self._message_bus

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the swarm and subscribe to message bus."""
        self._agents[agent.id] = agent
        self._message_bus.subscribe(agent.id, self._create_message_handler(agent))

    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the swarm."""
        self._agents.pop(agent_id, None)
        self._message_bus.unsubscribe(agent_id)

    def get_agent(self, agent_id: str) -> Agent | None:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def get_agent_by_name(self, name: str) -> Agent | None:
        """Get agent by name."""
        for agent in self._agents.values():
            if agent.name == name:
                return agent
        return None

    async def run(
        self,
        task: str,
        strategy: Literal["sequential", "parallel", "adaptive"] = "sequential"
    ) -> SwarmResult:
        """
        Run a task across agents.
        
        Strategies:
        - sequential: agents run one after another, each building on previous
        - parallel: all agents run simultaneously on the same task
        - adaptive: decompose task and assign subtasks to best-fit agents
        """
        if strategy == "sequential":
            return await self._run_sequential(task)
        elif strategy == "parallel":
            return await self._run_parallel(task)
        elif strategy == "adaptive":
            return await self._run_adaptive(task)
        else:
            raise InvalidStrategyError(f"Unknown strategy: {strategy}")

    async def _run_sequential(self, task: str) -> SwarmResult:
        """Run agents sequentially, passing results to next agent."""
        result = SwarmResult()
        current_task = task

        for agent in self._agents.values():
            try:
                output = await self._run_with_retry(agent, current_task)
                result.results.append(output)
                result.agent_results[agent.name] = output
                current_task = f"Previous agent ({agent.name}) output: {output}\n\nContinue with: {task}"
            except Exception as e:
                result.errors.append(e)
                result.agent_results[agent.name] = {"error": str(e)}

        return result

    async def _run_parallel(self, task: str) -> SwarmResult:
        """Run all agents in parallel."""
        result = SwarmResult()

        async def run_agent(agent: Agent):
            try:
                return agent.name, await self._run_with_retry(agent, task)
            except Exception as e:
                return agent.name, e

        outputs = await asyncio.gather(
            *[run_agent(agent) for agent in self._agents.values()],
            return_exceptions=True
        )

        for output in outputs:
            if isinstance(output, Exception):
                result.errors.append(output)
            else:
                name, value = output
                if isinstance(value, Exception):
                    result.errors.append(value)
                    result.agent_results[name] = {"error": str(value)}
                else:
                    result.results.append(value)
                    result.agent_results[name] = value

        return result

    async def _run_adaptive(self, task: str) -> SwarmResult:
        """Decompose task and assign subtasks to best-fit agents.
        
        Uses agent roles to match subtasks to capabilities.
        If an LLM router is available, uses it for decomposition.
        """
        result = SwarmResult()

        if len(self._agents) <= 1:
            return await self._run_sequential(task)

        subtasks = self._decompose_task(task)

        if len(subtasks) == 1:
            return await self._run_sequential(task)

        assignments = self._assign_subtasks(subtasks)

        for agent, subtask in assignments:
            try:
                output = await self._run_with_retry(agent, subtask)
                result.results.append(output)
                result.agent_results[agent.name] = output

                await self._message_bus.publish(Message(
                    type=MessageType.TASK_RESULT,
                    sender_id=agent.id,
                    content={"task": subtask, "result": str(output)[:500]},
                ))
            except Exception as e:
                result.errors.append(e)
                result.agent_results[agent.name] = {"error": str(e)}

        return result

    def _decompose_task(self, task: str) -> List[str]:
        """Simple rule-based task decomposition."""
        indicators = [
            " then ", " and then ", " after that ",
            " next ", " finally ", " also ",
        ]

        for indicator in indicators:
            if indicator in task.lower():
                parts = task.split(indicator, 1)
                if len(parts) == 2 and all(len(p.strip()) > 10 for p in parts):
                    return [p.strip() for p in parts]

        if len(self._agents) > 1 and len(task) > 100:
            agents = list(self._agents.values())
            return [task] * min(len(agents), 3)

        return [task]

    def _assign_subtasks(self, subtasks: List[str]) -> List[tuple]:
        """Assign subtasks to agents based on role matching."""
        agents = list(self._agents.values())
        assignments = []

        for i, subtask in enumerate(subtasks):
            best_agent = self._find_best_agent(subtask, agents)
            assignments.append((best_agent, subtask))

        return assignments

    def _find_best_agent(self, subtask: str, agents: List[Agent]) -> Agent:
        """Find the best agent for a subtask based on role keyword matching."""
        subtask_lower = subtask.lower()
        best_score = -1
        best_agent = agents[0]

        for agent in agents:
            role_words = set(agent.role.lower().split())
            task_words = set(subtask_lower.split())
            overlap = len(role_words & task_words)
            if overlap > best_score:
                best_score = overlap
                best_agent = agent

        return best_agent

    async def _run_with_retry(self, agent: Agent, task: str) -> Any:
        """Run agent with retry on failure."""
        last_error = None

        for attempt in range(self._max_retries):
            try:
                return await agent.run(task)
            except Exception as e:
                last_error = e
                agent._state = agent._state  # keep state
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))

        raise last_error

    async def delegate(self, from_agent: Agent, to_agent: Agent, task: str) -> Any:
        """Delegate a task from one agent to another via the message bus."""
        await self._message_bus.publish(Message(
            type=MessageType.TASK_DELEGATE,
            sender_id=from_agent.id,
            receiver_id=to_agent.id,
            content=task,
        ))

        result = await to_agent.run(task)

        await self._message_bus.publish(Message(
            type=MessageType.TASK_RESULT,
            sender_id=to_agent.id,
            receiver_id=from_agent.id,
            content=str(result)[:500],
        ))

        return result

    async def broadcast(self, message: str, sender_id: str = "swarm") -> None:
        """Broadcast message to all agents via message bus."""
        await self._message_bus.broadcast(sender_id, message)

        for agent in self._agents.values():
            agent._recall_memory.push(f"[Broadcast] {message}", role="system")

    async def health_ping_all(self) -> dict:
        """Send health ping to all agents and collect status."""
        status = {}
        for agent in self._agents.values():
            status[agent.name] = {
                "id": agent.id,
                "state": agent.state.value,
                "healthy": agent.state.value not in ("terminated", "recovering"),
            }
        return status

    async def terminate_all(self) -> None:
        """Terminate all agents and cleanup."""
        for agent in self._agents.values():
            await agent.terminate()
        self._message_bus.clear()
        self._agents.clear()

    def _create_message_handler(self, agent: Agent):
        """Create a message handler for an agent."""
        async def handler(message: Message):
            if message.type == MessageType.TASK_DELEGATE:
                agent._recall_memory.push(
                    f"Delegated task from {message.sender_id}: {message.content}",
                    role="system"
                )
            elif message.type == MessageType.CONTEXT_SHARE:
                agent._recall_memory.push(
                    f"Context from {message.sender_id}: {message.content}",
                    role="system"
                )
            elif message.type == MessageType.HEALTH_PING:
                await self._message_bus.publish(Message(
                    type=MessageType.STATUS,
                    sender_id=agent.id,
                    receiver_id=message.sender_id,
                    content={"state": agent.state.value},
                ))
        return handler
