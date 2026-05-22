import uuid
import json
import asyncio
from typing import Any, List, Optional, Union

from .core.types import AgentState
from .core.exceptions import ToolNotFoundError
from .memory.core_memory import CoreMemory
from .memory.recall_memory import RecallMemory
from .memory.controller import MemoryController
from .tools.base import Tool
from .tools.discovery import ToolRegistry as ToolDiscovery, ToolSelector, get_global_registry as _get_discovery_registry
from .llm.base import LLMMessage
from .llm.router import LLMRouter
from .llm.context_compressor import ContextCompressor
from .lifecycle.spawner import Spawner
from .lifecycle.sandbox import Sandbox, SandboxConfig
from .compliance.isolation import DataIsolation
from .vectordb.base import BaseVectorDB
from .rag.embedder import Embedder


# Global data isolation manager (shared across all agents)
_global_isolation = DataIsolation()


def get_tool_registry() -> ToolDiscovery:
    """Get the global tool registry (from discovery module)."""
    return _get_discovery_registry()


def register_tool(
    tool: Tool,
    category: str = "general",
    keywords: List[str] = None
) -> Tool:
    """Register a tool globally for auto-discovery by agents."""
    get_tool_registry().register(tool, category, keywords)
    return tool


class Agent:
    """
    Base Agent class with lifecycle management.
    
    Features:
    - Tools with automatic discovery and retry
    - Memory (core + recall + archival with vector search)
    - Dynamic child agent creation
    - ReAct execution pattern
    - Sandbox isolation (CPU, memory, timeout limits)
    - Data isolation (agents cannot access each other's data)
    - Never-forget memory: compresses, stores, searches, and injects memories
    
    Tool Discovery:
    - Pass tools directly: Agent(tools=[my_tool])
    - Auto-discover from registry: Agent(auto_tools=True)
    - Auto-discover for task: Agent(auto_tools="search database")
    - Combine both: Agent(tools=[must_have], auto_tools=True)
    
    Tool Retry:
    - On tool failure, automatically tries similar tools
    - Set tool_retry=3 for max retry attempts (default: 0 = disabled)
    
    Sandbox Isolation:
    - Each agent runs in an isolated sandbox by default
    - Configure with sandbox_config parameter
    - Prevents resource abuse and data leakage
    
    Never-Forget Memory:
    - Pass vectordb and embedder for long-term memory
    - Auto-archives evicted recall entries
    - Searches relevant memories and injects into context
    - Persists across sessions when using persistent vectordb
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
        auto_tools: Union[bool, str] = False,
        tool_retry: int = 0,
        tool_categories: List[str] = None,
        sandbox_config: SandboxConfig = None,
        enable_isolation: bool = True,
        tenant_id: str = None,
        # Never-forget memory options
        vectordb: BaseVectorDB = None,
        embedder: Embedder = None,
        auto_archive: bool = True,
        auto_inject_memories: bool = True,
        memory_search_limit: int = 3,
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.llm_model = llm
        self.llm_router = llm_router
        self.max_iterations = max_iterations
        self.parent = parent
        self._state = AgentState.CREATED
        self._children: List["Agent"] = []
        self._spawner = spawner or (parent._spawner if parent else self._default_spawner)
        self._tool_retry = tool_retry
        self._tool_selector: Optional[ToolSelector] = None
        
        # Sandbox for isolated execution
        self._sandbox = Sandbox(sandbox_config or SandboxConfig())
        self._sandbox_config = sandbox_config
        
        # Data isolation
        self._enable_isolation = enable_isolation
        self._tenant_id = tenant_id or (parent._tenant_id if parent else None)
        if enable_isolation:
            self._namespace = _global_isolation.register_agent(self.id, self._tenant_id)
        else:
            self._namespace = f"agent:{self.id}"
        
        # Build tool set
        self.tools = {}
        
        # Add explicitly provided tools
        if tools:
            for t in tools:
                self.tools[t.name] = t
        
        # Auto-discover tools from global registry
        if auto_tools:
            registry = get_tool_registry()
            
            if isinstance(auto_tools, str):
                # Search by task description
                category_filter = tool_categories[0] if tool_categories and len(tool_categories) > 0 else None
                matches = registry.search(auto_tools, limit=10, category=category_filter)
                for m in matches:
                    if m.tool.name not in self.tools:
                        self.tools[m.tool.name] = m.tool
            elif tool_categories and len(tool_categories) > 0:
                # Get tools from specific categories
                for cat in tool_categories:
                    for t in registry.get_by_category(cat):
                        if t.name not in self.tools:
                            self.tools[t.name] = t
            else:
                # Get all registered tools
                for name in registry.list_all():
                    t = registry.get(name)
                    if t and t.name not in self.tools:
                        self.tools[t.name] = t
        
        # Setup tool selector for retry
        if tool_retry > 0:
            self._tool_selector = ToolSelector(get_tool_registry(), max_retries=tool_retry)
        
        # Never-forget memory system
        self._vectordb = vectordb
        self._embedder = embedder
        self._auto_inject_memories = auto_inject_memories
        self._memory_search_limit = memory_search_limit
        
        # Use full MemoryController if vectordb provided, otherwise basic memory
        if vectordb:
            self._memory = MemoryController(
                agent_id=self.id,
                name=name,
                persona=role,
                capabilities=list(self.tools.keys()),
                vectordb=vectordb,
                embedder=embedder,
                auto_archive=auto_archive,
                auto_extract_facts=True,
            )
            self._core_memory = self._memory.core
            self._recall_memory = self._memory.recall
        else:
            self._memory = None
            self._core_memory = CoreMemory(
                agent_id=self.id,
                name=name,
                persona=role,
                capabilities=list(self.tools.keys()),
            )
            self._recall_memory = RecallMemory()
        
        # Context compressor for token management
        self._compressor = ContextCompressor()
        
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
        
        Never-Forget Memory:
        1. Search archival memory for relevant past memories
        2. Inject relevant memories into context
        3. Execute task with enriched context
        4. Auto-archive important information
        5. Flush to archival on completion
        """
        self._state = AgentState.RUNNING
        
        # Search and inject relevant memories from archival
        if self._memory and self._auto_inject_memories:
            await self._inject_relevant_memories(task)
        
        # Use MemoryController if available, otherwise basic recall
        if self._memory:
            self._memory.push_recall(task, role="user")
        else:
            self._recall_memory.push(task, role="user")
        
        try:
            for iteration in range(self.max_iterations):
                response = await self._think()
                
                if response.get("done"):
                    self._state = AgentState.DONE
                    # Flush any pending memories to archival
                    if self._memory:
                        await self._memory.flush_to_archival()
                    return response.get("result")
                
                if tool_call := response.get("tool_call"):
                    result = await self._execute_tool(
                        tool_call["name"],
                        tool_call["arguments"]
                    )
                    tool_result = f"[Tool Result] {tool_call['name']}: {result}"
                    if self._memory:
                        self._memory.push_recall(tool_result, role="user")
                    else:
                        self._recall_memory.push(tool_result, role="user")
            
            self._state = AgentState.DONE
            # Flush any pending memories to archival
            if self._memory:
                await self._memory.flush_to_archival()
            return {"error": "Max iterations reached"}
            
        except Exception as e:
            self._state = AgentState.RECOVERING
            await self._recover(e)
            raise
    
    async def _inject_relevant_memories(self, task: str) -> None:
        """Search archival memory and inject relevant memories into context."""
        if not self._memory or not self._memory.archival:
            return
        
        try:
            # Search archival memory for relevant past memories
            memories = await self._memory.search_archival(task, limit=self._memory_search_limit)
            
            if memories:
                # Format memories for injection
                memory_context = "[Relevant memories from past sessions]\n"
                for mem in memories:
                    memory_context += f"- {mem.content}\n"
                
                # Inject as system context
                self._recall_memory.push(memory_context, role="system")
        except Exception:
            # Don't fail if memory search fails
            pass
    
    async def remember(self, content: str, metadata: dict = None) -> Optional[str]:
        """
        Explicitly store something in long-term archival memory.
        
        Use this for important information that should persist across sessions.
        Returns the memory ID if stored, None if no archival memory configured.
        """
        if self._memory:
            return await self._memory.store_archival(content, metadata)
        return None
    
    async def recall(self, query: str, limit: int = 5) -> List[Any]:
        """
        Search long-term archival memory for relevant information.
        
        Returns list of ArchivalEntry objects with content and metadata.
        """
        if self._memory:
            return await self._memory.search_archival(query, limit)
        return []
    
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
        
        # Only push non-empty assistant responses
        if response.content:
            if self._memory:
                self._memory.push_recall(response.content, role="assistant")
            else:
                self._recall_memory.push(response.content, role="assistant")
        
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
        """Execute a tool by name with optional retry on failure."""
        tool = self.tools.get(name)
        
        if not tool:
            # Try to find tool in global registry
            registry = get_tool_registry()
            tool = registry.get(name)
            if tool:
                self.tools[name] = tool
        
        if not tool:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        
        try:
            return await tool.execute(**arguments)
        except Exception as e:
            # If retry is enabled, try alternative tools
            if self._tool_selector and self._tool_retry > 0:
                result = await self._tool_selector.execute_with_retry(
                    task_description=tool.description,
                    arguments=arguments
                )
                if result.success:
                    return result.result
                raise ToolNotFoundError(f"Tool '{name}' and alternatives failed: {result.error}")
            raise
    
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
        
        # Remove from spawner tracking to prevent memory leak
        self._spawner.remove_agent(self.id)
        
        # Unregister from data isolation
        if self._enable_isolation:
            _global_isolation.unregister_agent(self.id)
    
    # --- Data Isolation Methods ---
    
    def isolate_data(self, data: dict) -> dict:
        """Add isolation metadata to data, ensuring it's namespaced to this agent.
        
        Other agents cannot access this data unless explicitly granted access.
        """
        if not self._enable_isolation:
            return data
        return _global_isolation.isolate_data(data, self.id)
    
    def can_access(self, resource: str) -> bool:
        """Check if this agent can access a resource.
        
        Returns True if:
        - Isolation is disabled
        - Resource is in agent's namespace
        - Agent has been granted explicit access
        """
        if not self._enable_isolation:
            return True
        return _global_isolation.validate_access(self.id, resource)
    
    def grant_access_to(self, other_agent: "Agent", resource: str = None) -> None:
        """Grant another agent access to this agent's data.
        
        Args:
            other_agent: The agent to grant access to
            resource: Specific resource to grant access to (default: this agent's namespace)
        """
        if not self._enable_isolation:
            return
        resource = resource or self._namespace
        _global_isolation.grant_access(other_agent.id, resource)
    
    def revoke_access_from(self, other_agent: "Agent", resource: str = None) -> None:
        """Revoke another agent's access to this agent's data."""
        if not self._enable_isolation:
            return
        resource = resource or self._namespace
        _global_isolation.revoke_access(other_agent.id, resource)
    
    @property
    def namespace(self) -> str:
        """Get this agent's data namespace."""
        return self._namespace
    
    @property
    def sandbox(self) -> Sandbox:
        """Get this agent's sandbox for isolated execution."""
        return self._sandbox
    
    async def execute_isolated(self, func, *args, **kwargs) -> Any:
        """Execute a function in this agent's sandbox.
        
        The sandbox enforces:
        - CPU limits
        - Memory limits  
        - Timeout limits
        
        Raises SandboxTimeoutError if execution exceeds timeout.
        """
        return await self._sandbox.execute(func, *args, **kwargs)
    
    def __eq__(self, other):
        if not isinstance(other, Agent):
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
