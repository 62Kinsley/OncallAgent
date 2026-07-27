"""LangChain @tool bindings over investigation adapters."""
from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool

from adapters.logs import query_logs as _query_logs
from adapters.metrics import query_metrics as _query_metrics


@tool
def query_logs(service: str, limit: int = 5) -> str:
    """Fetch application logs for a service during the incident window."""
    result = _query_logs(service=service, limit=limit)
    #dicts are not JSON serializable, so we convert to JSON string here
    return json.dumps(result, ensure_ascii=False)


@tool
def query_metrics(service: str) -> str:
    """Fetch metrics and recent deploy metadata for a service."""
    result = _query_metrics(service=service)
    return json.dumps(result, ensure_ascii=False)


@tool
def submit_investigation_result(
    hypothesis_id: str,
    summary: str,
    confidence: float,
    recommended_action: str,
    explanation: str,
) -> str:
    """Submit the final investigation result when evidence is enough. Call once at the end."""
    payload = {
        "id": hypothesis_id,
        "summary": summary,
        "confidence": float(confidence),
        "recommended_action": recommended_action,
        "explanation": explanation,
    }
    return json.dumps(payload, ensure_ascii=False)


def get_tools() -> list[Any]:
    """Tools list for create_react_agent."""
    return [query_logs, query_metrics, submit_investigation_result]