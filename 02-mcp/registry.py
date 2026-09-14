import sys
from pathlib import Path

from client import McpError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "01-mini-agent"))
from tools import ToolResult


def _text(result):
    content = result.get("content") or []
    if not content:
        return ""
    return str(content[0].get("text", ""))


from protocol import PROTOCOL


class McpRegistry:
    def __init__(self, client):
        self.client = client
        self.prefix = ""
        self.capabilities = {}

    def connect(self):
        result = self.client.discover()
        versions = result.get("supportedVersions") or []
        if PROTOCOL not in versions:
            raise RuntimeError(f"unsupported protocol versions: {versions}")
        info = (result.get("_meta") or {}).get(
            "io.modelcontextprotocol/serverInfo"
        ) or {}
        name = info.get("name")
        if not name:
            raise RuntimeError("discover missing serverInfo.name")
        self.prefix = name
        self.capabilities = result.get("capabilities") or {}
        return result

    def schema(self):
        self._require_connected()
        if "tools" not in self.capabilities:
            return []
        items = []
        for tool in self.client.list_tools():
            items.append(
                {
                    "name": self._host_name(tool["name"]),
                    "description": tool.get("description", ""),
                    "input_schema": tool["inputSchema"],
                }
            )
        return items

    def execute(self, name, arguments):
        self._require_connected()
        short = self._short_name(name)
        if short is None:
            return ToolResult(ok=False, observation=f"unknown tool: {name}")
        try:
            result = self.client.call_tool(short, arguments)
        except TimeoutError as exc:
            return ToolResult(ok=False, observation=f"mcp timeout: {exc}")
        except McpError as exc:
            return ToolResult(ok=False, observation=f"mcp error: {exc.message}")
        except Exception as exc:
            return ToolResult(
                ok=False,
                observation=f"mcp error: {type(exc).__name__}: {exc}",
            )
        text = _text(result)
        if result.get("isError"):
            return ToolResult(ok=False, observation=text)
        return ToolResult(ok=True, observation=text)

    def _host_name(self, short):
        return f"{self.prefix}_{short}"

    def _short_name(self, name):
        head = self.prefix + "_"
        if name.startswith(head):
            return name[len(head):]
        return None

    def _require_connected(self):
        if not self.prefix:
            raise RuntimeError("mcp registry not connected")

class CompositeRegistry:
    def __init__(self, *registries):
        self._registries = list(registries)

    def schema(self):
        items = []
        for registry in self._registries:
            items.extend(registry.schema())
        return items

    def execute(self, name, arguments):
        for registry in self._registries:
            owned = [item["name"] for item in registry.schema()]
            if name in owned:
                return registry.execute(name, arguments)
        return ToolResult(ok=False, observation=f"unknown tool: {name}")