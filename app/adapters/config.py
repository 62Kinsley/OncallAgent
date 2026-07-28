"""Shared adapter settings (mock vs CloudWatch)."""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


@lru_cache(maxsize=1)
def use_mock_adapters() -> bool:
    """Default True: never hit AWS unless explicitly disabled."""
    raw = os.getenv("USE_MOCK_ADAPTERS", "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def aws_region() -> str:
    return os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-west-2")).strip()


def log_group_prefix() -> str:
    # Matches TS example: /aws/service/{serviceName}
    return os.getenv("CW_LOG_GROUP_PREFIX", "/aws/service").rstrip("/")


def lookback_minutes() -> int:
    """Hard cap the query window to limit CloudWatch scan cost."""
    try:
        value = int(os.getenv("CW_LOOKBACK_MINUTES", "15"))
    except ValueError:
        value = 15
    return max(1, min(value, 60))


def max_log_events() -> int:
    try:
        value = int(os.getenv("CW_MAX_LOG_EVENTS", "20"))
    except ValueError:
        value = 20
    return max(1, min(value, 50))


def metrics_namespace() -> str:
    """Custom demo namespace (not AWS/EC2) so teaching data is easy to seed."""
    return os.getenv("CW_METRICS_NAMESPACE", "OncallAgent/Demo").strip() or "OncallAgent/Demo"


def metrics_period_seconds() -> int:
    try:
        value = int(os.getenv("CW_METRICS_PERIOD_SECONDS", "60"))
    except ValueError:
        value = 60
    return max(60, min(value, 300))
