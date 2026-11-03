import pytest

from core.assertions import assert_evidence, assert_required_fields, assert_schema, assert_status
from sample_app.main import AnswerResponse


@pytest.mark.parametrize(
    ("question", "source"),
    [
        ("What is the return window?", "refund_policy"),
        ("How long does express shipping take?", "shipping_policy"),
        ("Does the account support MFA?", "account_security"),
    ],
)
def test_ask_answers_known_questions(api_client, question, source):
    result = api_client.post("/ask", json={"question": question})

    assert_status(result, 200)
    payload = result.json()
    assert_required_fields(
        payload, ["answer", "sources", "retrieved_context", "request_id", "refused"]
    )
    assert_schema(payload, AnswerResponse)
    assert_evidence(payload, [source])


def test_ask_unknown_question_is_explicitly_unanswerable(api_client):
    result = api_client.post("/ask", json={"question": "Where is the Paris office?"})

    assert_status(result, 200)
    payload = result.json()
    assert "don't have enough information" in payload["answer"].lower()
    assert payload["sources"] == []
    assert payload["retrieved_context"] == []


def test_chat_uses_prior_user_turn_for_explicit_follow_up(api_client):
    result = api_client.post(
        "/chat",
        json={
            "messages": [
                {"role": "user", "content": "What is the return window?"},
                {"role": "assistant", "content": "Let me check."},
                {"role": "user", "content": "How long is that?"},
            ]
        },
    )

    assert_status(result, 200)
    assert_evidence(result.json(), ["refund_policy"])
