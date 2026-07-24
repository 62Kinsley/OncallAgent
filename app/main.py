import json
from pathlib import Path

from models import Incident
from runtime import process_incident


def load_incident(path: str) -> Incident:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return Incident.model_validate(raw)


if __name__ == "__main__":
    incident = load_incident("data/sample_incident.json")
    print("Incident loaded successfully:")
    print(f"- ID: {incident.incident_id}")
    print(f"- Service: {incident.service}")
    print(f"- Severity: {incident.severity}")
    print(f"- Title: {incident.title}")
    print(f"- Summary: {incident.summary}")
    print("---")
    record = process_incident(incident)
    print("---")
    print(f"Final state: {record.state}")
