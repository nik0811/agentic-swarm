"""Message protocols for agent communication."""
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class MessageType(str, Enum):
    TASK = "task"
    RESULT = "result"
    ERROR = "error"
    STATUS = "status"
    BROADCAST = "broadcast"
    DIRECT = "direct"
    HANDOFF = "handoff"
    TASK_DELEGATE = "task_delegate"
    TASK_RESULT = "task_result"
    CONTEXT_SHARE = "context_share"
    HEALTH_PING = "health_ping"
    SPAWN_REQUEST = "spawn_request"


class Priority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class Message(BaseModel):
    """Structured message for agent-to-agent communication."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.DIRECT
    sender_id: str
    receiver_id: Optional[str] = None
    content: Any = None
    metadata: Dict[str, Any] = {}
    priority: Priority = Priority.NORMAL
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reply_to: Optional[str] = None
    ttl: Optional[int] = None


class Protocol(str, Enum):
    """Communication protocol between agents."""
    REQUEST_RESPONSE = "request_response"
    PUBLISH_SUBSCRIBE = "publish_subscribe"
    FIRE_AND_FORGET = "fire_and_forget"
    STREAMING = "streaming"
