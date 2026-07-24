import json
import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from models import Incident
from runtime import process_incident

st.set_page_config(page_title="OncallAgent", page_icon="🦞", layout="centered")
st.title("OncallAgent")
st.caption("Local MVP: incident -> investigate -> hypothesis -> LLM explanation")

sample_path = ROOT_DIR / "data" / "sample_incident.json"

st.subheader("1. Load incident")
if st.button("Load sample incident"):
    raw = json.loads(sample_path.read_text(encoding="utf-8"))
    st.session_state["incident_raw"] = raw

incident_raw = st.session_state.get("incident_raw")
if not incident_raw:
    st.info("Click the button above to load a sample incident.")
    st.stop()

st.json(incident_raw)

st.subheader("2. Run investigation")
if st.button("Run Investigation", type="primary"):
    incident = Incident.model_validate(incident_raw)
    record = process_incident(incident)
    st.session_state["record"] = {
        "state": record.state,
        "hypothesis": record.hypothesis,
        "evidence": record.evidence,
        "llm_explanation": record.llm_explanation,
    }

record_data = st.session_state.get("record")
if not record_data:
    st.stop()

st.subheader("3. Result")
st.write(f"**Final state:** `{record_data['state']}`")

hypothesis = record_data["hypothesis"]
st.write("**Hypothesis**")
st.write(f"- ID: `{hypothesis.get('id')}`")
st.write(f"- Summary: {hypothesis.get('summary')}")
st.write(f"- Confidence: `{hypothesis.get('confidence')}`")
st.write(f"- Recommended action: {hypothesis.get('recommended_action')}")

st.write("**LLM explanation**")
if record_data.get("llm_explanation"):
    st.write(record_data["llm_explanation"])
else:
    st.info("No LLM explanation. Set OPENAI_API_KEY in `.env` (Bailian/DashScope).")

with st.expander("Evidence"):
    st.json(record_data["evidence"])
