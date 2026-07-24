# OncallAgent

A Python on-call incident response agent.

It takes an incident signal, runs a small state machine, gathers investigation evidence (logs/metrics), and will later produce a root-cause hypothesis, notify Slack, and optionally open a GitHub PR.

> Current stage: **local MVP with mock tools** (no real AWS/LLM/Slack yet).

## What works now

1. Load a structured incident from JSON
2. Process it through states: `RECEIVED → INVESTIGATE → DONE`
3. Collect mock evidence via:
   - `query_logs`
   - `query_metrics`

## Project structure

```text
OncallAgent/
├── app/
│   ├── main.py          # entrypoint
│   ├── models.py        # Incident schema
│   ├── runtime.py       # state machine + investigation flow
│   └── tools/
│       ├── logs.py      # mock log lookup
│       └── metrics.py   # mock metrics lookup
├── data/
│   └── sample_incident.json
├── requirements.txt
└── README.md
```

## Quick start

```bash
cd OncallAgent
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app/main.py
```

Expected output includes:

- incident fields loaded from `data/sample_incident.json`
- state transitions
- mock logs + metrics evidence
- final state: `DONE`

## Roadmap

- [x] Incident model + JSON input
- [x] State machine
- [x] Mock investigation tools
- [ ] Rule-based root-cause hypothesis
- [ ] Streamlit UI
- [ ] Real LLM tool-calling
- [ ] Slack notifications
- [ ] Real AWS lookups (CloudWatch)
- [ ] Optional GitHub PR remediation
- [ ] Short-lived credentials (e.g. Teleport)

## Design notes

- Keep the agent core (`models` / `runtime` / `tools`) separate from any UI
- Mock tools first, replace with real integrations later
- Remediation actions should stay opt-in and off by default

## License

MIT
