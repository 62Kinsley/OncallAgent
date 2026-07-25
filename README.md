# OncallAgent

A Python on-call incident response agent for local investigation demos.

Given an incident signal, it:

1. Runs a small state machine (`RECEIVED → INVESTIGATE → DONE`)
2. Collects investigation evidence (mock logs/metrics for now)
3. Forms a rule-based root-cause hypothesis
4. Asks an LLM (Alibaba Bailian / DashScope) for a human-readable explanation
5. Posts a summary to Slack
6. Shows the result in a Streamlit UI

> Current stage: **working local MVP**.  
> Logs/metrics are still mocked. Real CloudWatch and remediation PR are next.

## Demo flow

```text
sample incident JSON
        │
        ▼
   state machine
        │
        ├─ query_logs (mock)
        ├─ query_metrics (mock)
        ├─ rule-based hypothesis
        ├─ Bailian LLM explanation
        └─ Slack webhook notification
        │
        ▼
   CLI output + Streamlit UI
```

## What works now

- [x] Incident model + JSON input
- [x] State machine
- [x] Mock investigation tools (`query_logs`, `query_metrics`)
- [x] Rule-based root-cause hypothesis
- [x] Streamlit UI
- [x] LLM explanation via Alibaba Bailian (OpenAI-compatible API)
- [x] Slack Incoming Webhook notifications
- [ ] Real AWS CloudWatch lookups
- [ ] Optional GitHub issue/PR remediation
- [ ] Short-lived credentials (e.g. Teleport)

## Project structure

```text
OncallAgent/
├── app/
│   ├── main.py           # CLI entrypoint
│   ├── ui.py             # Streamlit UI
│   ├── models.py         # Incident schema
│   ├── runtime.py        # state machine + investigation flow
│   ├── hypothesis.py     # rule-based hypothesis engine
│   ├── llm.py            # Bailian / DashScope explanation
│   └── tools/
│       ├── logs.py       # mock log lookup
│       ├── metrics.py    # mock metrics lookup
│       └── slack.py      # Slack webhook sender
├── data/
│   └── sample_incident.json
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.11+
- (Optional) Alibaba Bailian / DashScope API key
- (Optional) Slack Incoming Webhook URL

The agent still works without LLM or Slack: those steps are skipped gracefully.

## Setup

```bash
cd OncallAgent
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a local `.env` file in the project root (do **not** commit it):

```text
# Alibaba Bailian / DashScope (OpenAI-compatible mode)
OPENAI_API_KEY=your-bailian-api-key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-plus

# Slack Incoming Webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
```

Notes:

- Variable names keep the `OPENAI_*` prefix because we use the OpenAI-compatible SDK.
- For international DashScope endpoints, you may need:
  `OPENAI_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- `.env` is gitignored.

## Run (CLI)

```bash
python app/main.py
```

Expected output includes:

- loaded incident fields
- state transitions
- mock logs + metrics
- hypothesis id/confidence
- LLM explanation (if Bailian key is set)
- Slack send/skip status
- final state: `DONE`

## Run (Streamlit UI)

```bash
streamlit run app/ui.py
```

Then:

1. Click **Load sample incident**
2. Click **Run Investigation**
3. Review hypothesis, LLM explanation, Slack status, and evidence

## Slack setup (short)

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Create a **Blank app**
3. Enable **Incoming Webhooks**
4. Add a webhook to your workspace/channel
5. Put the webhook URL into `.env` as `SLACK_WEBHOOK_URL`

## Design notes

- Keep agent core (`models` / `runtime` / `tools`) separate from UI
- Use mock tools first; swap in real AWS later without rewriting the whole flow
- LLM and Slack are optional enrichments, not hard dependencies
- Secrets stay in `.env`, never in git

## Roadmap

- Replace mock logs/metrics with CloudWatch via `boto3`
- Add optional GitHub issue/PR creation (off by default)
- Add basic tests (`pytest`) and richer incident scenarios

## License

MIT
