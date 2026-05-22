from agentic_swarm import Agent, Tool, Swarm
from agentic_swarm.core.types import AgentState, MessageType, TaskComplexity, AgentSpec, Message


def test_agent_creation():
    agent = Agent(name="TestAgent")
    assert agent.name == "TestAgent"


def test_agent_default_name():
    swarm = Swarm(agents=[Agent(name="Agent1"), Agent(name="Agent2"), Agent(name="Agent3")])
    assert swarm.agents == [Agent(name="Agent1"), Agent(name="Agent2"), Agent(name="Agent3")]


def test_tool_creation():
    tool = Tool(name="TestTool")
    assert tool.name == "TestTool"


def test_agent_state():
    spec = AgentSpec(name="TestAgent", role="TestRole", tools=["TestTool"])
    assert spec.max_iterations == 10
    assert AgentState.RUNNING.value == "running"

