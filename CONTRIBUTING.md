# Contributing to Agentic Swarm

Thank you for your interest in contributing to Agentic Swarm! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Issues

Before creating an issue, please:

1. **Search existing issues** to avoid duplicates
2. **Use the issue template** and include:
   - Python version (`python --version`)
   - SDK version (`pip show agentic-swarm`)
   - Full error traceback
   - Minimal reproducible example
   - Expected vs actual behavior

### Submitting Pull Requests

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Write tests** for your changes
4. **Ensure all tests pass**: `pytest tests/ -v`
5. **Lint your code**: `ruff check agentic_swarm/`
6. **Format your code**: `ruff format agentic_swarm/`
7. **Commit** with clear messages
8. **Push** and open a PR against `main`

### Development Setup

```bash
# Clone the repository
git clone https://github.com/nik0811/agentic-swarm.git
cd agentic-swarm

# Create virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev,all]"

# Run tests
pytest tests/ -v

# Run linter
ruff check agentic_swarm/

# Run formatter
ruff format agentic_swarm/
```

## Code Style

### General Guidelines

- **Line length**: 100 characters max
- **Type hints**: Required for all public APIs
- **Docstrings**: Google style for public methods
- **Tests**: pytest + pytest-asyncio for async tests

### Commit Message Format

Use clear, descriptive commit messages:

| Prefix | Meaning |
|--------|---------|
| `Add:` | New feature |
| `Fix:` | Bug fix |
| `Update:` | Enhancement to existing feature |
| `Refactor:` | Code restructuring (no behavior change) |
| `Docs:` | Documentation only |
| `Test:` | Test additions/modifications |
| `Chore:` | Build, CI, or tooling changes |

Examples:
```
Add: Support for Groq LLM provider
Fix: Memory leak in agent spawning
Update: Improve RAG retrieval accuracy
Docs: Add configuration guide
```

### Code Review Process

1. All PRs require at least one approval
2. CI must pass (tests, lint, type check)
3. No decrease in test coverage
4. Documentation updated if needed

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_agent.py -v

# Run with coverage
pytest tests/ --cov=agentic_swarm --cov-report=html

# Run only fast tests (skip slow integration tests)
pytest tests/ -v -m "not slow"
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use `pytest.mark.asyncio` for async tests
- Mock external services (LLM APIs, databases)

Example:
```python
import pytest
from agentic_swarm import Agent

@pytest.mark.asyncio
async def test_agent_creation():
    agent = Agent(name="test", role="tester")
    assert agent.name == "test"
    assert agent.role == "tester"
```

## Documentation

- Update docstrings for any API changes
- Update `docs/` for new features
- Include code examples where helpful
- Keep README.md concise; detailed docs go in `docs/`

## Security

- **Never commit credentials** or API keys
- Use environment variables for secrets
- Report security vulnerabilities privately to maintainers
- Follow secure coding practices

## Questions?

- Open a [Discussion](https://github.com/nik0811/agentic-swarm/discussions) for questions
- Check existing issues and discussions first
- Be respectful and constructive

Thank you for contributing! 🎉
