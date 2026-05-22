import pytest
from agentic_swarm.compliance.audit import AuditLogger, AuditEventType
from agentic_swarm.compliance.encryption import Encryption
from agentic_swarm.compliance.isolation import DataIsolation, RBACManager


def test_audit_log():
    logger = AuditLogger(in_memory=True)
    
    entry = logger.log(
        AuditEventType.AGENT_CREATED,
        agent_id="agent-1",
        data={"name": "TestAgent"},
    )
    
    assert entry.event_type == AuditEventType.AGENT_CREATED
    assert entry.agent_id == "agent-1"
    assert entry.checksum


def test_audit_query():
    logger = AuditLogger(in_memory=True)
    
    logger.log(AuditEventType.AGENT_CREATED, agent_id="agent-1")
    logger.log(AuditEventType.TASK_STARTED, agent_id="agent-1")
    logger.log(AuditEventType.AGENT_CREATED, agent_id="agent-2")
    
    results = logger.query(event_type=AuditEventType.AGENT_CREATED)
    
    assert len(results) == 2


def test_audit_integrity():
    logger = AuditLogger(in_memory=True)
    
    logger.log(AuditEventType.AGENT_CREATED, agent_id="agent-1")
    logger.log(AuditEventType.TASK_STARTED, agent_id="agent-1")
    
    assert logger.verify_integrity() is True


def test_encryption_generate_key():
    key = Encryption.generate_key()
    assert len(key) > 0


def test_encryption_encrypt_decrypt():
    key = Encryption.generate_key()
    crypto = Encryption(key)
    
    original = "sensitive data"
    encrypted = crypto.encrypt(original)
    decrypted = crypto.decrypt_string(encrypted)
    
    assert decrypted == original
    assert encrypted != original.encode()


def test_encryption_derive_key():
    key, salt = Encryption.derive_key("password123")
    key2, _ = Encryption.derive_key("password123", salt)
    
    assert key == key2


def test_encryption_hash():
    hash1 = Encryption.hash_data("test")
    hash2 = Encryption.hash_data("test")
    hash3 = Encryption.hash_data("different")
    
    assert hash1 == hash2
    assert hash1 != hash3


def test_isolation_register():
    isolation = DataIsolation()
    
    namespace = isolation.register_agent("agent-1")
    
    assert "agent-1" in namespace


def test_isolation_validate_access():
    isolation = DataIsolation()
    isolation.register_agent("agent-1")
    isolation.register_agent("agent-2")
    
    assert isolation.validate_access("agent-1", "agent:agent-1:data") is True
    assert isolation.validate_access("agent-1", "agent:agent-2:data") is False


def test_isolation_grant_access():
    isolation = DataIsolation()
    isolation.register_agent("agent-1")
    
    isolation.grant_access("agent-1", "shared:resource")
    
    assert isolation.validate_access("agent-1", "shared:resource") is True


def test_rbac_permissions():
    rbac = RBACManager()
    
    rbac.create_role("admin", {"read", "write", "delete"})
    rbac.create_role("viewer", {"read"})
    
    rbac.assign_role("agent-1", "admin")
    rbac.assign_role("agent-2", "viewer")
    
    assert rbac.has_permission("agent-1", "write") is True
    assert rbac.has_permission("agent-2", "write") is False
    assert rbac.has_permission("agent-2", "read") is True
