from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from models import Incident
from tools import query_logs, query_metrics
from hypothesis import form_hypothesis

AgentState = Literal["RECEIVED", "INVESTIGATE", "DONE", "FAILED"]


@dataclass
class IncidentRecord:
    incident: Incident
    state: AgentState = "RECEIVED"
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    hypothesis: dict[str, Any] = field(default_factory=dict)


def transition(record: IncidentRecord, next_state: AgentState, error: str | None = None) -> IncidentRecord:
    record.state = next_state
    record.updated_at = datetime.now(timezone.utc).isoformat()
    record.error = error
    return record

def investigate(incident: Incident) -> dict[str, Any]:
    logs = query_logs(incident.service)
    metrics = query_metrics(incident.service)
    print(f"  - fetched {len(logs)} log lines")

    for line in logs:
        print(f"    [{line['level']}] {line['message']}")

    print("  - fetched metrics:")
    print(f"    error_rate: {metrics['error_rate_pct']}")
    print(f"    p95_latency_ms: {metrics['p95_latency_ms']}")
    print(f"    recent_deploy: {metrics['recent_deploy']}")

    return {"logs": logs, "metrics": metrics}


def process_incident(incident: Incident) -> IncidentRecord:
    record = IncidentRecord(incident=incident)
    print(f"[{record.state}] incident accepted: {incident.incident_id}")

    record = transition(record, "INVESTIGATE")
    print(f"[{record.state}] starting investigation for {incident.service}")

    record.evidence = investigate(incident)
    record.hypothesis = form_hypothesis(record.evidence) 

    print("  - hypothesis:")
    print(f"    id: {record.hypothesis['id']}")
    print(f"    summary: {record.hypothesis['summary']}")
    print(f"    confidence: {record.hypothesis['confidence']}")
    print(f"    recommended_action: {record.hypothesis['recommended_action']}")
    
    record = transition(record, "DONE")
    print(f"[{record.state}] investigation finished (placeholder)")

    return record



