# OncallAgent

A Python on-call incident response agent for local investigation demos.

Given an incident signal, it:

1. Runs a small state machine (`RECEIVED → INVESTIGATE → DONE`)
2. Starts a **LangChain `create_agent`** investigation loop
3. Lets the model choose tools: `query_logs`, `query_metrics`, `submit_investigation_result`
4. Falls back to a rule-based hypothesis engine if the agent is unavailable
5. Posts a summary to Slack
6. Shows results in a Streamlit UI

> Current stage: **LangChain agent MVP** with optional CloudWatch adapters.  
> Default is still mock (no AWS cost). Set `USE_MOCK_ADAPTERS=false` only when you want live CloudWatch.

## Demo flow

```text
sample incident JSON
        │
        ▼
   state machine (runtime)
        │
        ▼
   LangChain create_agent
        ├─ query_logs (mock)
        ├─ query_metrics (mock)
        └─ submit_investigation_result
        │
        ├─ rule fallback (if agent unavailable)
        └─ Slack webhook notification
        │
        ▼
   CLI output + Streamlit UI
```

## What works now

- [x] Incident model + JSON input
- [x] State machine runtime
- [x] Mock investigation tools (`query_logs`, `query_metrics`)
- [x] Optional CloudWatch Logs / Metrics adapters (`USE_MOCK_ADAPTERS`)
- [x] LangChain `@tool` wrappers
- [x] ChatOpenAI via Alibaba Bailian (OpenAI-compatible endpoint)
- [x] LangChain `create_agent` with `system_prompt`
- [x] Structured final answer via `submit_investigation_result`
- [x] Rule-based hypothesis fallback
- [x] Streamlit UI
- [x] Slack Incoming Webhook notifications
- [x] Basic pytest suite (incident / adapters / hypothesis / runtime)
- [ ] Optional runbook RAG
- [ ] Optional GitHub issue/PR remediation
- [ ] Short-lived credentials (e.g. Teleport)

## Project structure

```text
OncallAgent/
├── app/
│   ├── main.py                 # CLI entrypoint
│   ├── ui.py                   # Streamlit UI
│   ├── incident.py             # Incident schema
│   ├── runtime.py              # state machine + orchestration
│   ├── hypothesis.py           # rule-based fallback
│   ├── langchain_agent/
│   │   ├── model.py            # ChatModelFactory (ChatOpenAI + Bailian)
│   │   ├── agent_tools.py      # LangChain @tool bindings
│   │   ├── prompt.py           # system prompt
│   │   └── agent.py            # create_agent + result parsing
│   └── adapters/
│       ├── config.py           # mock/CloudWatch switch + cost limits
│       ├── logs.py             # mock or CloudWatch Logs
│       ├── metrics.py          # mock or CloudWatch Metrics
│       └── slack.py            # Slack webhook sender
├── scripts/
│   └── seed_demo_metrics.sh    # put demo CloudWatch custom metrics
├── data/
│   ├── sample_incident.json          # checkout error-rate spike
│   ├── sample_memory_leak.json
│   ├── sample_db_saturation.json
│   ├── sample_kafka_lag.json
│   ├── sample_external_latency.json
│   └── sample_auth_errors.json
├── requirements.txt
└── README.md
```

Active path: `runtime.py` → `langchain_agent.agent`.

## Prerequisites

- Python 3.11+
- Alibaba Bailian / DashScope API key
- (Optional) Slack Incoming Webhook URL

If the API key is missing, the runtime falls back to the rule-based pipeline.

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

