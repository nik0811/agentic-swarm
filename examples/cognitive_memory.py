"""
Cognitive Memory Example - Full Memory Architecture Demo

Demonstrates all memory types working together:
- Vector DB: Semantic search over documents
- Graph Memory: Entity-relationship knowledge graph
- Session Memory (Recall): Working context window
- Tool Memory: Learn from tool usage patterns
- Planning Memory: Goals, plans, and task tracking

This simulates long-term cognition where an agent:
1. Builds knowledge graphs from conversations
2. Tracks tool effectiveness
3. Plans and executes multi-step tasks
4. Remembers everything across sessions
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentic_swarm.memory import (
    MemoryController,
    Priority,
    GoalStatus,
)
from agentic_swarm.vectordb import InMemoryVectorDB
from agentic_swarm.rag.embedder import MockEmbedder


async def main():
    print("=" * 60)
    print("COGNITIVE MEMORY ARCHITECTURE DEMO")
    print("=" * 60)

    # Initialize memory controller with all cognitive features
    vectordb = InMemoryVectorDB()
    embedder = MockEmbedder(dimensions=384)  # Use mock embedder for demo
    
    memory = MemoryController(
        agent_id="cognitive-agent-001",
        name="CognitiveAgent",
        persona="An AI assistant with full cognitive memory capabilities",
        capabilities=["reasoning", "planning", "learning", "knowledge-graph"],
        vectordb=vectordb,
        embedder=embedder,
        recall_max_size=50,
        auto_archive=True,
        auto_extract_facts=True,
        # Enable cognitive memory features
        enable_graph_memory=True,
        enable_tool_memory=True,
        enable_planning_memory=True,
    )

    print("\n[1] GRAPH MEMORY - Building Knowledge Graph")
    print("-" * 40)
    
    # Add entities (people, projects, technologies)
    memory.add_entity("user_john", "person", "John Smith", {
        "role": "developer",
        "experience_years": 5,
        "department": "engineering"
    })
    memory.add_entity("user_sarah", "person", "Sarah Johnson", {
        "role": "product_manager",
        "experience_years": 8,
        "department": "product"
    })
    memory.add_entity("proj_alpha", "project", "Project Alpha", {
        "status": "active",
        "priority": "high"
    })
    memory.add_entity("tech_python", "technology", "Python", {
        "type": "language",
        "version": "3.11"
    })
    memory.add_entity("tech_fastapi", "technology", "FastAPI", {
        "type": "framework",
        "language": "python"
    })
    
    # Add relationships
    memory.add_relationship("user_john", "proj_alpha", "works_on", {"role": "lead"})
    memory.add_relationship("user_sarah", "proj_alpha", "manages")
    memory.add_relationship("proj_alpha", "tech_python", "uses")
    memory.add_relationship("proj_alpha", "tech_fastapi", "uses")
    memory.add_relationship("user_john", "tech_python", "expert_in", {"years": 5})
    memory.add_relationship("tech_fastapi", "tech_python", "built_with")
    
    # Query the graph
    print("Entities in graph:")
    for entity_type in ["person", "project", "technology"]:
        entities = memory.graph.get_entities_by_type(entity_type)
        print(f"  {entity_type}: {[e.name for e in entities]}")
    
    print("\nRelationships from John:")
    related = memory.get_related_entities("user_john", direction="outgoing")
    for rel_id in related:
        entity = memory.graph.get_entity(rel_id)
        if entity:
            print(f"  -> {entity.name} ({entity.type})")
    
    print("\nPath from John to FastAPI:")
    path = memory.find_entity_path("user_john", "tech_fastapi")
    if path:
        path_names = [memory.graph.get_entity(p).name for p in path]
        print(f"  {' -> '.join(path_names)}")

    print("\n[2] TOOL MEMORY - Learning from Tool Usage")
    print("-" * 40)
    
    # Simulate tool usage history
    tool_usages = [
        ("web_search", "search for Python best practices", True, 150),
        ("web_search", "find FastAPI documentation", True, 120),
        ("web_search", "search API endpoints", True, 180),
        ("code_analyzer", "analyze Python code quality", True, 500),
        ("code_analyzer", "check code complexity", True, 450),
        ("code_analyzer", "analyze JavaScript code", False, 100),  # Failed
        ("database_query", "fetch user data", True, 50),
        ("database_query", "complex join query", False, 200),  # Failed
        ("file_reader", "read configuration file", True, 30),
        ("file_reader", "read large log file", True, 80),
    ]
    
    for tool, task, success, duration in tool_usages:
        memory.record_tool_usage(
            tool_name=tool,
            task_description=task,
            success=success,
            duration_ms=duration,
            error_message=None if success else "Operation failed"
        )
    
    print("Tool Statistics:")
    for tool_name in ["web_search", "code_analyzer", "database_query", "file_reader"]:
        stats = memory.get_tool_stats(tool_name)
        if stats:
            print(f"  {tool_name}:")
            print(f"    Success rate: {stats.success_rate:.1%}")
            print(f"    Avg duration: {stats.avg_duration_ms:.0f}ms")
            print(f"    Total uses: {stats.total_uses}")
    
    print("\nBest tool recommendations:")
    tasks = [
        "search for documentation",
        "analyze code quality",
        "read a file",
    ]
    for task in tasks:
        best = memory.get_best_tool(task)
        print(f"  '{task}' -> {best}")

    print("\n[3] PLANNING MEMORY - Goals and Task Management")
    print("-" * 40)
    
    # Create a high-level goal
    goal = memory.add_goal(
        description="Build and deploy Project Alpha API",
        priority=Priority.HIGH,
        success_criteria=[
            "All endpoints implemented",
            "Tests passing with >90% coverage",
            "Deployed to production",
            "Documentation complete"
        ]
    )
    print(f"Created goal: {goal.description}")
    print(f"  Priority: {goal.priority.value}")
    print(f"  Criteria: {len(goal.success_criteria)} items")
    
    # Create a plan with tasks
    plan = memory.create_plan(
        goal_id=goal.id,
        description="API Development Plan",
        tasks=[
            {"description": "Set up project structure", "priority": "high"},
            {"description": "Implement user endpoints", "dependencies": ["task_1"]},
            {"description": "Implement data endpoints", "dependencies": ["task_1"]},
            {"description": "Write unit tests", "dependencies": ["task_2", "task_3"]},
            {"description": "Write integration tests", "dependencies": ["task_4"]},
            {"description": "Deploy to staging", "dependencies": ["task_5"]},
            {"description": "Deploy to production", "dependencies": ["task_6"]},
        ]
    )
    print(f"\nCreated plan: {plan.description}")
    print(f"  Tasks: {len(plan.tasks)}")
    
    # Simulate working through tasks
    print("\nExecuting plan:")
    for i in range(3):  # Complete first 3 tasks
        task = memory.get_next_task(plan.id)
        if task:
            print(f"  Starting: {task.description}")
            memory.planning.start_task(plan.id, task.id)
            memory.planning.complete_task(plan.id, task.id, result="Completed successfully")
            print(f"    ✓ Completed")
    
    print(f"\nPlan progress: {plan.progress:.0%}")
    print(f"Plan status: {plan.status.value}")
    
    # Show blocked tasks
    blocked = memory.planning.get_blocked_tasks(plan.id)
    if blocked:
        print(f"Blocked tasks: {[t.description for t in blocked]}")

    print("\n[4] SESSION MEMORY (RECALL) - Working Context")
    print("-" * 40)
    
    # Simulate a conversation
    messages = [
        ("user", "I need help with Project Alpha"),
        ("assistant", "I can help with Project Alpha. John is the lead developer and Sarah manages it."),
        ("user", "What technologies does it use?"),
        ("assistant", "Project Alpha uses Python 3.11 with FastAPI framework."),
        ("user", "Remember that we need to add Redis for caching"),
        ("assistant", "Noted! I'll remember that Project Alpha needs Redis for caching."),
    ]
    
    for role, content in messages:
        memory.push_recall(content, role=role)
    
    print("Recent conversation:")
    for msg in memory.get_recall_messages()[-4:]:
        print(f"  [{msg['role']}]: {msg['content'][:60]}...")
    
    # Search recall
    print("\nSearching recall for 'Redis':")
    results = memory.search_recall("Redis", limit=2)
    for r in results:
        print(f"  Found: {str(r.content)[:50]}...")

    print("\n[5] ARCHIVAL MEMORY - Long-term Storage")
    print("-" * 40)
    
    # Store important facts
    facts = [
        "Project Alpha deadline is Q4 2026",
        "John prefers async/await patterns",
        "Sarah requires weekly status updates",
        "Redis caching is required for performance",
    ]
    
    for fact in facts:
        await memory.store_archival(fact)
    
    # Flush auto-extracted facts
    flushed = await memory.flush_to_archival()
    print(f"Auto-archived {flushed} facts from conversation")
    
    # Search archival
    print("\nSearching archival for 'deadline':")
    results = await memory.search_archival("deadline", limit=2)
    for r in results:
        print(f"  Found: {r.content}")

    print("\n[6] UNIFIED MEMORY STATS")
    print("-" * 40)
    
    stats = memory.get_stats()
    print(f"Core Memory:")
    print(f"  Agent: {stats['core']['name']}")
    print(f"  Capabilities: {stats['core']['capabilities']}")
    
    print(f"\nRecall Memory:")
    print(f"  Size: {stats['recall']['size']} entries")
    print(f"  Tokens: {stats['recall']['token_count']}")
    
    print(f"\nArchival Memory:")
    print(f"  Enabled: {stats['archival']['enabled']}")
    print(f"  Pending: {stats['archival']['pending_archives']}")
    
    print(f"\nGraph Memory:")
    print(f"  Enabled: {stats['graph']['enabled']}")
    print(f"  Entities: {stats['graph']['entities']}")
    print(f"  Relationships: {stats['graph']['relationships']}")
    
    print(f"\nTool Memory:")
    print(f"  Enabled: {stats['tool_memory']['enabled']}")
    print(f"  Tools tracked: {stats['tool_memory']['tools_tracked']}")
    print(f"  History size: {stats['tool_memory']['history_size']}")
    
    print(f"\nPlanning Memory:")
    print(f"  Enabled: {stats['planning']['enabled']}")
    print(f"  Goals: {stats['planning']['goals']}")
    print(f"  Plans: {stats['planning']['plans']}")

    print("\n[7] CROSS-SESSION PERSISTENCE")
    print("-" * 40)
    
    # Export all memory state
    print("Exporting memory state for persistence...")
    
    graph_data = memory.graph.to_dict()
    tool_data = memory.tool_memory.to_dict()
    planning_data = memory.planning.to_dict()
    
    print(f"  Graph: {len(graph_data['entities'])} entities, {len(graph_data['relationships'])} relationships")
    print(f"  Tools: {len(tool_data['history'])} usage records")
    print(f"  Planning: {len(planning_data['goals'])} goals, {len(planning_data['plans'])} plans")
    
    # Simulate loading in a new session
    print("\nSimulating new session with restored memory...")
    
    from agentic_swarm.memory.graph_memory import GraphMemory
    from agentic_swarm.memory.tool_memory import ToolMemory
    from agentic_swarm.memory.planning_memory import PlanningMemory
    
    restored_graph = GraphMemory.from_dict(graph_data)
    restored_tools = ToolMemory.from_dict(tool_data)
    restored_planning = PlanningMemory.from_dict(planning_data)
    
    print(f"  Restored graph: {restored_graph.entity_count} entities")
    print(f"  Restored tools: {len(restored_tools._stats)} tools tracked")
    print(f"  Restored planning: {len(restored_planning._goals)} goals")
    
    # Verify restored data
    john = restored_graph.get_entity("user_john")
    print(f"\n  Verified: John's role is '{john.properties['role']}'")
    
    search_stats = restored_tools.get_tool_stats("web_search")
    print(f"  Verified: web_search success rate is {search_stats.success_rate:.1%}")
    
    active_goals = restored_planning.get_active_goals()
    print(f"  Verified: {len(active_goals)} active goals")

    print("\n" + "=" * 60)
    print("COGNITIVE MEMORY DEMO COMPLETE")
    print("=" * 60)
    print("""
Summary of capabilities demonstrated:
1. Graph Memory - Entity relationships and knowledge graph queries
2. Tool Memory - Learning from tool usage patterns
3. Planning Memory - Goal setting and task management
4. Session Memory - Working context with auto-archiving
5. Archival Memory - Long-term vector-indexed storage
6. Cross-session persistence - Export/import for continuity

This architecture enables agents to:
- Build and query knowledge graphs
- Learn which tools work best for which tasks
- Plan and track multi-step objectives
- Remember everything across sessions
- Compress and retrieve relevant memories
""")


if __name__ == "__main__":
    asyncio.run(main())
