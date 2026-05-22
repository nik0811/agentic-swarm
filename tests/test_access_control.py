import pytest

from agentic_swarm.compliance.access import (
    AccessController,
    AccessPolicy,
    Permission,
)


class TestAccessController:
    def setup_method(self):
        self.controller = AccessController()

    def test_set_and_get_policy(self):
        policy = AccessPolicy(
            agent_id="agent-1",
            permissions={Permission.READ, Permission.WRITE},
        )
        self.controller.set_policy("agent-1", policy)
        retrieved = self.controller.get_policy("agent-1")
        assert retrieved is not None
        assert retrieved.agent_id == "agent-1"

    def test_get_policy_nonexistent(self):
        assert self.controller.get_policy("ghost") is None

    def test_check_permission_with_policy(self):
        policy = AccessPolicy(
            agent_id="agent-1",
            permissions={Permission.READ, Permission.EXECUTE},
        )
        self.controller.set_policy("agent-1", policy)

        assert self.controller.check_permission("agent-1", Permission.READ) is True
        assert self.controller.check_permission("agent-1", Permission.EXECUTE) is True
        assert self.controller.check_permission("agent-1", Permission.ADMIN) is False
        assert self.controller.check_permission("agent-1", Permission.SPAWN) is False

    def test_check_permission_default(self):
        assert self.controller.check_permission("unknown", Permission.READ) is True
        assert self.controller.check_permission("unknown", Permission.WRITE) is True
        assert self.controller.check_permission("unknown", Permission.EXECUTE) is True
        assert self.controller.check_permission("unknown", Permission.ADMIN) is False
        assert self.controller.check_permission("unknown", Permission.SPAWN) is False
        assert self.controller.check_permission("unknown", Permission.TERMINATE) is False

    def test_check_tool_access_no_policy(self):
        assert self.controller.check_tool_access("unknown", "any_tool") is True

    def test_check_tool_access_allowed_list(self):
        policy = AccessPolicy(
            agent_id="agent-1",
            permissions={Permission.EXECUTE},
            allowed_tools=["tool_a", "tool_b"],
        )
        self.controller.set_policy("agent-1", policy)

        assert self.controller.check_tool_access("agent-1", "tool_a") is True
        assert self.controller.check_tool_access("agent-1", "tool_b") is True
        assert self.controller.check_tool_access("agent-1", "tool_c") is False

    def test_check_tool_access_denied_list(self):
        policy = AccessPolicy(
            agent_id="agent-1",
            permissions={Permission.EXECUTE},
            denied_tools=["dangerous_tool"],
        )
        self.controller.set_policy("agent-1", policy)

        assert self.controller.check_tool_access("agent-1", "safe_tool") is True
        assert self.controller.check_tool_access("agent-1", "dangerous_tool") is False

    def test_check_tool_access_denied_takes_precedence(self):
        policy = AccessPolicy(
            agent_id="agent-1",
            permissions={Permission.EXECUTE},
            allowed_tools=["tool_a"],
            denied_tools=["tool_a"],
        )
        self.controller.set_policy("agent-1", policy)
        assert self.controller.check_tool_access("agent-1", "tool_a") is False

    def test_check_model_access_no_policy(self):
        assert self.controller.check_model_access("unknown", "gpt-4") is True

    def test_check_model_access_allowed_models(self):
        policy = AccessPolicy(
            agent_id="agent-1",
            permissions={Permission.EXECUTE},
            allowed_models=["gpt-4o-mini", "gpt-4o"],
        )
        self.controller.set_policy("agent-1", policy)

        assert self.controller.check_model_access("agent-1", "gpt-4o-mini") is True
        assert self.controller.check_model_access("agent-1", "gpt-4o") is True
        assert self.controller.check_model_access("agent-1", "claude-3-opus") is False

    def test_check_model_access_empty_allowed_models(self):
        policy = AccessPolicy(
            agent_id="agent-1",
            permissions={Permission.EXECUTE},
            allowed_models=[],
        )
        self.controller.set_policy("agent-1", policy)
        assert self.controller.check_model_access("agent-1", "any-model") is True

    def test_remove_policy(self):
        policy = AccessPolicy(agent_id="agent-1", permissions={Permission.READ})
        self.controller.set_policy("agent-1", policy)
        self.controller.remove_policy("agent-1")
        assert self.controller.get_policy("agent-1") is None
        assert self.controller.check_permission("agent-1", Permission.READ) is True

    def test_clear(self):
        self.controller.set_policy(
            "a1", AccessPolicy(agent_id="a1", permissions={Permission.ADMIN})
        )
        self.controller.set_policy(
            "a2", AccessPolicy(agent_id="a2", permissions={Permission.SPAWN})
        )
        self.controller.clear()
        assert self.controller.get_policy("a1") is None
        assert self.controller.get_policy("a2") is None
