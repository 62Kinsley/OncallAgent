"""Metrics adapters: mock by default, optional CloudWatch Metrics."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any

from adapters.config import (
    aws_region,
    lookback_minutes,
    metrics_namespace,
    metrics_period_seconds,
    use_mock_adapters,
)


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


def _latest_or_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(float(values[-1]), 2)


def _mean_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return round(mean(values), 2)


def _max_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return round(max(values), 2)


def _extract_values(result: dict[str, Any], metric_id: str) -> list[float]:
    for item in result.get("MetricDataResults") or []:
        if item.get("Id") == metric_id:
            return [float(v) for v in (item.get("Values") or [])]
    return []


def _demo_deploy_metadata() -> dict[str, str] | None:
    """Optional teaching-only deploy context via env (not discovered from AWS)."""
    version = os.getenv("CW_DEMO_DEPLOY_VERSION", "").strip()
    change = os.getenv("CW_DEMO_DEPLOY_CHANGE", "").strip()
    deployed_at = os.getenv("CW_DEMO_DEPLOYED_AT", "").strip()
    if not (version or change or deployed_at):
        return None
    return {
        "version": version or "unknown",
        "deployed_at": deployed_at or "unknown",
        "change": change or "unknown",
    }


def _cloudwatch_query_metrics(service: str) -> dict:
    """Read demo custom metrics from CloudWatch (OncallAgent/Demo by default).

    Expected metric names (Dimension ServiceName=<service>):
      - ErrorRatePct
      - LatencyP95Ms
      - CpuUsagePct
    """
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=lookback_minutes())
    namespace = metrics_namespace()
    period = metrics_period_seconds()
    dimensions = [{"Name": "ServiceName", "Value": service}]

    queries = [
        {
            "Id": "error_rate",
            "MetricStat": {
                "Metric": {
                    "Namespace": namespace,
                    "MetricName": "ErrorRatePct",
                    "Dimensions": dimensions,
                },
                "Period": period,
                "Stat": "Average",
            },
            "ReturnData": True,
        },
        {
            "Id": "latency_p95",
            "MetricStat": {
                "Metric": {
                    "Namespace": namespace,
                    "MetricName": "LatencyP95Ms",
                    "Dimensions": dimensions,
                },
                "Period": period,
                "Stat": "Average",
            },
            "ReturnData": True,
        },
        {
            "Id": "cpu",
            "MetricStat": {
                "Metric": {
                    "Namespace": namespace,
                    "MetricName": "CpuUsagePct",
                    "Dimensions": dimensions,
                },
                "Period": period,
                "Stat": "Average",
            },
            "ReturnData": True,
        },
        {
            "Id": "cpu_max",
            "MetricStat": {
                "Metric": {
                    "Namespace": namespace,
                    "MetricName": "CpuUsagePct",
                    "Dimensions": dimensions,
                },
                "Period": period,
                "Stat": "Maximum",
            },
            "ReturnData": True,
        },
    ]

    try:
        client = boto3.client("cloudwatch", region_name=aws_region())
        response = client.get_metric_data(
            MetricDataQueries=queries,
            StartTime=start,
            EndTime=end,
            ScanBy="TimestampAscending",
        )
    except (ClientError, BotoCoreError, Exception) as exc:  # noqa: BLE001
        return {
            "service": service,
            "source": "cloudwatch",
            "namespace": namespace,
            "error": str(exc),
            "window_minutes": lookback_minutes(),
            "error_rate_pct": {"baseline": None, "current": None},
            "p95_latency_ms": {"baseline": None, "current": None},
            "cpu_usage_pct": {"avg": None, "peak": None},
            "recent_deploy": _demo_deploy_metadata(),
        }

    error_vals = _extract_values(response, "error_rate")
    latency_vals = _extract_values(response, "latency_p95")
    cpu_vals = _extract_values(response, "cpu")
    cpu_max_vals = _extract_values(response, "cpu_max")

    # Teaching baselines (env-overridable) so agent can compare spike vs normal.
    try:
        baseline_error = float(os.getenv("CW_BASELINE_ERROR_RATE_PCT", "0.2"))
    except ValueError:
        baseline_error = 0.2
    try:
        baseline_latency = float(os.getenv("CW_BASELINE_P95_LATENCY_MS", "180"))
    except ValueError:
        baseline_latency = 180.0

    current_error = _latest_or_mean(error_vals)
    current_latency = _latest_or_mean(latency_vals)
    cpu_avg = _mean_or_none(cpu_vals)
    cpu_peak = _max_or_none(cpu_max_vals) or _max_or_none(cpu_vals)

    empty = current_error is None and current_latency is None and cpu_avg is None
    note = (
        f"Custom metrics from {namespace} with Dimension ServiceName={service}. "
        "Seed with scripts/seed_demo_metrics.sh if empty."
    )
    if empty:
        note += " No datapoints found in the lookback window."

    return {
        "service": service,
        "source": "cloudwatch",
        "namespace": namespace,
        "window_minutes": lookback_minutes(),
        "error_rate_pct": {
            "baseline": baseline_error,
            "current": current_error,
        },
        "p95_latency_ms": {
            "baseline": baseline_latency,
            "current": current_latency,
        },
        "cpu_usage_pct": {
            "avg": cpu_avg,
            "peak": cpu_peak,
        },
        "recent_deploy": _demo_deploy_metadata(),
        "datapoint_counts": {
            "error_rate": len(error_vals),
            "latency_p95": len(latency_vals),
            "cpu": len(cpu_vals),
        },
        "note": note,
    }


def query_metrics(service: str) -> dict:
    """Public API used by runtime fallback and LangChain tools."""
    if use_mock_adapters():
        return _mock_query_metrics(service=service)
    return _cloudwatch_query_metrics(service=service)
