def query_metrics(service: str) -> dict:
    """Mock metrics lookup. Replace with CloudWatch/boto3 later."""
    return {
        "service": service,
        "error_rate_pct": {"baseline": 0.2, "current": 12.0},
        "p95_latency_ms": {"baseline": 180, "current": 3400},
        "cpu_usage_pct": {"avg": 65, "peak": 91},
        "recent_deploy": {
            "version": "v1.84.2",
            "deployed_at": "2026-07-22T22:10:00Z",
            "change": "timeout reduced from 3000ms to 300ms",
        },
    }
