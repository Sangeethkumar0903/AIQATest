from evaluators.deterministic import contains_unsupported_answer


def test_answer_text_is_supported_by_returned_context(api_client):
    payload = api_client.post("/ask", json={"question": "What is the API rate limit?"}).json()

    assert not contains_unsupported_answer(payload["answer"], payload["retrieved_context"])


def test_unsupported_answer_detector_flags_absent_claim():
    assert contains_unsupported_answer(
        "The API permits one million requests.",
        ["The public API permits 100 requests per minute per API key."],
    )
