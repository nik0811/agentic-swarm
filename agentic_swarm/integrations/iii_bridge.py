"""
iii Integration Bridge
======================

This module provides a bridge to run Agentic Swarm agents as iii workers.

Features:
- Agents become discoverable iii workers
- Tools become iii functions
- HTTP/Cron/Queue triggers invoke agents
- **Immortal agents**: Self-healing with state recovery exposed to iii

Usage:
    from agentic_swarm import Agent
    from agentic_swarm.integrations.iii_bridge import IIIWorkerBridge
    
    agent = Agent(name="my_agent", role="Do stuff", tools=[...])
    bridge = IIIWorkerBridge(agent, immortal=True)
    
    # Register with iii engine
    bridge.start()  # Blocks and handles requests

Requirements:
    pip install iii-sdk
"""

from typing import Any, Callable, Dict, List, Optional
import asyncio
import time

try:
    from iii import Worker
    III_AVAILABLE = True
except ImportError:
    III_AVAILABLE = False
    Worker = None

# Import lifecycle components for immortal agents
from ..lifecycle.supervisor import Supervisor, HealthStatus, AgentHealth
from ..lifecycle.healer import Healer, StateSnapshot
from ..core.types import AgentState


class IIIWorkerBridge:
    """
    Bridge between Agentic Swarm Agent and iii Worker.
    
    Maps:
      - Agent       → iii Worker
      - Agent.run() → iii Function (main entry point)
      - Tools       → iii Functions (individually callable)
      - Triggers    → HTTP / Cron / Queue → Agent.run()
    
    Immortal Mode:
      - Supervisor monitors agent health
      - Healer auto-recovers from failures with state snapshots
      - Health status exposed to iii for observability
    """
    
    def __init__(
        self,
        agent: "Agent",
        worker_name: str = None,
        http_path: str = None,
        cron_schedule: str = None,
        queue_topic: str = None,
        immortal: bool = True,
        health_check_interval: float = 5.0,
        max_recovery_retries: int = 3,
    ):
        """
        Initialize the bridge.
        
        Args:
            agent: Agentic Swarm Agent instance
            worker_name: Name for the iii worker (default: swarm-{agent.name})
            http_path: HTTP trigger path (default: /{agent.name})
            cron_schedule: Cron schedule for periodic execution (e.g., "*/5 * * * *")
            queue_topic: Queue topic to subscribe to
            immortal: Enable self-healing with state recovery (default: True)
            health_check_interval: Seconds between health checks (default: 5.0)
            max_recovery_retries: Max recovery attempts before giving up (default: 3)
        """
        if not III_AVAILABLE:
            raise ImportError(
                "iii-sdk is not installed. Install with: pip install iii-sdk"
            )
        
        self.agent = agent
        self.worker_name = worker_name or f"swarm-{agent.name}"
        self.http_path = http_path or f"/{agent.name}"
        self.cron_schedule = cron_schedule
        self.queue_topic = queue_topic
        
        self._worker: Optional[Worker] = None
        self._registered_functions: List[str] = []
        
        # Immortal agent components
        self._immortal = immortal
        self._supervisor: Optional[Supervisor] = None
        self._healer: Optional[Healer] = None
        self._health_check_interval = health_check_interval
        self._max_recovery_retries = max_recovery_retries
        self._recovery_count = 0
        self._last_snapshot_time: float = 0
        
        if immortal:
            self._setup_immortality()
    
    def _setup_immortality(self):
        """Setup supervisor and healer for self-healing."""
        self._healer = Healer(
            max_retries=self._max_recovery_retries,
            backoff_factor=2.0,
        )
        
        self._supervisor = Supervisor(
            check_interval=self._health_check_interval,
            max_errors=self._max_recovery_retries,
            on_failure=self._on_agent_failure,
        )
        
        self._supervisor.register(self.agent)
    
    async def _on_agent_failure(self, agent: "Agent", health: AgentHealth):
        """Handle agent failure - attempt recovery."""
        print(f"[IMMORTAL] Agent {agent.name} failed: {health.last_error}")
        print(f"[IMMORTAL] Attempting recovery ({self._recovery_count + 1}/{self._max_recovery_retries})...")
        
        try:
            # Attempt recovery with healer
            recovered = await self._healer.recover(agent, Exception(health.last_error or "Unknown error"))
            
            if recovered:
                self._recovery_count += 1
                self._supervisor.reset_errors(agent.id)
                print(f"[IMMORTAL] Agent {agent.name} recovered successfully!")
            else:
                print(f"[IMMORTAL] Agent {agent.name} recovery failed - max retries exceeded")
        except Exception as e:
            print(f"[IMMORTAL] Recovery error: {e}")
    
    def _take_snapshot(self):
        """Take a state snapshot for recovery."""
        if self._healer and self._immortal:
            self._healer.snapshot(self.agent)
            self._last_snapshot_time = time.time()
    
    async def _run_with_immortality(self, task: str) -> Any:
        """Run agent task with immortality wrapper."""
        # Take snapshot before execution
        self._take_snapshot()
        
        try:
            result = await self.agent.run(task)
            
            # Reset error count on success
            if self._supervisor:
                self._supervisor.reset_errors(self.agent.id)
            
            return result
            
        except Exception as e:
            # Record error
            if self._supervisor:
                self._supervisor.record_error(self.agent.id, str(e))
            
            # Attempt recovery
            if self._healer:
                recovered = await self._healer.recover(self.agent, e)
                if recovered:
                    # Retry the task after recovery
                    return await self.agent.run(task)
            
            raise
    
    def get_health_status(self) -> Dict:
        """Get current health status (exposed to iii)."""
        if not self._supervisor:
            return {
                "status": "unknown",
                "immortal": False,
            }
        
        health = self._supervisor.health_check(self.agent.id)
        snapshot = self._healer.get_snapshot(self.agent.id) if self._healer else None
        
        return {
            "status": health.status.value,
            "immortal": self._immortal,
            "agent_state": self.agent.state.value,
            "error_count": health.error_count,
            "last_error": health.last_error,
            "recovery_count": self._recovery_count,
            "max_retries": self._max_recovery_retries,
            "last_snapshot": self._last_snapshot_time,
            "has_snapshot": snapshot is not None,
            "uptime": time.time() - health.last_check if health.last_check else 0,
        }
    
    def get_function_catalog(self) -> List[Dict]:
        """Get all functions this worker exposes to iii."""
        functions = []
        
        # Main agent entry point
        functions.append({
            "id": f"{self.agent.name}::run",
            "description": f"Run the {self.agent.name} agent with a task (immortal: auto-recovers on failure)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Task for the agent"}
                },
                "required": ["task"]
            },
        })
        
        # Health check function (for immortal agents)
        if self._immortal:
            functions.append({
                "id": f"{self.agent.name}::health",
                "description": f"Get health status of {self.agent.name} agent (immortal mode)",
                "input_schema": {"type": "object", "properties": {}},
            })
            
            functions.append({
                "id": f"{self.agent.name}::snapshot",
                "description": f"Take a state snapshot of {self.agent.name} for recovery",
                "input_schema": {"type": "object", "properties": {}},
            })
            
            functions.append({
                "id": f"{self.agent.name}::recover",
                "description": f"Manually trigger recovery of {self.agent.name} from last snapshot",
                "input_schema": {"type": "object", "properties": {}},
            })
        
        # Individual tools as functions
        for tool_obj in self.agent.tools.values():
            schema = tool_obj.to_openai_schema()["function"]
            functions.append({
                "id": f"{self.agent.name}::{tool_obj.name}",
                "description": schema["description"],
                "input_schema": schema["parameters"],
            })
        
        return functions
    
    def build_worker(self) -> Worker:
        """Build the iii Worker with all functions and triggers."""
        worker = Worker(name=self.worker_name)
        
        # Register main agent.run function (with immortality wrapper)
        @worker.function(f"{self.agent.name}::run")
        async def run_agent(task: str) -> Any:
            if self._immortal:
                return await self._run_with_immortality(task)
            return await self.agent.run(task)
        
        self._registered_functions.append(f"{self.agent.name}::run")
        
        # Register immortal agent functions
        if self._immortal:
            @worker.function(f"{self.agent.name}::health")
            async def get_health() -> Dict:
                return self.get_health_status()
            
            self._registered_functions.append(f"{self.agent.name}::health")
            
            @worker.function(f"{self.agent.name}::snapshot")
            async def take_snapshot() -> Dict:
                self._take_snapshot()
                return {
                    "success": True,
                    "timestamp": self._last_snapshot_time,
                    "agent": self.agent.name,
                }
            
            self._registered_functions.append(f"{self.agent.name}::snapshot")
            
            @worker.function(f"{self.agent.name}::recover")
            async def manual_recover() -> Dict:
                if self._healer:
                    snapshot = self._healer.get_snapshot(self.agent.id)
                    if snapshot:
                        await self._healer.restore(self.agent, snapshot)
                        return {
                            "success": True,
                            "restored_from": snapshot.timestamp,
                            "agent": self.agent.name,
                        }
                return {"success": False, "error": "No snapshot available"}
            
            self._registered_functions.append(f"{self.agent.name}::recover")
        
        # Register each tool as a separate function
        for tool_name, tool_obj in self.agent.tools.items():
            fn_id = f"{self.agent.name}::{tool_name}"
            
            # Create closure to capture tool_obj
            def make_tool_handler(t):
                async def handler(**kwargs) -> Any:
                    return await self.agent.execute_isolated(t.execute, **kwargs)
                return handler
            
            worker.function(fn_id)(make_tool_handler(tool_obj))
            self._registered_functions.append(fn_id)
        
        # Add HTTP trigger if configured
        if self.http_path:
            @worker.trigger("http", path=self.http_path)
            async def http_handler(request: dict) -> Any:
                task = request.get("body", {}).get("task", "")
                return await self.agent.run(task)
        
        # Add cron trigger if configured
        if self.cron_schedule:
            @worker.trigger("cron", schedule=self.cron_schedule)
            async def cron_handler() -> Any:
                return await self.agent.run("Scheduled execution")
        
        # Add queue trigger if configured
        if self.queue_topic:
            @worker.trigger("queue", topic=self.queue_topic)
            async def queue_handler(message: dict) -> Any:
                task = message.get("task", str(message))
                return await self.agent.run(task)
        
        self._worker = worker
        return worker
    
    def start(self, blocking: bool = True):
        """
        Start the iii worker.
        
        Args:
            blocking: If True, blocks until worker is stopped
        """
        if self._worker is None:
            self.build_worker()
        
        if blocking:
            self._worker.start()
        else:
            # Start in background
            import threading
            thread = threading.Thread(target=self._worker.start, daemon=True)
            thread.start()
            return thread
    
    def stop(self):
        """Stop the iii worker."""
        if self._worker:
            self._worker.stop()


