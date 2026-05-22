from enum import Enum
from typing import Any, Callable, TypeVar
from pydantic import BaseModel


class AgentState(Enum):
    """State of an agent."""
    CREATED = "created"
    RUNNING = "running"
    WAITING = "waiting"
    RECOVERING = "recovering"
    DONE = "done"
    TERMINATED = "terminated"


class MessageType(str, Enum):
    TASK_DELEGATE = "task_delegate"
    TASK_RESULT = "task_result"
    CONTEXT_SHARE = "context_share"
    HEALTH_PING = "health_ping"
    SPAWN_REQUEST = "spawn_request"

class TaskComplexity(str, Enum):
    TRIVIAL = "trivial"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"

class AgentSpec(BaseModel):
    name: str
    role: str
    tools: list[str] = []
    llm: str | None = None
    max_iterations: int = 10
    timeout: int = 300
    parent_id: str | None = None

class Message(BaseModel):
    id: str
    type: MessageType
    sender_id: str
    receiver_id: str | None
    content: Any
    timestamp: float