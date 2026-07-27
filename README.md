# OncallAgent

A Python on-call incident response agent for local investigation demos.

Given an incident signal, it:

1. Runs a small state machine (`RECEIVED → INVESTIGATE → DONE`)
2. Starts a **LangChain `create_agent`** investigation loop
3. Lets the model choose tools: `query_logs`, `query_metrics`, `submit_investigation_result`
4. Falls back to a rule-based hypothesis engine if the agent is unavailable
5. Posts a summary to Slack
6. Shows results in a Streamlit UI

> Current stage: **LangChain agent MVP** (mock logs/metrics).  
> Real CloudWatch and remediation PR are next. RAG is not required for this stage.

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
- [x] LangChain `@tool` wrappers
- [x] ChatOpenAI via Alibaba Bailian (OpenAI-compatible endpoint)
- [x] LangChain `create_agent` with `system_prompt`
- [x] Structured final answer via `submit_investigation_result`
- [x] Rule-based hypothesis fallback
- [x] Streamlit UI
- [x] Slack Incoming Webhook notifications
- [ ] Real AWS CloudWatch lookups
- [ ] Optional runbook RAG
- [ ] Optional GitHub issue/PR remediation
- [ ] Short-lived credentials (e.g. Teleport)

## Project structure

```text
OncallAgent/
├── app/
│   ├── main.py                 # CLI entrypoint
│   ├── ui.py                   # Streamlit UI
│   ├── models.py               # Incident schema
│   ├── runtime.py              # state machine + orchestration
│   ├── hypothesis.py           # rule-based fallback
│   ├── langchain_agent/
│   │   ├── model.py            # ChatModelFactory (ChatOpenAI + Bailian)
│   │   ├── tools.py            # @tool wrappers
│   │   ├── prompt.py           # system prompt
│   │   └── agent.py            # create_agent + result parsing
│   └── tools/
│       ├── logs.py             # mock log lookup
│       ├── metrics.py          # mock metrics lookup
│       └── slack.py            # Slack webhook sender
├── data/
│   └── sample_incident.json
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
```

Important:

- Use **`OPENAI_API_KEY`** (not `API_KEY`)
- Variable names keep the `OPENAI_*` prefix because we use the OpenAI-compatible SDK
- `.env` is gitignored

## Run (CLI)

```bash
python app/main.py
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

1. Click **Load sample incident**
2. Click **Run Investigation**
3. Review mode, hypothesis, explanation, Slack status, agent trace, and evidence

## Design notes

- Agent orchestration uses LangChain `create_agent`
- Tools use `@tool` wrappers over existing `app/tools/*` implementations
- System prompt includes operational rules (max one call per evidence tool, ignore tool `error` payloads, confidence rubric)
- Rule engine remains as fallback, not the primary decision path
- No RAG in this stage: investigation relies on tools for live/mock evidence
- Secrets stay in `.env`, never in git

## Roadmap

- Replace mock logs/metrics with CloudWatch via `boto3`
- Add lightweight middleware (timeouts, audit logging, safety checks)
- Optional runbook / PIR RAG
- Optional GitHub issue/PR creation (off by default)
- Add basic tests (`pytest`) and richer incident scenarios

## License

MIT
