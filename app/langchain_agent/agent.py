from __future__ import annotations
import json
from typing import Any
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain.agents import create_agent

from langchain_agent.model import ChatModelFactory
from langchain_agent.prompt import SYSTEM_PROMPT
from langchain_agent.tools import get_tools


def build_agent():
    model = ChatModelFactory().generator()
    if model is None:
        return None
    return create_agent(
        model=model,
        tools=get_tools(),
        system_prompt=SYSTEM_PROMPT,
    )


def _parse_submit_payload(messages: list[Any]) -> dict[str, Any] | None:
    for message in reversed(messages):
        if isinstance(message, ToolMessage) and message.name == "submit_investigation_result":
            try:
                return json.loads(message.content)
            except json.JSONDecodeError:
                return None
    return None


def _collect_evidence(messages: list[Any]) -> dict[str, Any]:
    evidence: dict[str, Any] = {"logs": None, "metrics": None}
    for message in messages:
        if not isinstance(message, ToolMessage):
            continue
        try:
            payload = json.loads(message.content)
        except json.JSONDecodeError:
            continue
        if message.name == "query_logs":
            evidence["logs"] = payload
        elif message.name == "query_metrics":
            evidence["metrics"] = payload
    return evidence


def _build_trace(messages: list[Any]) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    for message in messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                trace.append(
                    {
                        "event": "tool_call",
                        "tool": call.get("name"),
                        "arguments": call.get("args"),
                    }
                )
        elif isinstance(message, ToolMessage):
            trace.append(
                {
                    "event": "tool_result",
                    "tool": message.name,
                    "content_preview": str(message.content)[:300],
                }
            )
    return trace


def run_langgraph_agent(incident: dict[str, Any]) -> dict[str, Any]:
    agent = build_agent()
    if agent is None:
        return {
            "ok": False,
            "reason": "OPENAI_API_KEY not set",
            "hypothesis": None,
            "llm_explanation": None,
            "evidence": {},
            "trace": [],
        }

    result = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "Investigate this incident and submit a final result.\n\n"
                        f"Incident JSON:\n{json.dumps(incident, indent=2)}"
                    )
                )
            ]
        }
    )

    messages = result.get("messages", [])
    submit_payload = _parse_submit_payload(messages)
    evidence = _collect_evidence(messages)
    trace = _build_trace(messages)

    if not submit_payload:
        return {
            "ok": False,
            "reason": "Agent finished without submit_investigation_result",
            "hypothesis": None,
            "llm_explanation": None,
            "evidence": evidence,
            "trace": trace,
        }

    hypothesis = {
        "id": submit_payload.get("id"),
        "summary": submit_payload.get("summary"),
        "confidence": submit_payload.get("confidence"),
        "recommended_action": submit_payload.get("recommended_action"),
        "evidence_refs": [],
    }
    return {
        "ok": True,
        "reason": "completed",
        "hypothesis": hypothesis,
        "llm_explanation": submit_payload.get("explanation"),
        "evidence": evidence,
        "trace": trace,
    }