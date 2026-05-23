"""
Planning Memory - Goals, Plans, and Task Management

Stores goals, plans, task decomposition, and tracks progress.
Enables agents to maintain long-term objectives and multi-step planning.

Features:
- Define goals with priorities and deadlines
- Create plans with ordered steps
- Decompose tasks into subtasks
- Track progress and completion status
- Resume interrupted plans
- Learn from completed plans
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel


class GoalStatus(str, Enum):
    """Status of a goal."""

    PENDING = "pending"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Status of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class Priority(str, Enum):
    """Priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PlanTask(BaseModel):
    """A single task within a plan."""

    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    dependencies: list[str] = []
    assigned_tool: str | None = None
    result: Any = None
    error: str | None = None
    started_at: float | None = None
    completed_at: float | None = None
    metadata: dict[str, Any] = {}

    def __init__(self, **data):
        if "id" not in data:
            data["id"] = f"task_{uuid.uuid4().hex[:8]}"
        super().__init__(**data)


class Plan(BaseModel):
    """A plan consisting of ordered tasks to achieve a goal."""

    id: str
    goal_id: str
    description: str
    tasks: list[PlanTask] = []
    status: GoalStatus = GoalStatus.PENDING
    created_at: float = 0.0
    started_at: float | None = None
    completed_at: float | None = None
    metadata: dict[str, Any] = {}

    def __init__(self, **data):
        if "id" not in data:
            data["id"] = f"plan_{uuid.uuid4().hex[:8]}"
        if "created_at" not in data or data["created_at"] == 0.0:
            data["created_at"] = time.time()
        super().__init__(**data)

    @property
    def progress(self) -> float:
        """Calculate plan progress (0.0 to 1.0)."""
        if not self.tasks:
            return 0.0
        completed = sum(
            1 for t in self.tasks if t.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED)
        )
        return completed / len(self.tasks)

    @property
    def current_task(self) -> PlanTask | None:
        """Get the current task to work on."""
        for task in self.tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                return task
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                deps_met = all(
                    self._get_task(dep_id).status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                    if self._get_task(dep_id)
                )
                if deps_met:
                    return task
        return None

    def _get_task(self, task_id: str) -> PlanTask | None:
        """Get task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None


class Goal(BaseModel):
    """A high-level goal the agent is working towards."""

    id: str
    description: str
    status: GoalStatus = GoalStatus.PENDING
    priority: Priority = Priority.MEDIUM
    deadline: float | None = None
    parent_goal_id: str | None = None
    sub_goal_ids: list[str] = []
    plan_ids: list[str] = []
    success_criteria: list[str] = []
    created_at: float = 0.0
    started_at: float | None = None
    completed_at: float | None = None
    metadata: dict[str, Any] = {}

    def __init__(self, **data):
        if "id" not in data:
            data["id"] = f"goal_{uuid.uuid4().hex[:8]}"
        if "created_at" not in data or data["created_at"] == 0.0:
            data["created_at"] = time.time()
        super().__init__(**data)


class PlanningMemory:
    """
    Memory for goals, plans, and task management.

    Enables agents to:
    - Set and track long-term goals
    - Create multi-step plans
    - Decompose complex tasks
    - Track progress across sessions
    - Resume interrupted work
    - Learn from completed plans

    Usage:
        planning = PlanningMemory(agent_id="agent-123")

        # Create a goal
        goal = planning.add_goal(
            description="Build a web scraper",
            priority=Priority.HIGH,
            success_criteria=["Scraper runs without errors", "Data is saved"]
        )

        # Create a plan for the goal
        plan = planning.create_plan(
            goal_id=goal.id,
            description="Web scraper implementation plan",
            tasks=[
                {"description": "Research target website structure"},
                {"description": "Implement HTTP client", "dependencies": ["task_1"]},
                {"description": "Parse HTML content", "dependencies": ["task_2"]},
                {"description": "Save data to file", "dependencies": ["task_3"]},
            ]
        )

        # Work through tasks
        task = planning.get_next_task(plan.id)
        planning.start_task(plan.id, task.id)
        planning.complete_task(plan.id, task.id, result="Done")
    """

    def __init__(self, agent_id: str):
        """
        Initialize planning memory.

        Args:
            agent_id: Owner agent ID for isolation
        """
        self.agent_id = agent_id
        self._goals: dict[str, Goal] = {}
        self._plans: dict[str, Plan] = {}

    def add_goal(
        self,
        description: str,
        priority: Priority = Priority.MEDIUM,
        deadline: float = None,
        parent_goal_id: str = None,
        success_criteria: list[str] = None,
        metadata: dict[str, Any] = None,
    ) -> Goal:
        """
        Add a new goal.

        Args:
            description: What the goal aims to achieve
            priority: Goal priority level
            deadline: Unix timestamp deadline (optional)
            parent_goal_id: Parent goal if this is a sub-goal
            success_criteria: List of criteria for goal completion
            metadata: Additional metadata

        Returns:
            The created Goal
        """
        goal = Goal(
            description=description,
            priority=priority,
            deadline=deadline,
            parent_goal_id=parent_goal_id,
            success_criteria=success_criteria or [],
            metadata=metadata or {},
        )

        self._goals[goal.id] = goal

        if parent_goal_id and parent_goal_id in self._goals:
            self._goals[parent_goal_id].sub_goal_ids.append(goal.id)

        return goal

    def get_goal(self, goal_id: str) -> Goal | None:
        """Get a goal by ID."""
        return self._goals.get(goal_id)

    def get_active_goals(self) -> list[Goal]:
        """Get all active (non-completed, non-cancelled) goals."""
        return [
            g
            for g in self._goals.values()
            if g.status not in (GoalStatus.COMPLETED, GoalStatus.CANCELLED, GoalStatus.FAILED)
        ]

    def get_goals_by_priority(self, priority: Priority) -> list[Goal]:
        """Get goals with a specific priority."""
        return [g for g in self._goals.values() if g.priority == priority]

    def update_goal_status(self, goal_id: str, status: GoalStatus) -> Goal | None:
        """Update a goal's status."""
        goal = self._goals.get(goal_id)
        if not goal:
            return None

        goal.status = status

        if status == GoalStatus.IN_PROGRESS and goal.started_at is None:
            goal.started_at = time.time()
        elif status in (GoalStatus.COMPLETED, GoalStatus.FAILED, GoalStatus.CANCELLED):
            goal.completed_at = time.time()

        return goal

    def create_plan(
        self,
        goal_id: str,
        description: str,
        tasks: list[dict[str, Any]],
        metadata: dict[str, Any] = None,
    ) -> Plan | None:
        """
        Create a plan for a goal.

        Args:
            goal_id: ID of the goal this plan is for
            description: Plan description
            tasks: List of task definitions (dicts with 'description', optional 'dependencies', etc.)
            metadata: Additional metadata

        Returns:
            The created Plan, or None if goal not found
        """
        if goal_id not in self._goals:
            return None

        plan_tasks = []
        for i, task_def in enumerate(tasks):
            task = PlanTask(
                id=task_def.get("id", f"task_{i + 1}"),
                description=task_def["description"],
                priority=Priority(task_def.get("priority", "medium")),
                dependencies=task_def.get("dependencies", []),
                assigned_tool=task_def.get("assigned_tool"),
                metadata=task_def.get("metadata", {}),
            )
            plan_tasks.append(task)

        plan = Plan(
            goal_id=goal_id,
            description=description,
            tasks=plan_tasks,
            metadata=metadata or {},
        )

        self._plans[plan.id] = plan
        self._goals[goal_id].plan_ids.append(plan.id)

        return plan

    def get_plan(self, plan_id: str) -> Plan | None:
        """Get a plan by ID."""
        return self._plans.get(plan_id)

    def get_plans_for_goal(self, goal_id: str) -> list[Plan]:
        """Get all plans for a goal."""
        return [p for p in self._plans.values() if p.goal_id == goal_id]

    def get_next_task(self, plan_id: str) -> PlanTask | None:
        """Get the next task to work on in a plan."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        return plan.current_task

    def start_task(self, plan_id: str, task_id: str) -> PlanTask | None:
        """Mark a task as started."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        for task in plan.tasks:
            if task.id == task_id:
                task.status = TaskStatus.IN_PROGRESS
                task.started_at = time.time()

                if plan.status == GoalStatus.PENDING:
                    plan.status = GoalStatus.IN_PROGRESS
                    plan.started_at = time.time()

                return task

        return None

    def complete_task(
        self,
        plan_id: str,
        task_id: str,
        result: Any = None,
        metadata: dict[str, Any] = None,
    ) -> PlanTask | None:
        """Mark a task as completed."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        for task in plan.tasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
                task.result = result
                if metadata:
                    task.metadata.update(metadata)

                if plan.progress >= 1.0:
                    plan.status = GoalStatus.COMPLETED
                    plan.completed_at = time.time()

                return task

        return None

    def fail_task(
        self,
        plan_id: str,
        task_id: str,
        error: str,
        metadata: dict[str, Any] = None,
    ) -> PlanTask | None:
        """Mark a task as failed."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        for task in plan.tasks:
            if task.id == task_id:
                task.status = TaskStatus.FAILED
                task.completed_at = time.time()
                task.error = error
                if metadata:
                    task.metadata.update(metadata)
                return task

        return None

    def skip_task(self, plan_id: str, task_id: str, reason: str = None) -> PlanTask | None:
        """Skip a task."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        for task in plan.tasks:
            if task.id == task_id:
                task.status = TaskStatus.SKIPPED
                task.completed_at = time.time()
                if reason:
                    task.metadata["skip_reason"] = reason
                return task

        return None

    def add_task_to_plan(
        self,
        plan_id: str,
        description: str,
        after_task_id: str = None,
        dependencies: list[str] = None,
        **kwargs,
    ) -> PlanTask | None:
        """Add a new task to an existing plan."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        task = PlanTask(
            description=description,
            dependencies=dependencies or [],
            **kwargs,
        )

        if after_task_id:
            for i, t in enumerate(plan.tasks):
                if t.id == after_task_id:
                    plan.tasks.insert(i + 1, task)
                    return task
            plan.tasks.append(task)
        else:
            plan.tasks.append(task)

        return task

    def get_blocked_tasks(self, plan_id: str) -> list[PlanTask]:
        """Get tasks that are blocked by dependencies."""
        plan = self._plans.get(plan_id)
        if not plan:
            return []

        blocked = []
        for task in plan.tasks:
            if task.status == TaskStatus.PENDING and task.dependencies:
                for dep_id in task.dependencies:
                    dep_task = plan._get_task(dep_id)
                    if dep_task and dep_task.status not in (
                        TaskStatus.COMPLETED,
                        TaskStatus.SKIPPED,
                    ):
                        blocked.append(task)
                        break

        return blocked

    def get_completed_plans(self) -> list[Plan]:
        """Get all completed plans (for learning)."""
        return [p for p in self._plans.values() if p.status == GoalStatus.COMPLETED]

    def to_dict(self) -> dict:
        """Export planning memory to dictionary."""
        return {
            "agent_id": self.agent_id,
            "goals": {gid: g.model_dump() for gid, g in self._goals.items()},
            "plans": {pid: p.model_dump() for pid, p in self._plans.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> PlanningMemory:
        """Load planning memory from dictionary."""
        mem = cls(agent_id=data.get("agent_id", "unknown"))

        for goal_data in data.get("goals", {}).values():
            goal = Goal(**goal_data)
            mem._goals[goal.id] = goal

        for plan_data in data.get("plans", {}).values():
            tasks = [PlanTask(**t) for t in plan_data.pop("tasks", [])]
            plan = Plan(**plan_data, tasks=tasks)
            mem._plans[plan.id] = plan

        return mem

    def clear(self) -> None:
        """Clear all goals and plans."""
        self._goals.clear()
        self._plans.clear()

    def get_summary(self) -> dict:
        """Get summary of planning memory state."""
        active_goals = self.get_active_goals()
        completed_plans = self.get_completed_plans()

        return {
            "agent_id": self.agent_id,
            "total_goals": len(self._goals),
            "active_goals": len(active_goals),
            "total_plans": len(self._plans),
            "completed_plans": len(completed_plans),
            "goals_by_priority": {p.value: len(self.get_goals_by_priority(p)) for p in Priority},
        }
