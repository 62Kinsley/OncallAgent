import json
import os
import urllib.error
import urllib.request
from typing import Any

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


def post_slack_summary(
    incident: dict[str, Any],
    hypothesis: dict[str, Any],
    llm_explanation: str | None = None,
) -> dict[str, Any]:
    """Post an incident summary to Slack via Incoming Webhook.

    Returns a small status dict. Skips sending when SLACK_WEBHOOK_URL is missing.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    if not webhook_url:
        return {
            "ok": False,
            "skipped": True,
            "reason": "SLACK_WEBHOOK_URL not set",
        }

    explanation = llm_explanation or hypothesis.get("summary", "No explanation available.")
    text = (
        f"*OncallAgent alert*\n"
        f"*Incident:* `{incident.get('incident_id')}` ({incident.get('severity')})\n"
        f"*Service:* `{incident.get('service')}`\n"
        f"*Title:* {incident.get('title')}\n"
        f"*Hypothesis:* `{hypothesis.get('id')}` "
        f"(confidence={hypothesis.get('confidence')})\n"
        f"*Action:* {hypothesis.get('recommended_action')}\n"
        f"*Details:* {explanation}"
    )

    payload = json.dumps({"text": text}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
            return {
                "ok": True,
                "skipped": False,
                "status_code": response.status,
                "body": body,
            }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "skipped": False,
            "status_code": exc.code,
            "reason": exc.read().decode("utf-8", errors="replace"),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "skipped": False,
            "reason": str(exc),
        }
