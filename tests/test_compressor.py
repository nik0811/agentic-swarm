import pytest
from agentic_swarm.llm.context_compressor import ContextCompressor
from agentic_swarm.llm.token_manager import TokenManager


def test_compressor_no_compression_needed():
    compressor = ContextCompressor()
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
    ]
    
    result = compressor.compress(messages, budget=10000)
    assert len(result) == 2


def test_compressor_truncate():
    compressor = ContextCompressor()
    messages = [
        {"role": "user", "content": "Message " * 100},
        {"role": "assistant", "content": "Response " * 100},
        {"role": "user", "content": "Short"},
    ]
    
    result = compressor.compress(messages, budget=100, preserve_recent=1)
    assert len(result) <= 2


def test_compressor_preserve_recent():
    compressor = ContextCompressor()
    messages = [
        {"role": "user", "content": f"Message {i}"} for i in range(10)
    ]
    
    result = compressor.compress(messages, budget=500, preserve_recent=3)
    assert result[-1]["content"] == "Message 9"


def test_compressor_empty_messages():
    compressor = ContextCompressor()
    result = compressor.compress([], budget=1000)
    assert result == []


def test_compressor_extract_key_facts():
    compressor = ContextCompressor()
    messages = [
        {"role": "user", "content": "The capital of France is Paris. Python is a programming language."},
    ]
    
    facts = compressor.extract_key_facts(messages)
    assert len(facts) > 0


def test_compressor_filter_by_relevance():
    compressor = ContextCompressor()
    messages = [
        {"role": "user", "content": "I love Python programming"},
        {"role": "assistant", "content": "Python is great for AI"},
        {"role": "user", "content": "What about JavaScript?"},
    ]
    
    filtered = compressor.filter_by_relevance(messages, "Python programming")
    assert len(filtered) >= 1
