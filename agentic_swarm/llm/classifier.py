from ..core.config import get_config
from ..core.types import TaskComplexity


class TaskClassifier:
    """Classify tasks into complexity levels."""

    def __init__(
        self,
        use_llm: bool = False,
        llm_provider=None,
        keywords: dict = None,
        trivial_word_threshold: int = None,
        moderate_word_threshold: int = None,
    ):
        self.use_llm = use_llm
        self.llm_provider = llm_provider
        self._cache: dict[str, TaskComplexity] = {}

        cfg = get_config().classifier
        self.trivial_word_threshold = (
            trivial_word_threshold
            if trivial_word_threshold is not None
            else cfg.trivial_word_threshold
        )
        self.moderate_word_threshold = (
            moderate_word_threshold
            if moderate_word_threshold is not None
            else cfg.moderate_word_threshold
        )

        if keywords:
            self._keywords = keywords
        else:
            self._keywords = {
                TaskComplexity.TRIVIAL: cfg.keywords.get("trivial", []),
                TaskComplexity.MODERATE: cfg.keywords.get("moderate", []),
                TaskComplexity.COMPLEX: cfg.keywords.get("complex", []),
                TaskComplexity.EXPERT: cfg.keywords.get("expert", []),
            }

    def classify(self, task: str) -> TaskComplexity:
        """Classify task complexity using keyword matching."""
        if task in self._cache:
            return self._cache[task]

        task_lower = task.lower()

        for complexity in reversed(list(TaskComplexity)):
            keywords = self._keywords.get(complexity, [])
            for keyword in keywords:
                if keyword in task_lower:
                    self._cache[task] = complexity
                    return complexity

        word_count = len(task.split())
        if word_count < self.trivial_word_threshold:
            complexity = TaskComplexity.TRIVIAL
        elif word_count < self.moderate_word_threshold:
            complexity = TaskComplexity.MODERATE
        else:
            complexity = TaskComplexity.COMPLEX

        self._cache[task] = complexity
        return complexity

    async def classify_with_llm(self, task: str) -> TaskComplexity:
        """Classify using LLM for more accurate results."""
        if not self.llm_provider:
            return self.classify(task)

        from .base import LLMMessage

        cfg = get_config().classifier

        prompt = f"""Classify this task's complexity level.

Task: {task}

Respond with ONLY one of: TRIVIAL, MODERATE, COMPLEX, EXPERT

- TRIVIAL: Simple yes/no, lookups, basic questions
- MODERATE: Summarization, formatting, basic code
- COMPLEX: Multi-step reasoning, analysis, implementation
- EXPERT: Research, architecture, novel problems"""

        response = await self.llm_provider.chat(
            [LLMMessage(role="user", content=prompt)], temperature=cfg.classification_temperature
        )

        result = response.content.strip().upper()

        for complexity in TaskComplexity:
            if complexity.value.upper() in result:
                self._cache[task] = complexity
                return complexity

        return self.classify(task)

    def clear_cache(self):
        """Clear classification cache."""
        self._cache.clear()
