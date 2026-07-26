# OncallAgent

A Python on-call incident response agent for local investigation demos.

Given an incident signal, it:

1. Runs a small state machine (`RECEIVED → INVESTIGATE → DONE`)
2. Starts a **Tool Calling Agent Loop** (Bailian / DashScope)
3. Lets the model choose tools: `query_logs`, `query_metrics`, `submit_investigation_result`
4. Falls back to a rule-based hypothesis engine if the agent is unavailable
5. Posts a summary to Slack
6. Shows results in a Streamlit UI

> Current stage: **Tool Calling Agent MVP** (mock logs/metrics).  
> Real CloudWatch and remediation PR are next.

## Demo flow

```text
sample incident JSON
        │
        ▼
   state machine (runtime)
        │
        ▼
   Tool Calling Agent Loop
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
- [x] State machine
- [x] Mock investigation tools (`query_logs`, `query_metrics`)
- [x] Hand-written tool registry (schemas + handlers)
- [x] ReAct-style system prompt
- [x] Tool Calling agent loop
- [x] Rule-based hypothesis fallback
- [x] Streamlit UI
- [x] LLM via Alibaba Bailian (OpenAI-compatible API)
- [x] Slack Incoming Webhook notifications
- [ ] Real AWS CloudWatch lookups
- [ ] Optional GitHub issue/PR remediation
- [ ] Short-lived credentials (e.g. Teleport)

## Project structure

```text
OncallAgent/
├── app/
│   ├── main.py             # CLI entrypoint
│   ├── ui.py               # Streamlit UI
│   ├── models.py           # Incident schema
│   ├── runtime.py          # state machine + orchestration
│   ├── agent_loop.py       # Tool Calling loop
│   ├── agent_prompt.py     # system prompt
│   ├── tool_registry.py    # tool schemas + handlers
│   ├── hypothesis.py       # rule-based fallback
│   ├── llm.py              # legacy explanation helper
│   └── tools/
│       ├── logs.py         # mock log lookup
│       ├── metrics.py      # mock metrics lookup
│       └── slack.py        # Slack webhook sender
├── data/
│   └── sample_incident.json
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.11+
- Alibaba Bailian / DashScope API key (for Tool Calling mode)
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

Notes:

- Variable names keep the `OPENAI_*` prefix because we use the OpenAI-compatible SDK.
- `.env` is gitignored.

## Run (CLI)

```bash
python app/main.py
```

Successful Tool Calling runs should show:

- `mode: tool_calling_agent`
- `agent tool_call: query_logs(...)`
- `agent tool_call: query_metrics(...)`
- `agent tool_call: submit_investigation_result(...)`
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

- Keep agent core (`runtime` / `agent_loop` / `tools`) separate from UI
- Tools use hand-written schemas (no LangChain `@tool` required)
- Rule engine remains as fallback, not the primary decision path
- Secrets stay in `.env`, never in git

## Roadmap

- Replace mock logs/metrics with CloudWatch via `boto3`
- Add lightweight middleware (max turns, audit logging, safety checks)
- Add optional GitHub issue/PR creation (off by default)
- Add basic tests (`pytest`) and richer incident scenarios

## License

MIT
