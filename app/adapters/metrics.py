"""Metrics adapters: mock by default, optional CloudWatch Metrics."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean

from adapters.config import aws_region, lookback_minutes, use_mock_adapters


def _mock_query_metrics(service: str) -> dict:
    """Local fake metrics so demos work without AWS."""
    return {
        "service": service,
        "source": "mock",
        "error_rate_pct": {"baseline": 0.2, "current": 12.0},
        "p95_latency_ms": {"baseline": 180, "current": 3400},
        "cpu_usage_pct": {"avg": 65, "peak": 91},
        "recent_deploy": {
            "version": "v1.84.2",
            "deployed_at": "2026-07-22T22:10:00Z",
            "change": "timeout reduced from 3000ms to 300ms",
        },
    }


def _cloudwatch_query_metrics(service: str) -> dict:
    """Fetch a small CPUUtilization window as a starting CloudWatch metrics signal.

    Namespace/dimensions are configurable later; for teaching we use AWS/EC2-style
    CPUUtilization with a ServiceName dimension when present, and always return a
    stable shape for the agent.
    """
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=lookback_minutes())
    namespace = "AWS/EC2"
    metric_name = "CPUUtilization"

    try:
        client = boto3.client("cloudwatch", region_name=aws_region())
        response = client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=[{"Name": "ServiceName", "Value": service}],
            StartTime=start,
            EndTime=end,
            Period=300,
            Statistics=["Average", "Maximum"],
        )
    except (ClientError, BotoCoreError, Exception) as exc:  # noqa: BLE001
        return {
            "service": service,
            "source": "cloudwatch",
            "error": str(exc),
            "window_minutes": lookback_minutes(),
            "cpu_usage_pct": None,
            "raw_datapoints": [],
        }

    points = response.get("Datapoints") or []
    points_sorted = sorted(points, key=lambda p: p.get("Timestamp") or start)
    averages = [float(p["Average"]) for p in points_sorted if "Average" in p]
    maximums = [float(p["Maximum"]) for p in points_sorted if "Maximum" in p]

    raw = [
        {
            "timestamp": p["Timestamp"].astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "average": p.get("Average"),
            "maximum": p.get("Maximum"),
        }
        for p in points_sorted
        if "Timestamp" in p
    ]

    return {
        "service": service,
        "source": "cloudwatch",
        "namespace": namespace,
        "metric_name": metric_name,
        "window_minutes": lookback_minutes(),
        "cpu_usage_pct": {
            "avg": round(mean(averages), 2) if averages else None,
            "peak": round(max(maximums), 2) if maximums else None,
        },
        # Keep fields the rule/agent already understand; fill when unknown.
        "error_rate_pct": {"baseline": None, "current": None},
        "p95_latency_ms": {"baseline": None, "current": None},
        "recent_deploy": None,
        "raw_datapoints": raw,
        "note": (
            "CPUUtilization via Dimension ServiceName={service}. "
            "If empty, your metric dimensions may differ; keep USE_MOCK_ADAPTERS=true for demos."
        ).format(service=service),
    }


def query_metrics(service: str) -> dict:
    """Public API used by runtime fallback and LangChain tools."""
    if use_mock_adapters():
        return _mock_query_metrics(service=service)
    return _cloudwatch_query_metrics(service=service)
