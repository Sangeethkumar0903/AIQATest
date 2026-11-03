"""Transparent offline regression checks (not model-based judging)."""

from __future__ import annotations

import re

from evaluators.base import EvaluationResult, ResponseEvaluator


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


class DeterministicEvaluator(ResponseEvaluator):
    """Check expected text, sources, and whether answer claims appear in evidence."""

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
        del question  # Interface parity with evaluators that use the question.
        failures: list[str] = []
        normalized_answer = _normalize(answer)

        if expected_answer and _normalize(expected_answer) not in normalized_answer:
            failures.append("expected answer text was not present")

        missing_sources = sorted(set(expected_sources or []) - set(actual_sources or []))
        if missing_sources:
            failures.append(f"missing expected sources: {missing_sources}")

        # For evidence-bearing responses, the deterministic sample app should return text
        # found verbatim in retrieved context. This is a scoped regression guard, not a
        # general-purpose hallucination detector.
        if context and not any(normalized_answer in _normalize(item) for item in context):
            failures.append("answer was not directly supported by retrieved context")

        return EvaluationResult(
            passed=not failures,
            score=1.0 if not failures else 0.0,
            reason="; ".join(failures) if failures else "all deterministic checks passed",
            details={"missing_sources": missing_sources},
        )


def contains_unsupported_answer(answer: str, context: list[str]) -> bool:
    """Flag a deterministic answer absent from all supplied context strings."""

    if not context:
        return bool(answer.strip())
    normalized = _normalize(answer)
    return not any(normalized in _normalize(item) for item in context)
