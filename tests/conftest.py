import os

import pytest

# Force mock adapters for unit tests (never hit AWS/Slack unintentionally).
os.environ["USE_MOCK_ADAPTERS"] = "true"
os.environ.pop("SLACK_WEBHOOK_URL", None)


@pytest.fixture(autouse=True)
def _reset_adapter_config_cache():
    from adapters.config import use_mock_adapters

    use_mock_adapters.cache_clear()
    yield
    use_mock_adapters.cache_clear()


@pytest.fixture
def sample_incident():
    from incident import Incident

    return Incident(
        incident_id="inc-test-001",
        title="checkout-api error rate spike",
        severity="SEV2",
        service="checkout-api",
        started_at="2026-07-22T22:12:00Z",
        summary="P95 latency jumped and 500 errors increased after a recent deploy.",
        initial_context="Suspect timeout config change in the latest release.",
    )
