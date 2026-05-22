import pytest
from agentic_swarm.llm.classifier import TaskClassifier
from agentic_swarm.core.types import TaskComplexity


def test_classifier_trivial():
    classifier = TaskClassifier()
    assert classifier.classify("What is 2+2?") == TaskComplexity.TRIVIAL
    assert classifier.classify("Yes or no?") == TaskComplexity.TRIVIAL


def test_classifier_moderate():
    classifier = TaskClassifier()
    assert classifier.classify("Summarize this article about AI") == TaskComplexity.MODERATE
    assert classifier.classify("Explain how photosynthesis works") == TaskComplexity.MODERATE


def test_classifier_complex():
    classifier = TaskClassifier()
    assert classifier.classify("Analyze the market trends and compare competitors") == TaskComplexity.COMPLEX
    assert classifier.classify("Design a system for user authentication") == TaskComplexity.COMPLEX


def test_classifier_expert():
    classifier = TaskClassifier()
    assert classifier.classify("Research novel approaches to quantum computing architecture") == TaskComplexity.EXPERT


def test_classifier_cache():
    classifier = TaskClassifier()
    task = "What is the capital of France?"
    
    result1 = classifier.classify(task)
    result2 = classifier.classify(task)
    
    assert result1 == result2
    assert task in classifier._cache


def test_classifier_clear_cache():
    classifier = TaskClassifier()
    classifier.classify("Test task")
    assert len(classifier._cache) > 0
    
    classifier.clear_cache()
    assert len(classifier._cache) == 0
