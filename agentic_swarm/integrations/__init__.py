"""
Integrations with external platforms.

Available integrations:
- iii_bridge: Run Agentic Swarm agents as iii workers
"""

from .iii_bridge import III_AVAILABLE

# Only expose bridge classes if iii-sdk is available
if III_AVAILABLE:
    from .iii_bridge import (
        IIISwarmBridge,
        IIIWorkerBridge,
        register_agent_with_iii,
        register_swarm_with_iii,
    )
else:
    IIIWorkerBridge = None
    IIISwarmBridge = None
    register_agent_with_iii = None
    register_swarm_with_iii = None

__all__ = [
    "III_AVAILABLE",
    "IIIWorkerBridge",
    "IIISwarmBridge",
    "register_agent_with_iii",
    "register_swarm_with_iii",
]
