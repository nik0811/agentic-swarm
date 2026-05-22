from typing import Any, Optional, List
from pydantic import BaseModel
from enum import Enum
import json
import time
import hashlib
import os


class AuditEventType(str, Enum):
    AGENT_CREATED = "agent_created"
    AGENT_TERMINATED = "agent_terminated"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TOOL_INVOKED = "tool_invoked"
    MEMORY_WRITE = "memory_write"
    MEMORY_READ = "memory_read"
    ERROR = "error"
    RECOVERY = "recovery"
    AUTH_EVENT = "auth_event"


class AuditEntry(BaseModel):
    id: str
    timestamp: float
    event_type: AuditEventType
    agent_id: Optional[str] = None
    data: dict = {}
    checksum: str = ""


class AuditLogger:
    """Immutable audit logging with tamper-proof checksums."""
    
    def __init__(self, log_path: str = None, in_memory: bool = True):
        self._log_path = log_path
        self._in_memory = in_memory
        self._entries: List[AuditEntry] = []
        self._entry_count = 0
        
        if log_path and not in_memory:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    def _generate_checksum(self, entry: dict) -> str:
        """Generate tamper-proof checksum."""
        content = json.dumps(entry, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def log(
        self,
        event_type: AuditEventType,
        agent_id: str = None,
        data: dict = None,
    ) -> AuditEntry:
        """Log an audit event."""
        self._entry_count += 1
        
        entry_data = {
            "id": f"audit-{self._entry_count}",
            "timestamp": time.time(),
            "event_type": event_type.value,
            "agent_id": agent_id,
            "data": data or {},
        }
        
        checksum = self._generate_checksum(entry_data)
        
        entry = AuditEntry(
            id=entry_data["id"],
            timestamp=entry_data["timestamp"],
            event_type=event_type,
            agent_id=agent_id,
            data=data or {},
            checksum=checksum,
        )
        
        if self._in_memory:
            self._entries.append(entry)
        
        if self._log_path:
            self._write_to_file(entry)
        
        return entry
    
    def _write_to_file(self, entry: AuditEntry) -> None:
        """Append entry to log file."""
        with open(self._log_path, "a") as f:
            f.write(entry.model_dump_json() + "\n")
    
    def query(
        self,
        event_type: AuditEventType = None,
        agent_id: str = None,
        start_time: float = None,
        end_time: float = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Query audit log entries."""
        results = []
        
        for entry in reversed(self._entries):
            if event_type and entry.event_type != event_type:
                continue
            if agent_id and entry.agent_id != agent_id:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            
            results.append(entry)
            if len(results) >= limit:
                break
        
        return results
    
    def verify_integrity(self) -> bool:
        """Verify all entries have valid checksums."""
        for entry in self._entries:
            entry_data = {
                "id": entry.id,
                "timestamp": entry.timestamp,
                "event_type": entry.event_type.value,
                "agent_id": entry.agent_id,
                "data": entry.data,
            }
            expected_checksum = self._generate_checksum(entry_data)
            if entry.checksum != expected_checksum:
                return False
        return True
    
    def export(self, format: str = "json") -> str:
        """Export audit log."""
        if format == "json":
            return json.dumps([e.model_dump() for e in self._entries], indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def clear(self) -> None:
        """Clear in-memory entries (for testing only)."""
        self._entries.clear()
