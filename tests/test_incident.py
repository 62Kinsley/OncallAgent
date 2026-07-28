import json
from pathlib import Path

from incident import Incident


ROOT = Path(__file__).resolve().parents[1]


def test_incident_model_accepts_required_fields(sample_incident):
    assert sample_incident.service == "checkout-api"
    assert sample_incident.initial_context.startswith("Suspect")


def test_sample_incident_json_loads():
    path = ROOT / "data" / "sample_incident.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    incident = Incident.model_validate(raw)
    assert incident.incident_id == "inc-2026-07-22-001"
    assert incident.service == "checkout-api"
