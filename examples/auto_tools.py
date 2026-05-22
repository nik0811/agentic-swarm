"""
Auto Tool Discovery Example
===========================

Shows how the SDK automatically handles tool discovery and retry.
No complex setup needed - just register tools and create agents.
"""

import asyncio
from agentic_swarm import Agent, tool, register_tool


# =============================================================================
# 1. DEFINE AND REGISTER TOOLS (do this once at app startup)
# =============================================================================

@tool
def search_database(query: str, limit: int = 10) -> list:
    """Search database for records matching query."""
    return [{"id": 1, "name": "Result 1"}, {"id": 2, "name": "Result 2"}]

@tool
def search_cache(query: str) -> list:
    """Search cache for records (faster but may be stale)."""
    return [{"id": 1, "name": "Cached Result", "cached": True}]

@tool
def calculate_sum(numbers: list) -> float:
    """Calculate sum of numbers."""
    return sum(numbers)

@tool
def calculate_average(numbers: list) -> float:
    """Calculate average of numbers."""
    return sum(numbers) / len(numbers) if numbers else 0

@tool
def send_email(to: str, subject: str, body: str) -> dict:
    """Send email to recipient."""
    return {"status": "sent", "to": to}

@tool
def send_slack(channel: str, message: str) -> dict:
    """Send message to Slack channel."""
    return {"status": "sent", "channel": channel}

@tool  
def unreliable_api(endpoint: str) -> dict:
    """An API that sometimes fails."""
    import random
    if random.random() < 0.8:
        raise ConnectionError("API unavailable")
    return {"data": "success"}

@tool
def backup_api(endpoint: str) -> dict:
    """Backup API that always works."""
    return {"data": "from backup", "endpoint": endpoint}


# Register tools globally with categories
register_tool(search_database, category="data", keywords=["search", "query", "database", "find"])
register_tool(search_cache, category="data", keywords=["search", "cache", "fast"])
register_tool(calculate_sum, category="math", keywords=["sum", "add", "total"])
register_tool(calculate_average, category="math", keywords=["average", "mean"])
register_tool(send_email, category="notification", keywords=["email", "send", "notify"])
register_tool(send_slack, category="notification", keywords=["slack", "message", "notify"])
register_tool(unreliable_api, category="api", keywords=["api", "fetch", "data"])
register_tool(backup_api, category="api", keywords=["api", "backup", "fetch"])


# =============================================================================
# 2. CREATE AGENTS - Tools are auto-discovered!
# =============================================================================

async def main():
    print("=" * 60)
    print("  AUTO TOOL DISCOVERY EXAMPLE")
    print("=" * 60)
    
    # --- Method 1: Auto-discover ALL registered tools ---
    print("\n[1] Agent with ALL registered tools (auto_tools=True)\n")
    
    agent1 = Agent(
        name="full_agent",
        role="General assistant with all tools",
        auto_tools=True  # Gets ALL registered tools automatically
    )
    print(f"    Tools: {list(agent1.tools.keys())}")
    
    # --- Method 2: Auto-discover tools by TASK description ---
    print("\n[2] Agent with tools for specific TASK (auto_tools='...')\n")
    
    agent2 = Agent(
        name="data_agent",
        role="Data analyst",
        auto_tools="search and query database records"  # Finds relevant tools
    )
    print(f"    Task: 'search and query database records'")
    print(f"    Tools found: {list(agent2.tools.keys())}")
    
    agent3 = Agent(
        name="math_agent", 
        role="Calculator",
        auto_tools="calculate sum and average of numbers"
    )
    print(f"\n    Task: 'calculate sum and average of numbers'")
    print(f"    Tools found: {list(agent3.tools.keys())}")
    
    # --- Method 3: Auto-discover by CATEGORY ---
    print("\n[3] Agent with tools from specific CATEGORIES\n")
    
    agent4 = Agent(
        name="notifier",
        role="Notification sender",
        auto_tools=True,
        tool_categories=["notification"]  # Only notification tools
    )
    print(f"    Categories: ['notification']")
    print(f"    Tools: {list(agent4.tools.keys())}")
    
    # --- Method 4: Combine explicit + auto tools ---
    print("\n[4] Agent with explicit tools + auto-discovery\n")
    
    @tool
    def custom_tool(x: int) -> int:
        """My custom tool."""
        return x * 2
    
    agent5 = Agent(
        name="hybrid_agent",
        role="Hybrid assistant",
        tools=[custom_tool],  # Explicit tool
        auto_tools="search database",  # Plus auto-discovered
    )
    print(f"    Explicit: [custom_tool]")
    print(f"    Auto-discover: 'search database'")
    print(f"    Final tools: {list(agent5.tools.keys())}")
    
    # --- Method 5: Auto-retry on tool failure ---
    print("\n[5] Agent with automatic tool RETRY on failure\n")
    
    agent6 = Agent(
        name="resilient_agent",
        role="Resilient API caller",
        auto_tools=True,
        tool_retry=3  # Try up to 3 alternative tools on failure
    )
    print(f"    tool_retry=3 (tries alternatives if tool fails)")
    print(f"    Tools: {list(agent6.tools.keys())}")
    
    # --- Summary ---
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print("""
    Tool Discovery Options:
    
    1. auto_tools=True
       → Gets ALL registered tools
    
    2. auto_tools="task description"  
       → Finds tools matching the task
    
    3. tool_categories=["cat1", "cat2"]
       → Gets tools from specific categories
    
    4. tools=[...] + auto_tools=...
       → Combine explicit and auto-discovered
    
    5. tool_retry=N
       → Auto-retry with similar tools on failure
    
    Registration (do once at startup):
    
        from agentic_swarm import tool, register_tool
        
        @tool
        def my_tool(x: int) -> int:
            return x * 2
        
        register_tool(my_tool, category="math", keywords=["multiply"])
    """)


if __name__ == "__main__":
    asyncio.run(main())
