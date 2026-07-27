import json
import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
DATA_DIR = ROOT_DIR / "data"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from incident import Incident
from runtime import process_incident

st.set_page_config(page_title="OncallAgent", page_icon="🦞", layout="centered")
st.title("OncallAgent")
st.caption("Tool Calling Agent: incident -> tools -> hypothesis -> Slack")

sample_files = sorted(DATA_DIR.glob("sample_*.json"))
sample_labels = {path.name: path for path in sample_files}

st.subheader("1. Load incident")
if not sample_labels:
    st.error("No sample_*.json files found in data/")
    st.stop()

selected_name = st.selectbox("Sample incident", options=list(sample_labels.keys()), index=0)
if st.button("Load selected sample"):
    raw = json.loads(sample_labels[selected_name].read_text(encoding="utf-8"))
    st.session_state["incident_raw"] = raw
    st.session_state.pop("record", None)

incident_raw = st.session_state.get("incident_raw")
if not incident_raw:
    st.info("Choose a sample above, then click **Load selected sample**.")
    st.stop()

st.json(incident_raw)

st.subheader("2. Run investigation")
if st.button("Run Investigation", type="primary"):
    incident = Incident.model_validate(incident_raw)
    record = process_incident(incident)
    st.session_state["record"] = {
        "state": record.state,
        "mode": record.mode,
        "hypothesis": record.hypothesis,
        "evidence": record.evidence,
        "llm_explanation": record.llm_explanation,
        "slack_result": record.slack_result,
        "agent_trace": record.agent_trace,
    }

record_data = st.session_state.get("record")
if not record_data:
    st.stop()

st.subheader("3. Result")
st.write(f"**Final state:** `{record_data['state']}`")
st.write(f"**Mode:** `{record_data.get('mode')}`")

hypothesis = record_data["hypothesis"]
st.write("**Hypothesis**")
st.write(f"- ID: `{hypothesis.get('id')}`")
st.write(f"- Summary: {hypothesis.get('summary')}")
st.write(f"- Confidence: `{hypothesis.get('confidence')}`")
st.write(f"- Recommended action: {hypothesis.get('recommended_action')}")

st.write("**Explanation**")
if record_data.get("llm_explanation"):
    st.write(record_data["llm_explanation"])
else:
    st.info("No explanation available.")

st.write("**Slack**")
slack_result = record_data.get("slack_result") or {}
if slack_result.get("skipped"):
    st.info(f"Slack skipped: {slack_result.get('reason')}")
elif slack_result.get("ok"):
    st.success("Slack message sent.")
else:
    st.error(f"Slack failed: {slack_result}")

with st.expander("Agent trace"):
    st.json(record_data.get("agent_trace") or [])

with st.expander("Evidence"):
    st.json(record_data.get("evidence") or {})
