"""Tests for PlanningMemory - Goals, Plans, and Task Management."""

import pytest

from agentic_swarm.memory.planning_memory import (
    Goal,
    GoalStatus,
    Plan,
    PlanningMemory,
    PlanTask,
    Priority,
    TaskStatus,
)


class TestPlanningMemory:
    """Test PlanningMemory functionality."""

    def test_create_planning_memory(self):
        """Test creating a planning memory instance."""
        planning = PlanningMemory(agent_id="test-agent")
        assert planning.agent_id == "test-agent"
        assert len(planning._goals) == 0
        assert len(planning._plans) == 0

    def test_add_goal(self):
        """Test adding a goal."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal(
            description="Build a web scraper",
            priority=Priority.HIGH,
            success_criteria=["Scraper runs", "Data saved"],
        )
        
        assert goal is not None
        assert goal.description == "Build a web scraper"
        assert goal.priority == Priority.HIGH
        assert goal.status == GoalStatus.PENDING
        assert len(goal.success_criteria) == 2
        assert goal.id.startswith("goal_")

    def test_add_goal_with_parent(self):
        """Test adding a sub-goal."""
        planning = PlanningMemory(agent_id="test")
        
        parent = planning.add_goal("Main goal")
        child = planning.add_goal("Sub goal", parent_goal_id=parent.id)
        
        assert child.parent_goal_id == parent.id
        assert child.id in parent.sub_goal_ids

    def test_get_goal(self):
        """Test retrieving a goal."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Test goal")
        retrieved = planning.get_goal(goal.id)
        
        assert retrieved is not None
        assert retrieved.description == "Test goal"
        
        missing = planning.get_goal("nonexistent")
        assert missing is None

    def test_get_active_goals(self):
        """Test getting active goals."""
        planning = PlanningMemory(agent_id="test")
        
        g1 = planning.add_goal("Goal 1")
        g2 = planning.add_goal("Goal 2")
        g3 = planning.add_goal("Goal 3")
        
        planning.update_goal_status(g2.id, GoalStatus.COMPLETED)
        planning.update_goal_status(g3.id, GoalStatus.CANCELLED)
        
        active = planning.get_active_goals()
        
        assert len(active) == 1
        assert active[0].id == g1.id

    def test_get_goals_by_priority(self):
        """Test filtering goals by priority."""
        planning = PlanningMemory(agent_id="test")
        
        planning.add_goal("Low priority", priority=Priority.LOW)
        planning.add_goal("High priority 1", priority=Priority.HIGH)
        planning.add_goal("High priority 2", priority=Priority.HIGH)
        planning.add_goal("Critical", priority=Priority.CRITICAL)
        
        high = planning.get_goals_by_priority(Priority.HIGH)
        assert len(high) == 2

    def test_update_goal_status(self):
        """Test updating goal status."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Test goal")
        assert goal.status == GoalStatus.PENDING
        assert goal.started_at is None
        
        planning.update_goal_status(goal.id, GoalStatus.IN_PROGRESS)
        assert goal.status == GoalStatus.IN_PROGRESS
        assert goal.started_at is not None
        
        planning.update_goal_status(goal.id, GoalStatus.COMPLETED)
        assert goal.status == GoalStatus.COMPLETED
        assert goal.completed_at is not None

    def test_create_plan(self):
        """Test creating a plan."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Build feature")
        plan = planning.create_plan(
            goal_id=goal.id,
            description="Implementation plan",
            tasks=[
                {"description": "Research"},
                {"description": "Design"},
                {"description": "Implement", "dependencies": ["task_1", "task_2"]},
                {"description": "Test", "dependencies": ["task_3"]},
            ],
        )
        
        assert plan is not None
        assert plan.goal_id == goal.id
        assert len(plan.tasks) == 4
        assert plan.status == GoalStatus.PENDING
        assert plan.id in goal.plan_ids

    def test_create_plan_missing_goal(self):
        """Test creating plan for nonexistent goal."""
        planning = PlanningMemory(agent_id="test")
        
        plan = planning.create_plan(
            goal_id="nonexistent",
            description="Plan",
            tasks=[{"description": "Task"}],
        )
        
        assert plan is None

    def test_get_plan(self):
        """Test retrieving a plan."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        plan = planning.create_plan(goal.id, "Plan", [{"description": "Task"}])
        
        retrieved = planning.get_plan(plan.id)
        assert retrieved is not None
        assert retrieved.description == "Plan"

    def test_get_plans_for_goal(self):
        """Test getting all plans for a goal."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        planning.create_plan(goal.id, "Plan 1", [{"description": "Task"}])
        planning.create_plan(goal.id, "Plan 2", [{"description": "Task"}])
        
        plans = planning.get_plans_for_goal(goal.id)
        assert len(plans) == 2

    def test_get_next_task(self):
        """Test getting next task to work on."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        plan = planning.create_plan(
            goal.id,
            "Plan",
            [
                {"description": "Task 1"},
                {"description": "Task 2", "dependencies": ["task_1"]},
            ],
        )
        
        # First task should be available
        task = planning.get_next_task(plan.id)
        assert task is not None
        assert task.description == "Task 1"

    def test_start_task(self):
        """Test starting a task."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        plan = planning.create_plan(goal.id, "Plan", [{"description": "Task"}])
        task = plan.tasks[0]
        
        started = planning.start_task(plan.id, task.id)
        
        assert started is not None
        assert started.status == TaskStatus.IN_PROGRESS
        assert started.started_at is not None
        assert plan.status == GoalStatus.IN_PROGRESS

    def test_complete_task(self):
        """Test completing a task."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        plan = planning.create_plan(goal.id, "Plan", [{"description": "Task"}])
        task = plan.tasks[0]
        
        planning.start_task(plan.id, task.id)
        completed = planning.complete_task(plan.id, task.id, result="Done!")
        
        assert completed is not None
        assert completed.status == TaskStatus.COMPLETED
        assert completed.result == "Done!"
        assert completed.completed_at is not None

    def test_complete_all_tasks_completes_plan(self):
        """Test that completing all tasks completes the plan."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        plan = planning.create_plan(
            goal.id,
            "Plan",
            [{"description": "Task 1"}, {"description": "Task 2"}],
        )
        
        planning.start_task(plan.id, plan.tasks[0].id)
        planning.complete_task(plan.id, plan.tasks[0].id)
        
        assert plan.status == GoalStatus.IN_PROGRESS
        assert plan.progress == 0.5
        
        planning.start_task(plan.id, plan.tasks[1].id)
        planning.complete_task(plan.id, plan.tasks[1].id)
        
        assert plan.status == GoalStatus.COMPLETED
        assert plan.progress == 1.0

    def test_fail_task(self):
        """Test failing a task."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        plan = planning.create_plan(goal.id, "Plan", [{"description": "Task"}])
        task = plan.tasks[0]
        
        planning.start_task(plan.id, task.id)
        failed = planning.fail_task(plan.id, task.id, error="Something went wrong")
        
        assert failed is not None
        assert failed.status == TaskStatus.FAILED
        assert failed.error == "Something went wrong"

    def test_skip_task(self):
        """Test skipping a task."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        plan = planning.create_plan(goal.id, "Plan", [{"description": "Task"}])
        task = plan.tasks[0]
        
        skipped = planning.skip_task(plan.id, task.id, reason="Not needed")
        
        assert skipped is not None
        assert skipped.status == TaskStatus.SKIPPED
        assert skipped.metadata["skip_reason"] == "Not needed"

    def test_add_task_to_plan(self):
        """Test adding a task to existing plan."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        plan = planning.create_plan(
            goal.id,
            "Plan",
            [{"description": "Task 1"}, {"description": "Task 2"}],
        )
        
        new_task = planning.add_task_to_plan(
            plan.id,
            description="Task 1.5",
            after_task_id="task_1",
        )
        
        assert new_task is not None
        assert len(plan.tasks) == 3
        assert plan.tasks[1].description == "Task 1.5"

    def test_get_blocked_tasks(self):
        """Test getting blocked tasks."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        plan = planning.create_plan(
            goal.id,
            "Plan",
            [
                {"description": "Task 1"},
                {"description": "Task 2", "dependencies": ["task_1"]},
                {"description": "Task 3", "dependencies": ["task_2"]},
            ],
        )
        
        blocked = planning.get_blocked_tasks(plan.id)
        
        # Task 2 and 3 are blocked
        assert len(blocked) == 2

    def test_get_completed_plans(self):
        """Test getting completed plans."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        plan1 = planning.create_plan(goal.id, "Plan 1", [{"description": "Task"}])
        plan2 = planning.create_plan(goal.id, "Plan 2", [{"description": "Task"}])
        
        # Complete plan1
        planning.start_task(plan1.id, plan1.tasks[0].id)
        planning.complete_task(plan1.id, plan1.tasks[0].id)
        
        completed = planning.get_completed_plans()
        
        assert len(completed) == 1
        assert completed[0].id == plan1.id

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal", priority=Priority.HIGH)
        plan = planning.create_plan(
            goal.id,
            "Plan",
            [{"description": "Task 1"}, {"description": "Task 2"}],
        )
        planning.start_task(plan.id, plan.tasks[0].id)
        planning.complete_task(plan.id, plan.tasks[0].id, result="Done")
        
        # Serialize
        data = planning.to_dict()
        assert data["agent_id"] == "test"
        assert len(data["goals"]) == 1
        assert len(data["plans"]) == 1
        
        # Deserialize
        restored = PlanningMemory.from_dict(data)
        assert restored.agent_id == "test"
        
        restored_goal = list(restored._goals.values())[0]
        assert restored_goal.priority == Priority.HIGH
        
        restored_plan = list(restored._plans.values())[0]
        assert len(restored_plan.tasks) == 2
        assert restored_plan.tasks[0].status == TaskStatus.COMPLETED

    def test_clear(self):
        """Test clearing planning memory."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        planning.create_plan(goal.id, "Plan", [{"description": "Task"}])
        
        planning.clear()
        
        assert len(planning._goals) == 0
        assert len(planning._plans) == 0

    def test_get_summary(self):
        """Test getting memory summary."""
        planning = PlanningMemory(agent_id="test")
        
        planning.add_goal("Goal 1", priority=Priority.HIGH)
        planning.add_goal("Goal 2", priority=Priority.LOW)
        g3 = planning.add_goal("Goal 3", priority=Priority.HIGH)
        planning.update_goal_status(g3.id, GoalStatus.COMPLETED)
        
        summary = planning.get_summary()
        
        assert summary["agent_id"] == "test"
        assert summary["total_goals"] == 3
        assert summary["active_goals"] == 2
        assert summary["goals_by_priority"]["high"] == 2
        assert summary["goals_by_priority"]["low"] == 1

    def test_plan_progress(self):
        """Test plan progress calculation."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        plan = planning.create_plan(
            goal.id,
            "Plan",
            [
                {"description": "Task 1"},
                {"description": "Task 2"},
                {"description": "Task 3"},
                {"description": "Task 4"},
            ],
        )
        
        assert plan.progress == 0.0
        
        planning.start_task(plan.id, plan.tasks[0].id)
        planning.complete_task(plan.id, plan.tasks[0].id)
        assert plan.progress == 0.25
        
        planning.skip_task(plan.id, plan.tasks[1].id)
        assert plan.progress == 0.5

    def test_task_dependencies(self):
        """Test task dependency handling."""
        planning = PlanningMemory(agent_id="test")
        
        goal = planning.add_goal("Goal")
        plan = planning.create_plan(
            goal.id,
            "Plan",
            [
                {"description": "Setup"},
                {"description": "Build", "dependencies": ["task_1"]},
                {"description": "Test", "dependencies": ["task_2"]},
                {"description": "Deploy", "dependencies": ["task_2", "task_3"]},
            ],
        )
        
        # Only task_1 should be available initially
        next_task = planning.get_next_task(plan.id)
        assert next_task.description == "Setup"
        
        # Complete task_1
        planning.start_task(plan.id, "task_1")
        planning.complete_task(plan.id, "task_1")
        
        # Now task_2 should be available
        next_task = planning.get_next_task(plan.id)
        assert next_task.description == "Build"
