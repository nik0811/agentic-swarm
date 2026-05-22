"""
Agentic Swarm — Sandbox & Data Isolation Example
=================================================

This example demonstrates:
1. Sandbox isolation - Each agent runs with resource limits
2. Data isolation - Agents cannot access each other's data
3. Explicit access grants - Controlled data sharing between agents
4. Tenant isolation - Multi-tenant data separation

Run: python examples/sandbox_isolation.py
"""

import asyncio
from agentic_swarm import Agent, tool
from agentic_swarm.lifecycle.sandbox import SandboxConfig
from agentic_swarm.compliance.isolation import DataIsolation


# =============================================================================
# Tools for demonstration
# =============================================================================

@tool
def compute_heavy(n: int) -> int:
    """Compute sum of range (simulates CPU-intensive work)."""
    return sum(range(n))


@tool
def store_secret(secret: str) -> dict:
    """Store a secret value."""
    return {"secret": secret, "stored": True}


# =============================================================================
# Main Example
# =============================================================================

async def main():
    print("=" * 70)
    print("  AGENTIC SWARM — Sandbox & Data Isolation Example")
    print("=" * 70)
    
    # =========================================================================
    # 1. Sandbox Isolation
    # =========================================================================
    print("\n[1] SANDBOX ISOLATION")
    print("-" * 50)
    
    # Create agent with custom sandbox config
    sandbox_config = SandboxConfig(
        cpu_limit=1.0,           # 1 CPU core
        memory_limit_mb=256,     # 256 MB memory
        timeout_seconds=5,       # 5 second timeout
        allow_network=False,     # No network access
    )
    
    agent_a = Agent(
        name="agent_a",
        role="Compute agent with sandbox limits",
        tools=[compute_heavy],
        sandbox_config=sandbox_config,
    )
    
    print(f"    Agent: {agent_a.name}")
    print(f"    Sandbox config:")
    print(f"      - CPU limit: {sandbox_config.cpu_limit} cores")
    print(f"      - Memory limit: {sandbox_config.memory_limit_mb} MB")
    print(f"      - Timeout: {sandbox_config.timeout_seconds} seconds")
    print(f"      - Network: {'allowed' if sandbox_config.allow_network else 'blocked'}")
    
    # Execute function in sandbox
    print("\n    Executing compute_heavy(10000) in sandbox...")
    result = await agent_a.execute_isolated(compute_heavy.func, 10000)
    print(f"    Result: {result}")
    
    # Demonstrate timeout (would fail with large n)
    print("\n    Sandbox prevents runaway computations via timeout.")
    
    # =========================================================================
    # 2. Data Isolation Between Agents
    # =========================================================================
    print("\n[2] DATA ISOLATION BETWEEN AGENTS")
    print("-" * 50)
    
    # Create two agents with isolation enabled (default)
    agent_alice = Agent(
        name="alice",
        role="Agent Alice with private data",
        enable_isolation=True,
    )
    
    agent_bob = Agent(
        name="bob", 
        role="Agent Bob with private data",
        enable_isolation=True,
    )
    
    print(f"    Agent Alice namespace: {agent_alice.namespace}")
    print(f"    Agent Bob namespace: {agent_bob.namespace}")
    
    # Alice creates isolated data
    alice_data = agent_alice.isolate_data({
        "secret": "Alice's secret password",
        "balance": 1000,
    })
    print(f"\n    Alice's isolated data: {alice_data}")
    
    # Bob creates isolated data
    bob_data = agent_bob.isolate_data({
        "secret": "Bob's secret password",
        "balance": 500,
    })
    print(f"    Bob's isolated data: {bob_data}")
    
    # Check access permissions
    print(f"\n    Can Alice access her own namespace? {agent_alice.can_access(agent_alice.namespace)}")
    print(f"    Can Alice access Bob's namespace? {agent_alice.can_access(agent_bob.namespace)}")
    print(f"    Can Bob access Alice's namespace? {agent_bob.can_access(agent_alice.namespace)}")
    
    # =========================================================================
    # 3. Explicit Access Grants
    # =========================================================================
    print("\n[3] EXPLICIT ACCESS GRANTS")
    print("-" * 50)
    
    # Alice grants Bob access to her namespace
    print("    Alice grants Bob access to her namespace...")
    agent_alice.grant_access_to(agent_bob)
    
    print(f"    Can Bob access Alice's namespace now? {agent_bob.can_access(agent_alice.namespace)}")
    
    # Alice revokes access
    print("\n    Alice revokes Bob's access...")
    agent_alice.revoke_access_from(agent_bob)
    
    print(f"    Can Bob access Alice's namespace now? {agent_bob.can_access(agent_alice.namespace)}")
    
    # =========================================================================
    # 4. Tenant Isolation (Multi-tenant)
    # =========================================================================
    print("\n[4] TENANT ISOLATION (MULTI-TENANT)")
    print("-" * 50)
    
    # Create agents for different tenants
    tenant1_agent = Agent(
        name="tenant1_worker",
        role="Worker for Tenant 1",
        tenant_id="tenant_001",
        enable_isolation=True,
    )
    
    tenant2_agent = Agent(
        name="tenant2_worker",
        role="Worker for Tenant 2",
        tenant_id="tenant_002",
        enable_isolation=True,
    )
    
    print(f"    Tenant 1 agent namespace: {tenant1_agent.namespace}")
    print(f"    Tenant 2 agent namespace: {tenant2_agent.namespace}")
    
    # Tenants cannot access each other's data
    print(f"\n    Can Tenant 1 access Tenant 2's namespace? {tenant1_agent.can_access(tenant2_agent.namespace)}")
    print(f"    Can Tenant 2 access Tenant 1's namespace? {tenant2_agent.can_access(tenant1_agent.namespace)}")
    
    # =========================================================================
    # 5. Parent-Child Isolation
    # =========================================================================
    print("\n[5] PARENT-CHILD ISOLATION")
    print("-" * 50)
    
    parent = Agent(
        name="parent",
        role="Parent agent",
        tenant_id="company_xyz",
        enable_isolation=True,
    )
    
    # Child inherits tenant_id from parent
    child = await parent.create_agent(
        name="child",
        role="Child agent",
    )
    
    print(f"    Parent namespace: {parent.namespace}")
    print(f"    Child namespace: {child.namespace}")
    print(f"    Child inherited tenant_id: {child._tenant_id}")
    
    # Parent and child have separate namespaces but same tenant
    print(f"\n    Can parent access child's namespace? {parent.can_access(child.namespace)}")
    print(f"    Can child access parent's namespace? {child.can_access(parent.namespace)}")
    
    # Grant access for collaboration
    print("\n    Parent grants child access to parent's namespace...")
    parent.grant_access_to(child)
    print(f"    Can child access parent's namespace now? {child.can_access(parent.namespace)}")
    
    # =========================================================================
    # 6. Isolation Disabled Mode
    # =========================================================================
    print("\n[6] ISOLATION DISABLED MODE")
    print("-" * 50)
    
    # Create agent without isolation (for testing/development)
    open_agent = Agent(
        name="open_agent",
        role="Agent without isolation",
        enable_isolation=False,
    )
    
    print(f"    Agent: {open_agent.name}")
    print(f"    Isolation enabled: {open_agent._enable_isolation}")
    print(f"    Namespace: {open_agent.namespace}")
    print(f"    Can access any resource: {open_agent.can_access('any:resource:path')}")
    
    # =========================================================================
    # Cleanup
    # =========================================================================
    print("\n[7] CLEANUP")
    print("-" * 50)
    
    await agent_a.terminate()
    await agent_alice.terminate()
    await agent_bob.terminate()
    await tenant1_agent.terminate()
    await tenant2_agent.terminate()
    await parent.terminate()
    await open_agent.terminate()
    
    print("    All agents terminated and unregistered from isolation.")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 70)
    print("  EXAMPLE COMPLETE")
    print("=" * 70)
    print("""
    Features Demonstrated:
    
    ✓ Sandbox Isolation
      - CPU, memory, and timeout limits
      - execute_isolated() for controlled execution
      - Prevents resource abuse
    
    ✓ Data Isolation
      - Each agent has a unique namespace
      - isolate_data() adds namespace metadata
      - can_access() validates permissions
    
    ✓ Access Control
      - grant_access_to() for explicit sharing
      - revoke_access_from() to remove access
      - Fine-grained resource control
    
    ✓ Multi-Tenant Support
      - tenant_id for organizational isolation
      - Tenants cannot access each other's data
      - Child agents inherit tenant_id
    
    ✓ Configurable
      - enable_isolation=True (default) for production
      - enable_isolation=False for testing
    
    Security Guarantees:
    - No data leakage between agents by default
    - Explicit grants required for cross-agent access
    - Tenant boundaries enforced
    - Resource limits prevent abuse
    """)


if __name__ == "__main__":
    asyncio.run(main())
