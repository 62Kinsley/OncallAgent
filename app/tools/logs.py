def query_logs(service: str, limit: int = 5) -> list[dict]:
    """Mock log lookup. Replace with CloudWatch/boto3 later."""
    return [
        {
            "timestamp": "2026-07-22T22:12:15Z",
            "level": "INFO",
            "service": service,
            "message": "Request to /checkout/confirm duration=180ms",
        },
        {
            "timestamp": "2026-07-22T22:12:45Z",
            "level": "WARN",
            "service": service,
            "message": "Request to /checkout/confirm duration=2800ms",
        },
        {
            "timestamp": "2026-07-22T22:13:10Z",
            "level": "ERROR",
            "service": service,
            "message": "TimeoutError: payment-service exceeded 300ms",
        },
        {
            "timestamp": "2026-07-22T22:13:40Z",
            "level": "ERROR",
            "service": service,
            "message": "TimeoutError: payment-service exceeded 300ms",
        },
        {
            "timestamp": "2026-07-22T22:14:05Z",
            "level": "ERROR",
            "service": service,
            "message": "checkout failed with HTTP 500",
        },
    ][:limit]
