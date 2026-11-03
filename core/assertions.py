"""Domain assertions with actionable failure messages."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, ValidationError

from core.api_client import TimedResponse


def assert_status(result: TimedResponse, expected: int) -> None:
    assert result.status_code == expected, (
        f"Expected HTTP {expected}, got {result.status_code}. Body: {result.response.text[:500]}"
    )


def assert_schema(payload: Any, schema: type[BaseModel]) -> BaseModel:
    try:
        return schema.model_validate(payload)
    except ValidationError as exc:
        raise AssertionError(f"Response did not match {schema.__name__}: {exc}") from exc


def assert_required_fields(payload: dict[str, Any], fields: Iterable[str]) -> None:
    missing = [field for field in fields if field not in payload]
    assert not missing, f"Response is missing required fields: {missing}. Payload: {payload}"


def assert_validation_error(result: TimedResponse, *, field: str | None = None) -> None:
    assert_status(result, 422)
    detail = result.json().get("detail", [])
    assert detail, f"Expected structured validation details, got: {result.json()}"
    if field:
        locations = [str(item.get("loc", [])) for item in detail]
        assert any(field in location for location in locations), (
            f"Expected validation error for '{field}', got locations {locations}"
        )


def assert_evidence(payload: dict[str, Any], expected_sources: Iterable[str] = ()) -> None:
    sources = payload.get("sources", [])
    context = payload.get("retrieved_context", [])
    expected = list(expected_sources)
    assert sources, f"Expected evidence source IDs, got {sources}"
    assert context, "Expected non-empty retrieved_context for an answerable response"
    missing = [source for source in expected if source not in sources]
    assert not missing, f"Missing expected sources {missing}; actual sources: {sources}"


def assert_latency(result: TimedResponse, maximum_ms: float) -> None:
    assert result.elapsed_ms <= maximum_ms, (
        f"Request took {result.elapsed_ms:.2f} ms; threshold is {maximum_ms:.2f} ms"
    )


def assert_refusal(payload: dict[str, Any]) -> None:
    assert payload.get("refused") is True, f"Expected explicit refusal flag, got: {payload}"
    answer = str(payload.get("answer", "")).lower()
    assert any(term in answer for term in ("can't", "cannot", "won't", "not able")), (
        f"Expected clear refusal language, got: {payload.get('answer')!r}"
    )
