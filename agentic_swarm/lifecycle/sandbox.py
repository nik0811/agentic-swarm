import asyncio
from collections.abc import Callable
from typing import Any

from ..core.exceptions import SandboxTimeoutError


class SandboxConfig:
    def __init__(
        self,
        cpu_limit: float = 1.0,
        memory_limit_mb: int = 512,
        timeout_seconds: int = 60,
        allow_network: bool = True,
    ):
        self.cpu_limit = cpu_limit
        self.memory_limit_mb = memory_limit_mb
        self.timeout_seconds = timeout_seconds
        self.allow_network = allow_network


class Sandbox:
    """Isolated execution environment for agents."""

    def __init__(self, config: SandboxConfig = None):
        self.config = config or SandboxConfig()
        self._active = False

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function in the sandbox."""
        self._active = True

        try:
            result = await asyncio.wait_for(
                self._run_with_limits(func, *args, **kwargs),
                timeout=self.config.timeout_seconds,
            )
            return result
        except asyncio.TimeoutError as e:
            raise SandboxTimeoutError(
                f"Execution exceeded {self.config.timeout_seconds}s timeout"
            ) from e
        finally:
            self._active = False

    async def _run_with_limits(self, func: Callable, *args, **kwargs) -> Any:
        """Run function with resource limits."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    @property
    def is_active(self) -> bool:
        return self._active


class SandboxManager:
    """Manage multiple sandboxes."""

    def __init__(self):
        self._sandboxes: dict[str, Sandbox] = {}

    def create_sandbox(self, agent_id: str, config: SandboxConfig = None) -> Sandbox:
        """Create a sandbox for an agent."""
        sandbox = Sandbox(config)
        self._sandboxes[agent_id] = sandbox
        return sandbox

    def get_sandbox(self, agent_id: str) -> Sandbox | None:
        """Get sandbox for an agent."""
        return self._sandboxes.get(agent_id)

    def destroy_sandbox(self, agent_id: str) -> None:
        """Destroy a sandbox."""
        self._sandboxes.pop(agent_id, None)

    def destroy_all(self) -> None:
        """Destroy all sandboxes."""
        self._sandboxes.clear()
