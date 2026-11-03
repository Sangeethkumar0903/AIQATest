"""Evaluator interfaces shared by offline and model-judged strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    passed: bool
    score: float | None
    reason: str
    details: dict[str, Any] = field(default_factory=dict)


class ResponseEvaluator(ABC):
    @abstractmethod
    def evaluate(
        self,
        *,
        question: str,
        answer: str,
        context: list[str],
        expected_answer: str | None = None,
        expected_sources: list[str] | None = None,
        actual_sources: list[str] | None = None,
    ) -> EvaluationResult:
        """Evaluate one answer and return an explainable result."""
