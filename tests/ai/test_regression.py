import json
from pathlib import Path

import pytest

from core.assertions import assert_refusal, assert_status

CASES = json.loads(
    (Path(__file__).parents[2] / "datasets" / "golden_questions.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_golden_dataset_regression(api_client, deterministic_evaluator, case):
    endpoint = "/chat" if case["category"] == "multi_turn" else "/ask"
    request = (
        {"messages": case["messages"]}
        if endpoint == "/chat"
        else {"question": case["question"]}
    )
    response = api_client.post(endpoint, json=request)
    assert_status(response, 200)
    payload = response.json()

    if case.get("expected_behavior") == "refuse":
        assert_refusal(payload)
        assert payload["sources"] == []
        return

    result = deterministic_evaluator.evaluate(
        question=case["question"],
        answer=payload["answer"],
        context=payload["retrieved_context"],
        expected_answer=case.get("expected_answer"),
        expected_sources=case.get("expected_sources"),
        actual_sources=payload["sources"],
    )
    assert result.passed, f"Golden case {case['id']} failed: {result.reason}"
