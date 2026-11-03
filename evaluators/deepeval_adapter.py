"""Optional DeepEval adapter; imports DeepEval only when invoked."""

from __future__ import annotations

from typing import Any

from core.exceptions import EvaluationError
from evaluators.base import EvaluationResult, ResponseEvaluator


class DeepEvalAdapter(ResponseEvaluator):
    """Evaluate responses with configured model-judged DeepEval metrics."""

    def __init__(self, *, model: str | None = None, threshold: float = 0.7) -> None:
        self.model = model
        self.threshold = threshold

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
        del expected_sources, actual_sources
        try:
            from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
            from deepeval.test_case import LLMTestCase
        except ImportError as exc:
            raise EvaluationError(
                "DeepEval is not installed. Install the 'llm' extra with: pip install -e .[llm]"
            ) from exc

        kwargs: dict[str, Any] = {"threshold": self.threshold}
        if self.model:
            kwargs["model"] = self.model
        metrics = [AnswerRelevancyMetric(**kwargs), FaithfulnessMetric(**kwargs)]
        test_case = LLMTestCase(
            input=question,
            actual_output=answer,
            expected_output=expected_answer,
            retrieval_context=context,
        )
        scores: list[float] = []
        reasons: list[str] = []
        for metric in metrics:
            try:
                metric.measure(test_case)
            except Exception as exc:  # DeepEval providers expose several error types.
                raise EvaluationError(
                    f"{metric.__class__.__name__} could not run: {exc.__class__.__name__}: {exc}"
                ) from exc
            scores.append(float(metric.score))
            reasons.append(f"{metric.__class__.__name__}: {metric.reason}")
        score = min(scores)
        return EvaluationResult(
            passed=all(value >= self.threshold for value in scores),
            score=score,
            reason=" | ".join(reasons),
            details={"scores": scores, "threshold": self.threshold},
        )