# Keep true for free local demos
USE_MOCK_ADAPTERS=true
```

Important:

- Use **`OPENAI_API_KEY`** (not `API_KEY`)
- Variable names keep the `OPENAI_*` prefix because we use the OpenAI-compatible SDK
- `.env` is gitignored
- **`USE_MOCK_ADAPTERS=true` (default)** never calls AWS

## CloudWatch adapters (optional, low-cost)

Default path stays mock. Only switch when you intentionally want live AWS evidence.

### Safety defaults

| Setting | Default | Why |
|---|---|---|
| `USE_MOCK_ADAPTERS` | `true` | No AWS API calls |
| `CW_LOOKBACK_MINUTES` | `15` (max 60) | Small time window = small scan |
| `CW_MAX_LOG_EVENTS` | `20` (max 50) | Hard cap on returned events |
| Logs filter | `ERROR` | Avoid scanning every INFO line |
| `CW_METRICS_NAMESPACE` | `OncallAgent/Demo` | Custom demo metrics (not AWS/EC2) |

### Enable live CloudWatch

1. Install deps (includes `boto3`):

```bash
pip install -r requirements.txt
```

2. Configure AWS credentials locally (pick one):

```bash
aws configure
# or export AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION
```

3. Put a small test log group in CloudWatch named like:

```text
/aws/service/checkout-api
```

(`CW_LOG_GROUP_PREFIX` defaults to `/aws/service`)

4. Seed demo metrics (ErrorRate / P95 latency / CPU):

```bash
chmod +x scripts/seed_demo_metrics.sh
./scripts/seed_demo_metrics.sh checkout-api
# wait 30-60 seconds for CloudWatch to index datapoints
```

5. In `.env`:

```text
USE_MOCK_ADAPTERS=false
AWS_REGION=us-west-2
CW_LOOKBACK_MINUTES=15
CW_MAX_LOG_EVENTS=20
CW_METRICS_NAMESPACE=OncallAgent/Demo
# optional teaching deploy context
CW_DEMO_DEPLOY_VERSION=v1.84.2
CW_DEMO_DEPLOYED_AT=2026-07-22T22:10:00Z
CW_DEMO_DEPLOY_CHANGE=timeout reduced from 3000ms to 300ms
```

6. Run once:

```bash
python app/main.py --incident data/sample_incident.json
```

If CloudWatch is missing/misconfigured, adapters return an `error` payload instead of crashing; set `USE_MOCK_ADAPTERS=true` again for demos.

### Cost tip

Demo usage (a few FilterLogEvents + GetMetricStatistics calls) is usually near-free. Avoid scanning huge production log groups without time/limit caps. Set an AWS Billing budget alarm (e.g. $5).

## Run (CLI)

```bash
# default sample
python app/main.py

# list available samples
python app/main.py --list

# pick a specific sample
python app/main.py --incident data/sample_db_saturation.json
```

Successful runs should show:

- `Mode: langgraph_agent` (or equivalent agent mode)
- a hypothesis id/confidence
- Slack send/skip status
- `Final state: DONE`

## Run (Streamlit UI)

```bash
streamlit run app/ui.py
```

Then:

1. Choose a sample from the dropdown and click **Load selected sample**
2. Click **Run Investigation**
3. Review mode, hypothesis, explanation, Slack status, agent trace, and evidence

## Run tests

```bash
pip install -r requirements.txt
pytest
```

Tests force `USE_MOCK_ADAPTERS=true` and mock Slack/agent where needed, so they do not call AWS or your LLM.

## Design notes

- Agent orchestration uses LangChain `create_agent`
- LangChain `@tool` bindings in `agent_tools.py` wrap `app/adapters/*` implementations
- System prompt includes operational rules (max one call per evidence tool, ignore tool `error` payloads, confidence rubric)
- Rule engine remains as fallback, not the primary decision path
- No RAG in this stage: investigation relies on tools for live/mock evidence
- Secrets stay in `.env`, never in git

## Roadmap

- Optional production metric dimension mapping beyond the demo namespace
- Add lightweight middleware (timeouts, audit logging, safety checks)
- Optional runbook / PIR RAG
- Optional GitHub issue/PR creation (off by default)
- Richer incident scenarios and adapter integration tests

## License

MIT
