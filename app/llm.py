import json
import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()


def explain_hypothesis(
    incident: dict[str, Any],
    evidence: dict[str, Any],
    hypothesis: dict[str, Any],
) -> str | None:
    """Ask the LLM to write a short human-readable explanation.

    Returns None when OPENAI_API_KEY is missing or the call fails,
    so the app can still run with rule-based hypothesis only.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "qwen3.7-plus")
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    prompt = f"""
You are an on-call engineer. Write a concise incident explanation in English.

Incident:
{json.dumps(incident, indent=2)}

Evidence:
{json.dumps(evidence, indent=2)}

Rule-based hypothesis:
{json.dumps(hypothesis, indent=2)}

Requirements:
- 4 to 6 sentences
- Mention likely root cause, key evidence, and next action
- Do not invent services or metrics not present in the input
""".strip()

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a careful on-call incident analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as exc:  # noqa: BLE001
        return f"LLM explanation unavailable: {exc}"
