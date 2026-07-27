"""Log adapters: mock by default, optional CloudWatch Logs."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from adapters.config import (
    aws_region,
    log_group_prefix,
    lookback_minutes,
    max_log_events,
    use_mock_adapters,
)


def _mock_query_logs(service: str, limit: int = 5) -> list[dict]:
    """Local fake evidence so demos work without AWS."""
    return [
        {
            "timestamp": "2026-07-22T22:12:15Z",
            "level": "INFO",
            "service": service,
            "message": "Request to /checkout/confirm duration=180ms",
            "source": "mock",
        },
        {
            "timestamp": "2026-07-22T22:12:45Z",
            "level": "WARN",
            "service": service,
            "message": "Request to /checkout/confirm duration=2800ms",
            "source": "mock",
        },
        {
            "timestamp": "2026-07-22T22:13:10Z",
            "level": "ERROR",
            "service": service,
            "message": "TimeoutError: payment-service exceeded 300ms",
            "source": "mock",
        },
        {
            "timestamp": "2026-07-22T22:13:40Z",
            "level": "ERROR",
            "service": service,
            "message": "TimeoutError: payment-service exceeded 300ms",
            "source": "mock",
        },
        {
            "timestamp": "2026-07-22T22:14:05Z",
            "level": "ERROR",
            "service": service,
            "message": "checkout failed with HTTP 500",
            "source": "mock",
        },
    ][:limit]


def _guess_level(message: str) -> str:
    upper = message.upper()
    if "ERROR" in upper or "EXCEPTION" in upper or "TIMEOUT" in upper:
        return "ERROR"
    if "WARN" in upper:
        return "WARN"
    return "INFO"


def _cloudwatch_query_logs(service: str, limit: int = 5) -> list[dict]:
    """Read a small recent window from CloudWatch Logs (FilterLogEvents)."""
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    capped = max(1, min(limit, max_log_events()))
    log_group = f"{log_group_prefix()}/{service}"
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=lookback_minutes())

    try:
        client = boto3.client("logs", region_name=aws_region())
        response = client.filter_log_events(
            logGroupName=log_group,
            startTime=int(start.timestamp() * 1000),
            endTime=int(end.timestamp() * 1000),
            limit=capped,
            # Prefer errors to keep scans small and useful for on-call.
            filterPattern="ERROR",
        )
    except (ClientError, BotoCoreError, Exception) as exc:  # noqa: BLE001
        return [
            {
                "timestamp": end.isoformat().replace("+00:00", "Z"),
                "level": "ERROR",
                "service": service,
                "message": f"CloudWatch Logs query failed for {log_group}: {exc}",
                "source": "cloudwatch",
                "error": True,
            }
        ]

    events = response.get("events") or []
    entries: list[dict] = []
    for event in events[:capped]:
        message = event.get("message") or ""
        ts_ms = event.get("timestamp")
        if isinstance(ts_ms, (int, float)):
            timestamp = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        else:
            timestamp = end.isoformat().replace("+00:00", "Z")
        entries.append(
            {
                "timestamp": timestamp,
                "level": _guess_level(message),
                "service": service,
                "message": message.strip(),
                "source": "cloudwatch",
                "log_group": log_group,
            }
        )

    if not entries:
        return [
            {
                "timestamp": end.isoformat().replace("+00:00", "Z"),
                "level": "INFO",
                "service": service,
                "message": (
                    f"No ERROR events in {log_group} for the last "
                    f"{lookback_minutes()} minutes"
                ),
                "source": "cloudwatch",
            }
        ]
    return entries


def query_logs(service: str, limit: int = 5) -> list[dict]:
    """Public API used by runtime fallback and LangChain tools."""
    if use_mock_adapters():
        return _mock_query_logs(service=service, limit=limit)
    return _cloudwatch_query_logs(service=service, limit=limit)
