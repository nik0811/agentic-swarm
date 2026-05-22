"""
Example: Security & Compliance Features

Demonstrates audit logging, encryption, data isolation, and access control.
"""

import asyncio
from agentic_swarm.compliance import AuditLogger, Encryption, DataIsolation, AuditEventType
from agentic_swarm.compliance.access import AccessController, Permission, AccessPolicy


def demonstrate_audit_logging():
    """Immutable audit log with checksum chain."""
    print("=== Audit Logging ===")
    audit = AuditLogger()

    audit.log(AuditEventType.AGENT_CREATED, agent_id="agent-001", data={"name": "researcher"})
    audit.log(AuditEventType.TOOL_INVOKED, agent_id="agent-001", data={"tool": "web_search", "query": "AI news"})
    audit.log(AuditEventType.AGENT_TERMINATED, agent_id="agent-001", data={"reason": "task_complete"})

    print(f"  Total entries: {len(audit._entries)}")
    print(f"  Integrity valid: {audit.verify_integrity()}")

    entries = audit.query(agent_id="agent-001")
    print(f"  Agent-001 events: {len(entries)}")
    for e in entries:
        print(f"    [{e.event_type.value}] {e.data}")


def demonstrate_encryption():
    """AES-256 encryption with key rotation."""
    print("\n=== Encryption ===")
    key = Encryption.generate_key()
    crypto = Encryption(key)

    sensitive = "User SSN: 123-45-6789"
    encrypted = crypto.encrypt(sensitive)
    decrypted = crypto.decrypt_string(encrypted)

    print(f"  Original:  {sensitive}")
    print(f"  Encrypted: {encrypted[:40]}...")
    print(f"  Decrypted: {decrypted}")
    print(f"  Match: {sensitive == decrypted}")

    new_key = Encryption.generate_key()
    re_encrypted = crypto.rotate_key(new_key, [encrypted])
    print(f"  Key rotated, re-encrypted {len(re_encrypted)} item(s)")


def demonstrate_data_isolation():
    """Tenant-based data isolation."""
    print("\n=== Data Isolation ===")
    isolation = DataIsolation()

    isolation.register_agent("agent-1", tenant_id="acme-corp")
    isolation.register_agent("agent-2", tenant_id="acme-corp")
    isolation.register_agent("agent-3", tenant_id="other-corp")

    print(f"  agent-1 → own data: {isolation.validate_access('agent-1', 'agent:agent-1:data')}")
    print(f"  agent-1 → agent-2 (same tenant): {isolation.validate_access('agent-1', 'agent:agent-2:data')}")
    print(f"  agent-1 → agent-3 (diff tenant): {isolation.validate_access('agent-1', 'agent:agent-3:data')}")


def demonstrate_access_control():
    """Fine-grained permission, tool, and model ACLs."""
    print("\n=== Access Control ===")
    controller = AccessController()

    policy = AccessPolicy(
        agent_id="agent-1",
        permissions={Permission.READ, Permission.WRITE, Permission.EXECUTE},
        allowed_tools=["web_search", "read_file", "calculator"],
        denied_tools=["run_shell", "delete_file"],
        allowed_models=["gpt-4o-mini", "gpt-4o"],
        rate_limit_per_minute=30,
    )
    controller.set_policy("agent-1", policy)

    print(f"  READ permission: {controller.check_permission('agent-1', Permission.READ)}")
    print(f"  ADMIN permission: {controller.check_permission('agent-1', Permission.ADMIN)}")
    print(f"  web_search tool: {controller.check_tool_access('agent-1', 'web_search')}")
    print(f"  run_shell tool: {controller.check_tool_access('agent-1', 'run_shell')}")
    print(f"  gpt-4o model: {controller.check_model_access('agent-1', 'gpt-4o')}")
    print(f"  claude model: {controller.check_model_access('agent-1', 'claude-3-opus')}")


if __name__ == "__main__":
    demonstrate_audit_logging()
    demonstrate_encryption()
    demonstrate_data_isolation()
    demonstrate_access_control()
