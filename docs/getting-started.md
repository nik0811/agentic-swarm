# Getting Started

## Installation

```bash
pip install agentic-swarm
```

### Optional Dependencies

```bash
pip install agentic-swarm[openai]       # OpenAI provider
pip install agentic-swarm[anthropic]    # Anthropic provider
pip install agentic-swarm[bedrock]      # AWS Bedrock provider
pip install agentic-swarm[gemini]       # Google Gemini provider
pip install agentic-swarm[qdrant]       # Qdrant vector DB
pip install agentic-swarm[crypto]       # Encryption support
pip install agentic-swarm[all]          # Everything
```

### Development Install

```bash
git clone https://github.com/nik0811/agentic-swarm.git
cd agentic-swarm
python -m venv env && source env/bin/activate
pip install -e ".[dev,all]"
pytest tests/ -v
```

## Quick Start

### Basic Agent

```python
import asyncio
from agentic_swarm import Agent, Swarm, tool

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

researcher = Agent(
    name="researcher",
    role="Research and gather information",
    tools=[search_web],
)

swarm = Swarm(agents=[researcher])

async def main():
    result = await swarm.run("Find information about AI agents")
    print(result)

asyncio.run(main())
```

### With LLM Provider (Bedrock Example)

```python
import os
from agentic_swarm import Agent, Swarm, tool
from agentic_swarm.llm import LLMRouter, BedrockProvider

# Create provider
provider = BedrockProvider(
    model=os.environ["BEDROCK_MODEL_ID"],
    region=os.environ["AWS_REGION"],
    access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
)

# Create router
router = LLMRouter(strategy="quality_optimized")
router.register_provider("bedrock", provider)

# Create agent with router
agent = Agent(
    name="assistant",
    role="Helpful AI assistant",
    llm_router=router,
    llm=os.environ["BEDROCK_MODEL_ID"],
)

result = await agent.run("Explain quantum computing")
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | For OpenAI | OpenAI API key |
| `ANTHROPIC_API_KEY` | For Anthropic | Anthropic API key |
| `GOOGLE_API_KEY` | For Gemini | Google AI API key |
| `GROQ_API_KEY` | For Groq | Groq API key |
| `AWS_ACCESS_KEY_ID` | For Bedrock | AWS access key ID |
| `AWS_SECRET_ACCESS_KEY` | For Bedrock | AWS secret access key |
| `AWS_REGION` | For Bedrock | AWS region (e.g. `us-east-1`) |
| `BEDROCK_MODEL_ID` | For Bedrock | Model ID |
| `OLLAMA_BASE_URL` | For Ollama | Server URL (default: `http://localhost:11434`) |
| `VLLM_BASE_URL` | For vLLM | Server URL (default: `http://localhost:8000/v1`) |

## Supported LLM Providers

| Provider | Models |
|----------|--------|
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-4-turbo, o1, o1-mini |
| **Anthropic** | claude-sonnet-4-20250514, claude-3-5-sonnet, claude-3-opus, claude-3-haiku |
| **Google Gemini** | gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash |
| **AWS Bedrock** | Claude, Llama, Titan, Mistral models |
| **Groq** | llama-3.3-70b, llama-3.1-8b, mixtral-8x7b |
| **Ollama** | Any locally available model |
| **vLLM** | Any model via OpenAI-compatible API |

## Next Steps

- [Configuration Guide](configuration.md) - Customize SDK behavior
- [API Reference](api-reference.md) - Complete API documentation
- [Examples](examples.md) - More code examples