class IIISwarmBridge:
    """
    Bridge an entire Agentic Swarm to iii as a worker group.
    
    Each agent becomes a separate iii worker, all discoverable
    in the iii catalog.
    """
    
    def __init__(
        self,
        swarm: "Swarm",
        group_name: str = None,
    ):
        """
        Initialize the swarm bridge.
        
        Args:
            swarm: Agentic Swarm instance
            group_name: Name for the worker group
        """
        if not III_AVAILABLE:
            raise ImportError(
                "iii-sdk is not installed. Install with: pip install iii-sdk"
            )
        
        self.swarm = swarm
        self.group_name = group_name or "agentic-swarm"
        self._bridges: List[IIIWorkerBridge] = []
    
    def build_workers(self) -> List[Worker]:
        """Build iii workers for all agents in the swarm."""
        workers = []
        
        for agent in self.swarm.agents:
            bridge = IIIWorkerBridge(
                agent=agent,
                worker_name=f"{self.group_name}-{agent.name}",
            )
            self._bridges.append(bridge)
            workers.append(bridge.build_worker())
        
        return workers
    
    def get_catalog(self) -> Dict:
        """Get the full function catalog for this swarm."""
        if not self._bridges:
            self.build_workers()
        
        return {
            "group": self.group_name,
            "workers": [
                {
                    "name": b.worker_name,
                    "agent": b.agent.name,
                    "role": b.agent.role,
                    "namespace": b.agent.namespace,
                    "functions": b.get_function_catalog(),
                }
                for b in self._bridges
            ]
        }
    
    def start_all(self, blocking: bool = False):
        """
        Start all workers.
        
        Args:
            blocking: If True, blocks on the last worker
        """
        if not self._bridges:
            self.build_workers()
        
        threads = []
        for i, bridge in enumerate(self._bridges):
            is_last = (i == len(self._bridges) - 1)
            if blocking and is_last:
                bridge.start(blocking=True)
            else:
                thread = bridge.start(blocking=False)
                threads.append(thread)
        
        return threads
    
    def stop_all(self):
        """Stop all workers."""
        for bridge in self._bridges:
            bridge.stop()


