import pytest
from agentic_swarm.llm.token_manager import TokenManager


def test_token_manager_count():
    manager = TokenManager()
    count = manager.count_tokens("Hello world")
    assert count > 0
    assert count < 10


def test_token_manager_count_messages():
    manager = TokenManager()
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    count = manager.count_messages_tokens(messages)
    assert count > 0


def test_token_manager_calculate_budget():
    manager = TokenManager()
    budget = manager.calculate_budget(
        model_context_limit=128000,
        reserved_output=4000,
        system_prompt_tokens=500,
    )
    assert budget == 123500


def test_token_manager_allocate_budget():
    manager = TokenManager()
    allocation = manager.allocate_budget(
        total_budget=10000,
        core_memory="You are a helpful assistant.",
        task="What is the weather?",
        tools=None,
        recall_messages=[{"role": "user", "content": "Hello"}],
    )
    
    assert "core_memory" in allocation
    assert "task" in allocation
    assert "remaining" in allocation
    assert allocation["remaining"] >= 0


def test_token_manager_track_usage():
    manager = TokenManager()
    usage = manager.track_usage(
        prompt_tokens=100,
        completion_tokens=50,
        model="gpt-4o-mini",
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
    )
    
    assert usage["prompt_tokens"] == 100
    assert usage["completion_tokens"] == 50
    assert usage["total_tokens"] == 150
    assert usage["cost"] > 0


def test_token_manager_get_total_usage():
    manager = TokenManager()
    manager.track_usage(100, 50, "gpt-4o-mini")
    manager.track_usage(200, 100, "gpt-4o-mini")
    
    total = manager.get_total_usage()
    assert total["prompt_tokens"] == 300
    assert total["completion_tokens"] == 150
    assert total["num_calls"] == 2


def test_token_manager_clear_history():
    manager = TokenManager()
    manager.track_usage(100, 50, "gpt-4o-mini")
    manager.clear_history()
    
    total = manager.get_total_usage()
    assert total["num_calls"] == 0
