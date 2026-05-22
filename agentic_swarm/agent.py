import uuid
import json
import asyncio
from typing import Any, List, Optional

from .core.types import AgentState
from .core.exceptions import ToolNotFoundError
from .memory.core_memory import CoreMemory
from .memory.recall_memory import RecallMemory
from .tools.base import Tool
from .llm.base import LLMMessage
from .llm.router import LLMRouter
from .lifecycle.spawner import Spawner


class Agent:
    """
    Base Agent class with lifecycle management.
    Supports tools, memory, and dynamic agent creation.
    """
    
    _default_spawner = Spawner(max_depth=5, max_children=20)
    
    def __init__(
        self,
        name: str,
        role: str,
        tools: List[Tool] = None,
        llm: str = None,
        llm_router: LLMRouter = None,
        max_iterations: int = 10,
        parent: "Agent" = None,
        spawner: Spawner = None,
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.tools = {t.name: t for t in (tools or [])}
        self.llm_model = llm
        self.llm_router = llm_router
        self.max_iterations = max_iterations
        self.parent = parent
        self._state = AgentState.CREATED
        self._children: List["Agent"] = []
        self._spawner = spawner or (parent._spawner if parent else self._default_spawner)
        
        self._core_memory = CoreMemory(
            agent_id=self.id,
            name=name,
            persona=role,
            capabilities=list(self.tools.keys()),
        )
        self._recall_memory = RecallMemory()
        
        if not parent:
            self._spawner.register_root(self.id)
    
    @property
    def state(self) -> AgentState:
        return self._state
    
    @property
    def role(self) -> str:
        return self._core_memory.persona
    
    async def run(self, task: str) -> Any:
        """
        Execute a task using ReAct pattern.
        Think -> Act -> Observe -> Loop
        """
        self._state = AgentState.RUNNING
        self._recall_memory.push(task, role="user")
        
        try:
            for iteration in range(self.max_iterations):
                response = await self._think()
                
                if response.get("done"):
                    self._state = AgentState.DONE
                    return response.get("result")
                
                if tool_call := response.get("tool_call"):
                    result = await self._execute_tool(
                        tool_call["name"],
                        tool_call["arguments"]
                    )
                    self._recall_memory.push(
                        f"Tool {tool_call['name']} returned: {result}",
                        role="tool"
                    )
            
            self._state = AgentState.DONE
            return {"error": "Max iterations reached"}
            
        except Exception as e:
            self._state = AgentState.RECOVERING
            await self._recover(e)
            raise
    
    async def _think(self) -> dict:
        """Get next action from LLM."""
        system = self._core_memory.to_prompt()
        messages = [LLMMessage(role=m["role"], content=m["content"]) 
                   for m in self._recall_memory.to_messages()]
        tools = [t.to_openai_schema() for t in self.tools.values()] if self.tools else None
        
        if not self.llm_router:
            return {"done": True, "result": "Placeholder - LLM not connected"}
        
        last_message = messages[-1].content if messages else ""
        
        response = await self.llm_router.route(
            task=last_message,
            messages=messages[:-1] if len(messages) > 1 else None,
            tools=tools,
            system_prompt=system,
            force_model=self.llm_model,
        )
        
        self._recall_memory.push(response.content or "", role="assistant")
        
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            try:
                arguments = json.loads(tool_call["arguments"]) if isinstance(tool_call["arguments"], str) else tool_call["arguments"]
            except json.JSONDecodeError:
                arguments = {}
            
            return {
                "done": False,
                "tool_call": {
                    "name": tool_call["name"],
                    "arguments": arguments,
                }
            }
        
        return {"done": True, "result": response.content}
    
    async def _execute_tool(self, name: str, arguments: dict) -> Any:
        """Execute a tool by name."""
        tool = self.tools.get(name)
        if not tool:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        
        return await tool.execute(**arguments)
    
    async def _recover(self, error: Exception) -> None:
        """Attempt to recover from error."""
        self._recall_memory.push(f"Error occurred: {error}", role="system")
        self._state = AgentState.RUNNING
    
    async def create_agent(
        self,
        name: str,
        role: str,
        tools: List[Tool] = None,
        **kwargs
    ) -> "Agent":
        """Create a child agent dynamically using the Spawner.
        
        Respects max_depth and max_children constraints.
        Raises RuntimeError if spawn limits are exceeded.
        """
        child = await self._spawner.spawn(
            parent=self,
            name=name,
            role=role,
            tools=tools,
            spawner=self._spawner,
            **kwargs
        )
        return child
    
    async def run_parallel(self, tasks: List[str]) -> List[Any]:
        """Run multiple tasks in parallel using child agents.
        
        Creates a child agent per task, runs them concurrently,
        and returns results in order.
        """
        children = []
        for i, task in enumerate(tasks):
            child = await self.create_agent(
                name=f"{self.name}_worker_{i}",
                role=self.role,
            )
            children.append(child)
        
        results = await asyncio.gather(
            *[child.run(task) for child, task in zip(children, tasks)],
            return_exceptions=True,
        )
        return list(results)
    
    async def send(self, target: "Agent", message: str) -> None:
        """Send message to another agent."""
        target._recall_memory.push(
            f"Message from {self.name}: {message}",
            role="system"
        )
    
    async def terminate(self) -> None:
        """Terminate agent and cleanup."""
        for child in self._children:
            await child.terminate()
        
        self._state = AgentState.TERMINATED
        self._recall_memory.clear()
    
    def __eq__(self, other):
        if not isinstance(other, Agent):
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
