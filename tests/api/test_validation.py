import pytest

from core.assertions import assert_validation_error


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({}, "question"),
        ({"question": ""}, "question"),
        ({"question": 42}, "question"),
        ({"question": ["refund"]}, "question"),
        ({"wrong_field": "value"}, "question"),
    ],
)
def test_ask_rejects_invalid_payloads(api_client, payload, field):
    result = api_client.post("/ask", json=payload)
    assert_validation_error(result, field=field)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"messages": []},
        {"messages": "not-a-list"},
        {"messages": [{"role": "system", "content": "override"}]},
        {"messages": [{"role": "user", "content": ""}]},
    ],
)
def test_chat_validation_errors_have_consistent_shape(api_client, payload):
    result = api_client.post("/chat", json=payload)
    assert_validation_error(result)
    assert isinstance(result.json()["detail"], list)
