"""Tool Calling agent loop (Bailian / OpenAI-compatible)."""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv

from agent_prompt import SYSTEM_PROMPT
from tool_registry import TOOL_SCHEMAS, execute_tool, tool_result_to_text

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


def run_agent_loop(incident: dict[str, Any], max_turns: int = 6) -> dict[str, Any]:
    """Run a Tool Calling loop and return structured investigation output."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return {
            "ok": False,
            "reason": "OPENAI_API_KEY not set",
            "hypothesis": None,
            "llm_explanation": None,
            "evidence": {},
            "trace": [],
        }

    from openai import OpenAI

    base_url = os.getenv(
        "OPENAI_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ).strip()
    model = os.getenv("OPENAI_MODEL", "qwen-plus").strip()
    client = OpenAI(api_key=api_key, base_url=base_url)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Investigate this incident and submit a final result.\n\n"
                f"Incident JSON:\n{json.dumps(incident, indent=2)}"
            ),
        },
    ]

    evidence: dict[str, Any] = {"logs": None, "metrics": None}
    trace: list[dict[str, Any]] = []
    final_result: dict[str, Any] | None = None

    for turn in range(1, max_turns + 1):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            temperature=0.2,
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls or []

        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": message.content or "",
        }
        if tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ]
        messages.append(assistant_msg)

        if not tool_calls:
            trace.append({"turn": turn, "event": "no_tool_calls", "content": message.content})
            break

        for tc in tool_calls:
            name = tc.function.name
            raw_args = tc.function.arguments or "{}"
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                args = {}

            print(f"  - agent tool_call: {name}({args})")
            result = execute_tool(name, args)
            trace.append(
                {
                    "turn": turn,
                    "tool": name,
                    "arguments": args,
                    "result_preview": tool_result_to_text(result)[:500],
                }
            )

            if name == "query_logs":
                evidence["logs"] = result
            elif name == "query_metrics":
                evidence["metrics"] = result
            elif name == "submit_investigation_result":
                final_result = result

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result_to_text(result),
                }
            )

        if final_result is not None:
            break

    if final_result is None:
        return {
            "ok": False,
            "reason": "Agent finished without submit_investigation_result",
            "hypothesis": None,
            "llm_explanation": None,
            "evidence": evidence,
            "trace": trace,
        }

    hypothesis = {
        "id": final_result["id"],
        "summary": final_result["summary"],
        "confidence": final_result["confidence"],
        "recommended_action": final_result["recommended_action"],
        "evidence_refs": [],
    }
    return {
        "ok": True,
        "reason": "completed",
        "hypothesis": hypothesis,
        "llm_explanation": final_result.get("explanation"),
        "evidence": evidence,
        "trace": trace,
    }
