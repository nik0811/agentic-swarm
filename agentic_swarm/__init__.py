# Optional integrations (available if dependencies installed)
from . import integrations
from .agent import Agent, get_tool_registry, register_tool
from .core.config import SDKConfig, get_config, reset_config, set_config
from .swarm import Swarm, SwarmResult
from .tool import tool
from .tools.base import Tool, ToolSchema
from .tools.registry import ToolRegistry

__version__ = "0.2.1"
__all__ = [
    "Agent",
    "Swarm",
    "SwarmResult",
    "tool",
    "Tool",
    "ToolSchema",
    "ToolRegistry",
    "SDKConfig",
    "get_config",
    "set_config",
    "reset_config",
    "register_tool",
    "get_tool_registry",
    "integrations",
]
