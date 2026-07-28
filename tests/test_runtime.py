from runtime import process_incident, transition, IncidentRecord


def test_transition_updates_state(sample_incident):
    record = IncidentRecord(incident=sample_incident)
    assert record.state == "RECEIVED"
    transition(record, "INVESTIGATE")
    assert record.state == "INVESTIGATE"


def test_process_incident_uses_agent_when_ok(monkeypatch, sample_incident):
    def fake_agent(_incident):
        return {
            "ok": True,
            "reason": "completed",
            "hypothesis": {
                "id": "agent-hypothesis",
                "summary": "timeout too aggressive",
                "confidence": 0.9,
                "recommended_action": "rollback",
            },
            "llm_explanation": "logs and metrics agree",
            "evidence": {"logs": [], "metrics": {}},
            "trace": [{"event": "tool_call", "tool": "query_logs"}],
        }

    monkeypatch.setattr("runtime.run_langgraph_agent", fake_agent)
    monkeypatch.setattr(
        "runtime.post_slack_summary",
        lambda **_kwargs: {"ok": True, "skipped": True, "reason": "test"},
    )

    record = process_incident(sample_incident)
    assert record.state == "DONE"
    assert record.mode == "langgraph_agent"
    assert record.hypothesis["id"] == "agent-hypothesis"
    assert record.slack_result["skipped"] is True


def test_process_incident_falls_back_when_agent_unavailable(monkeypatch, sample_incident):
    def fake_agent(_incident):
        return {
            "ok": False,
            "reason": "OPENAI_API_KEY not set",
            "hypothesis": None,
            "llm_explanation": None,
            "evidence": {},
            "trace": [],
        }

    monkeypatch.setattr("runtime.run_langgraph_agent", fake_agent)
    monkeypatch.setattr(
        "runtime.post_slack_summary",
        lambda **_kwargs: {"ok": False, "skipped": True, "reason": "test"},
    )

    record = process_incident(sample_incident)
    assert record.state == "DONE"
    assert record.mode == "rule_fallback"
    assert record.hypothesis["id"]
    assert record.evidence["logs"]
    assert record.evidence["metrics"]
