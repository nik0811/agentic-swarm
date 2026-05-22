import pytest
from agentic_swarm.memory.core_memory import CoreMemory
from agentic_swarm.memory.recall_memory import RecallMemory


def test_core_memory_creation():
    core = CoreMemory(
        agent_id="123",
        name="test",
        persona="Test persona",
        capabilities=["search"]
    )
    assert core.agent_id == "123"
    assert core.name == "test"
    assert "search" in core.capabilities


def test_core_memory_immutable():
    core = CoreMemory(agent_id="1", name="test", persona="Test")
    with pytest.raises(Exception):
        core._data.name = "changed"


def test_core_memory_to_prompt():
    core = CoreMemory(agent_id="1", name="helper", persona="You help users")
    prompt = core.to_prompt()
    assert "helper" in prompt
    assert "You help users" in prompt


def test_core_memory_to_dict():
    core = CoreMemory(agent_id="1", name="test", persona="Test", capabilities=["a", "b"])
    data = core.to_dict()
    assert data["agent_id"] == "1"
    assert data["name"] == "test"
    assert data["capabilities"] == ["a", "b"]


def test_recall_memory_push():
    recall = RecallMemory(max_size=5)
    recall.push("Hello", role="user")
    recall.push("Hi there", role="assistant")
    assert recall.size == 2


def test_recall_memory_eviction():
    recall = RecallMemory(max_size=2)
    recall.push("msg1", role="user")
    recall.push("msg2", role="assistant")
    recall.push("msg3", role="user")
    
    assert recall.size == 2
    entries = recall.get_all()
    assert entries[0].content == "msg2"


def test_recall_memory_search():
    recall = RecallMemory()
    recall.push("I like Python", role="user")
    recall.push("Python is great", role="assistant")
    recall.push("JavaScript too", role="user")
    
    results = recall.search("Python")
    assert len(results) == 2


def test_recall_memory_to_messages():
    recall = RecallMemory()
    recall.push("Hello", role="user")
    recall.push("Hi", role="assistant")
    
    messages = recall.to_messages()
    assert messages[0] == {"role": "user", "content": "Hello"}
    assert messages[1] == {"role": "assistant", "content": "Hi"}


def test_recall_memory_get_recent():
    recall = RecallMemory()
    for i in range(10):
        recall.push(f"msg{i}", role="user")
    
    recent = recall.get_recent(3)
    assert len(recent) == 3
    assert recent[0].content == "msg7"
    assert recent[2].content == "msg9"


def test_recall_memory_clear():
    recall = RecallMemory()
    recall.push("test", role="user")
    assert recall.size == 1
    
    recall.clear()
    assert recall.size == 0


def test_recall_memory_token_eviction():
    recall = RecallMemory(max_size=100, max_tokens=50)
    recall.push("msg1", role="user", token_count=20)
    recall.push("msg2", role="user", token_count=20)
    recall.push("msg3", role="user", token_count=20)
    
    assert recall.size == 2
    assert recall.token_count == 40
