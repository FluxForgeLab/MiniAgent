from dataclasses import dataclass
from typing import Any, Callable, Protocol


@dataclass
class ToolResult:
    ok: bool
    observation: str


class ToolProvider(Protocol):
    def schema(self) -> list[dict[str, Any]]:
        ...

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        ...


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., Any]

    def execute(self, arguments: dict[str, Any]) -> Any:
        required = self.input_schema.get("required") or []
        missing = [key for key in required if key not in arguments]

        if missing:
            raise ValueError(f"missing arguments: {missing}")

        return self.handler(**arguments)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(ok=False, observation=f"unknown tool: {name}")
        try:
            result = tool.execute(arguments)
            return ToolResult(ok=True, observation=str(result))
        except Exception as exc:
            return ToolResult(ok=False, observation=f"tool error: {type(exc).__name__}: {exc}")

    def schema(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]


get_celsius = Tool(
    name="get_celsius",
    description="返回指定城市当前气温（摄氏度）。",
    input_schema={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"},
        },
        "required": ["city"],
    },
    handler=lambda city: 26.0,
)

celsius_to_fahrenheit = Tool(
    name="celsius_to_fahrenheit",
    description="把摄氏度换成华氏度。",
    input_schema={
        "type": "object",
        "properties": {
            "c": {"type": "number", "description": "摄氏度"},
        },
        "required": ["c"],
    },
    handler=lambda c: float(c) * 9 / 5 + 32,
)


registry = ToolRegistry()
registry.register(get_celsius)
registry.register(celsius_to_fahrenheit)
