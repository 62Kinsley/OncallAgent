import argparse
import json
from pathlib import Path

from incident import Incident
from runtime import process_incident

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def list_sample_incidents() -> list[Path]:
    return sorted(DATA_DIR.glob("sample_*.json"))


def load_incident(path: str | Path) -> Incident:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return Incident.model_validate(raw)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OncallAgent investigation on a sample incident.")
    parser.add_argument(
        "--incident",
        default=str(DATA_DIR / "sample_incident.json"),
        help="Path to incident JSON (default: data/sample_incident.json)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available sample incident files and exit",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.list:
        samples = list_sample_incidents()
        if not samples:
            print("No sample_*.json files found in data/")
        else:
            print("Available sample incidents:")
            for path in samples:
                print(f"- {path.relative_to(ROOT_DIR)}")
        raise SystemExit(0)

    incident_path = Path(args.incident)
    if not incident_path.is_absolute():
        incident_path = ROOT_DIR / incident_path

    incident = load_incident(incident_path)
    print(f"Incident loaded from {incident_path.relative_to(ROOT_DIR)}:")
    print(f"- ID: {incident.incident_id}")
    print(f"- Service: {incident.service}")
    print(f"- Severity: {incident.severity}")
    print(f"- Title: {incident.title}")
    print(f"- Summary: {incident.summary}")

    print("---")
    record = process_incident(incident)
    print("---")

    print(f"Final state: {record.state}")
    print(f"Mode: {record.mode}")
    print(f"Hypothesis: {record.hypothesis['id']} ({record.hypothesis['confidence']})")
