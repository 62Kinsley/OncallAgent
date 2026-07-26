from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from langchain_agent.agent import run_langgraph_agent
from hypothesis import form_hypothesis
from models import Incident
from tools import post_slack_summary, query_logs, query_metrics

AgentState = Literal["RECEIVED", "INVESTIGATE", "DONE", "FAILED"]


@dataclass
class IncidentRecord:
    incident: Incident
    state: AgentState = "RECEIVED"
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    hypothesis: dict[str, Any] = field(default_factory=dict)
    llm_explanation: str | None = None
    slack_result: dict[str, Any] = field(default_factory=dict)
    agent_trace: list[dict[str, Any]] = field(default_factory=list)
    mode: str = "pipeline"


def transition(record: IncidentRecord, next_state: AgentState, error: str | None = None) -> IncidentRecord:
    record.state = next_state
    record.updated_at = datetime.now(timezone.utc).isoformat()
    record.error = error
    return record


def _fallback_pipeline(incident: Incident) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    """Old fixed pipeline: tools -> rule hypothesis."""
    logs = query_logs(incident.service)
    metrics = query_metrics(incident.service)
    evidence = {"logs": logs, "metrics": metrics}
    hypothesis = form_hypothesis(evidence)
    explanation = (
        f"Rule-based fallback hypothesis: {hypothesis['summary']} "
        f"Recommended action: {hypothesis['recommended_action']}"
    )
    return evidence, hypothesis, explanation


def process_incident(incident: Incident) -> IncidentRecord:
    record = IncidentRecord(incident=incident)
    print(f"[{record.state}] incident accepted: {incident.incident_id}")

    record = transition(record, "INVESTIGATE")
    print(f"[{record.state}] starting investigation for {incident.service}")

    agent_result = run_langgraph_agent(incident.model_dump())
    record.agent_trace = agent_result.get("trace", [])

    if agent_result.get("ok"):
        record.mode = "langgraph_agent"
        record.evidence = agent_result.get("evidence") or {}
        record.hypothesis = agent_result["hypothesis"]
        record.llm_explanation = agent_result.get("llm_explanation")
        print("  - mode: tool_calling_agent")
    else:
        record.mode = "rule_fallback"
        print(f"  - agent unavailable ({agent_result.get('reason')}); using rule fallback")
        evidence, hypothesis, explanation = _fallback_pipeline(incident)
        record.evidence = evidence
        record.hypothesis = hypothesis
        record.llm_explanation = explanation

    print("  - hypothesis:")
    print(f"    id: {record.hypothesis['id']}")
    print(f"    summary: {record.hypothesis['summary']}")
    print(f"    confidence: {record.hypothesis['confidence']}")
    print(f"    recommended_action: {record.hypothesis['recommended_action']}")
    if record.llm_explanation:
        print("  - explanation:")
        print(f"    {record.llm_explanation}")

    record.slack_result = post_slack_summary(
        incident=incident.model_dump(),
        hypothesis=record.hypothesis,
        llm_explanation=record.llm_explanation,
    )
    if record.slack_result.get("skipped"):
        print(f"  - slack: skipped ({record.slack_result.get('reason')})")
    elif record.slack_result.get("ok"):
        print("  - slack: message sent")
    else:
        print(f"  - slack: failed ({record.slack_result})")

    record = transition(record, "DONE")
    print(f"[{record.state}] investigation finished")
    return record
