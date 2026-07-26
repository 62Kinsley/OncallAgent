"""Hand-written tool schemas + handlers for Tool Calling."""

from __future__ import annotations

import json
from typing import Any, Callable

from tools.logs import query_logs
from tools.metrics import query_metrics

ToolHandler = Callable[..., Any]


def _submit_investigation_result(
    hypothesis_id: str,
    summary: str,
    confidence: float,
    recommended_action: str,
    explanation: str,
) -> dict[str, Any]:
    """Final answer tool. Ends the agent loop when called."""
    return {
        "id": hypothesis_id,
        "summary": summary,
        "confidence": float(confidence),
        "recommended_action": recommended_action,
        "explanation": explanation,
    }


TOOL_HANDLERS: dict[str, ToolHandler] = {
    "query_logs": query_logs,
    "query_metrics": query_metrics,
    "submit_investigation_result": _submit_investigation_result,
}

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "query_logs",
            "description": "Fetch application logs for a service during the incident window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name, e.g. checkout-api",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of log lines to return",
                        "default": 5,
                    },
                },
                "required": ["service"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_metrics",
            "description": "Fetch metrics and recent deploy metadata for a service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name, e.g. checkout-api",
                    },
                },
                "required": ["service"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_investigation_result",
            "description": (
                "Submit the final investigation result when you have enough evidence. "
                "Call this only once at the end."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "hypothesis_id": {
                        "type": "string",
                        "description": "Short machine id, e.g. recent-deploy-timeout-regression",
                    },
                    "summary": {
                        "type": "string",
                        "description": "One-sentence root cause summary",
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence score between 0 and 1",
                    },
                    "recommended_action": {
                        "type": "string",
                        "description": "Immediate next action for on-call",
                    },
                    "explanation": {
                        "type": "string",
                        "description": "4-6 sentence detailed explanation in English",
                    },
                },
                "required": [
                    "hypothesis_id",
                    "summary",
                    "confidence",
                    "recommended_action",
                    "explanation",
                ],
            },
        },
    },
]


def execute_tool(name: str, arguments: dict[str, Any] | str) -> Any:
    if name not in TOOL_HANDLERS:
        return {"error": f"Unknown tool: {name}"}

    if isinstance(arguments, str):
        arguments = json.loads(arguments or "{}")

    handler = TOOL_HANDLERS[name]
    return handler(**arguments)


def tool_result_to_text(result: Any) -> str:
    return json.dumps(result, ensure_ascii=False, default=str)
