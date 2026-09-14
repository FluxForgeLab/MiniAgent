import json
import urllib.request
import urllib.error

from dataclasses import dataclass
from typing import Any, Callable, Literal, Protocol


@dataclass
class ModelOutput:
    kind: Literal["tool_call", "final_answer"]
    name: str | None = None
    arguments: dict[str, Any] | None = None
    content: str | None = None
    tool_call_id: str | None = None


class Model(Protocol):
    def generate(self, messages: list[Any], tools_schema: list[dict[str, Any]]) -> ModelOutput:
        ...


class FakeModel:
    def __init__(self, outputs: list[ModelOutput]) -> None:
        self._outputs = list(outputs)

    def generate(self, messages: list[Any], tools_schema: list[dict[str, Any]]) -> ModelOutput:
        if not self._outputs:
            raise RuntimeError("FakeModel has no more scripted outputs")
        return self._outputs.pop(0)


class OpenAIModel:
    def __init__(
        self,
        model_id: str,
        post: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        self.model_id = model_id
        self._post = post

    def generate(self, messages: list[Any], tools_schema: list[dict[str, Any]]) -> ModelOutput:
        body = build_chat_request(self.model_id, messages, tools_schema)
        payload = self._post(body)
        return parse_completion(payload)


def completion_url(api_base: str) -> str:
    return api_base.rstrip("/") + "/chat/completions"


def auth_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def format_http_error(code: int, body: str) -> str:
    return f"HTTP {code}: {body}"


def make_http_post(
    api_base: str,
    api_key: str,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    url = completion_url(api_base)
    headers = auth_headers(api_key)

    def post(body: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(format_http_error(exc.code, detail)) from exc

    return post


def to_openai_tools(schema: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    for item in schema:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": item["name"],
                    "description": item["description"],
                    "parameters": item["input_schema"],
                }
            }
        )
    return tools


def build_chat_request(
    model_id: str,
    messages: list[Any],
    tools_schema: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "model": model_id,
        "messages": messages,
        "tools": to_openai_tools(tools_schema)
    }


def parse_completion(payload: dict[str, Any]) -> ModelOutput:
    message = payload["choices"][0]["message"]
    tool_calls = message.get("tool_calls") or []
    if tool_calls:
        call = tool_calls[0]
        fn = call["function"]
        return ModelOutput(
            kind="tool_call",
            name=fn["name"],
            arguments=json.loads(fn["arguments"]),
            tool_call_id=call.get("id"),
        )
    return ModelOutput(kind="final_answer", content=message.get("content") or "")
