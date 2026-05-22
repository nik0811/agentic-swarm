from ...tool import tool


@tool
async def create_agent(name: str, role: str, tools: list[str] = None) -> dict:
    """Create a new sub-agent dynamically.

    Args:
        name: Name for the new agent
        role: Role/persona for the agent
        tools: List of tool names to give the agent

    Returns:
        Agent info dict with id and name
    """
    return {"status": "created", "name": name, "role": role}


@tool
async def terminate_agent(agent_id: str) -> dict:
    """Terminate an agent.

    Args:
        agent_id: ID of the agent to terminate

    Returns:
        Status of termination
    """
    return {"status": "terminated", "agent_id": agent_id}


@tool
async def list_agents() -> list[dict]:
    """List all active agents.

    Returns:
        List of agent info dicts
    """
    return []


@tool
async def send_message(target_agent_id: str, message: str) -> dict:
    """Send a message to another agent.

    Args:
        target_agent_id: ID of the target agent
        message: Message to send

    Returns:
        Status of message delivery
    """
    return {"status": "sent", "target": target_agent_id}


@tool
async def delegate_task(agent_id: str, task: str) -> dict:
    """Delegate a task to another agent.

    Args:
        agent_id: ID of the agent to delegate to
        task: Task description

    Returns:
        Task delegation status
    """
    return {"status": "delegated", "agent_id": agent_id, "task": task}
