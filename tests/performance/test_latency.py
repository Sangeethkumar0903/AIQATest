from statistics import mean, median

import pytest

from core.assertions import assert_latency, assert_status


@pytest.mark.performance
def test_repeated_health_latency(api_client, settings, record_property):
    results = [api_client.get("/health") for _ in range(10)]
    values = [result.elapsed_ms for result in results]

    for result in results:
        assert_status(result, 200)
        assert_latency(result, settings.max_latency_ms)

    record_property("requests", len(values))
    record_property("mean_ms", round(mean(values), 2))
    record_property("median_ms", round(median(values), 2))
    record_property("max_ms", round(max(values), 2))
