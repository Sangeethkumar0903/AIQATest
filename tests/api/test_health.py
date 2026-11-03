from core.assertions import assert_latency, assert_status


def test_health_returns_deterministic_mode(api_client, settings):
    result = api_client.get("/health")

    assert_status(result, 200)
    assert result.json() == {"status": "ok", "mode": "deterministic"}
    assert_latency(result, settings.max_latency_ms)
