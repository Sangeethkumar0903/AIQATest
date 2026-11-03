import os

import pytest

from evaluators.deepeval_adapter import DeepEvalAdapter


@pytest.mark.llm
def test_optional_model_judged_relevancy_and_faithfulness(api_client, settings):
    if not settings.run_llm_evals:
        pytest.skip("Set RUN_LLM_EVALS=true and configure a DeepEval model to run")
    if not settings.deepeval_model and not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No DEEPEVAL_MODEL or supported provider credentials configured")

    payload = api_client.post("/ask", json={"question": "What is the return window?"}).json()
    result = DeepEvalAdapter(model=settings.deepeval_model).evaluate(
        question="What is the return window?",
        answer=payload["answer"],
        context=payload["retrieved_context"],
    )
    assert result.passed, result.reason