# Convenience function
def register_agent_with_iii(
    agent: "Agent",
    http_path: str = None,
    cron_schedule: str = None,
    queue_topic: str = None,
) -> IIIWorkerBridge:
    """
    Quick helper to register an agent with iii.
    
    Example:
        from agentic_swarm import Agent
        from agentic_swarm.integrations.iii_bridge import register_agent_with_iii
        
        agent = Agent(name="researcher", role="Research", tools=[...])
        bridge = register_agent_with_iii(
            agent,
            http_path="/research",
            cron_schedule="0 * * * *",  # Every hour
        )
        bridge.start()
    """
    bridge = IIIWorkerBridge(
        agent=agent,
        http_path=http_path,
        cron_schedule=cron_schedule,
        queue_topic=queue_topic,
    )
    return bridge


def register_swarm_with_iii(swarm: "Swarm", group_name: str = None) -> IIISwarmBridge:
    """
    Quick helper to register an entire swarm with iii.
    
    Example:
        from agentic_swarm import Swarm
        from agentic_swarm.integrations.iii_bridge import register_swarm_with_iii
        
        swarm = Swarm(agents=[agent1, agent2, agent3])
        bridge = register_swarm_with_iii(swarm, group_name="my-ai-team")
        bridge.start_all()
    """
    return IIISwarmBridge(swarm=swarm, group_name=group_name)
