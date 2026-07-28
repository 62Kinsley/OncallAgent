from adapters import query_logs, query_metrics
from adapters.config import use_mock_adapters


def test_use_mock_adapters_forced_true():
    assert use_mock_adapters() is True


def test_mock_query_logs_returns_entries():
    logs = query_logs("checkout-api", limit=3)
    assert len(logs) == 3
    assert logs[0]["source"] == "mock"
    assert logs[0]["service"] == "checkout-api"


def test_mock_query_metrics_has_expected_shape():
    metrics = query_metrics("checkout-api")
    assert metrics["source"] == "mock"
    assert metrics["error_rate_pct"]["current"] > metrics["error_rate_pct"]["baseline"]
    assert metrics["recent_deploy"]["version"]
