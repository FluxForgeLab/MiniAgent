import json
from typing import Any

from memory import Memory


def build(memory: Memory) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [{"role": "user", "content": memory.task}]
    for step in memory.steps:
        if step.tool_call is not None:
            messages.append(
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": step.tool_call.get("id"),
                            "type": "function",
                            "function": {
                                "name": step.tool_call.get("name"),
                                "arguments": json.dumps(
                                    step.tool_call.get("arguments") or {},
                                    ensure_ascii=False,
                                ),
                            },
                        }
                    ],
                }
            )
        if step.observation is not None:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": (step.tool_call or {}).get("id"),
                    "content": step.observation,
                }
            )
        if step.error is not None:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": (step.tool_call or {}).get("id"),
                    "content": step.error,
                }
            )
    return messages