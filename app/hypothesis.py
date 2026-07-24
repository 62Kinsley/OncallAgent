from typing import Any


def form_hypothesis(evidence: dict[str, Any]) -> dict[str, Any]:
    """Rule-based root-cause hypothesis from investigation evidence."""
    logs = evidence.get("logs", [])
    metrics = evidence.get("metrics", {})

    timeout_logs = []
    for line in logs:
        if "timeout" in line.get("message", "").lower():
            timeout_logs.append(line)
            
    error_rate = metrics.get("error_rate_pct", {})
    recent_deploy = metrics.get("recent_deploy")

    error_spiked = error_rate.get("current", 0) > error_rate.get("baseline", 0) * 5
    has_timeouts = len(timeout_logs) > 0
    has_recent_deploy = recent_deploy is not None

    if has_timeouts and has_recent_deploy and error_spiked:
        return {
            "id": "recent-deploy-timeout-regression",
            "summary": "Recent deploy likely caused downstream timeouts.",
            "confidence": 0.86,
            "recommended_action": "Rollback the deploy or restore the previous timeout value.",
            "evidence_refs": [
                f"timeout_log_count={len(timeout_logs)}",
                f"error_rate={error_rate}",
                f"recent_deploy={recent_deploy}",
            ],
        }

    if has_timeouts and error_spiked:
        return {
            "id": "downstream-timeout",
            "summary": "Downstream timeouts are correlated with the error spike.",
            "confidence": 0.72,
            "recommended_action": "Inspect downstream dependency latency and timeout settings.",
            "evidence_refs": [
                f"timeout_log_count={len(timeout_logs)}",
                f"error_rate={error_rate}",
            ],
        }

    return {
        "id": "insufficient-evidence",
        "summary": "Not enough signal to form a strong root-cause hypothesis.",
        "confidence": 0.2,
        "recommended_action": "Gather more logs, metrics, and deploy history.",
        "evidence_refs": [],
    }
