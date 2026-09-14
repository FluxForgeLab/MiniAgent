import sys
import unittest
from pathlib import Path

from client import McpClient
from protocol import PROTOCOL
from registry import CompositeRegistry, McpRegistry
from transport import StdioTransport

from agent import Agent
from model import FakeModel, ModelOutput
from tools import registry as local_registry

ROOT = Path(__file__).resolve().parent
ECHO = [sys.executable, str(ROOT / "servers" / "echo.py")]


def _discover_ok(capabilities=None):
    return {
        "supportedVersions": [PROTOCOL],
        "capabilities": {} if capabilities is None else capabilities,
        "_meta": {
            "io.modelcontextprotocol/serverInfo": {"name": "echo"}
        },
    }


class McpRegistryTest(unittest.TestCase):
    def setUp(self):
        self.client = McpClient(StdioTransport(ECHO, cwd=ROOT))
        self.client.start()
        self.reg = McpRegistry(self.client)
        self.reg.connect()

    def tearDown(self):
        self.client.close()

    def test_connect_sets_prefix_from_server_info(self):
        self.assertEqual(self.reg.prefix, "echo")

    def test_schema_uses_host_prefix(self):
        item = self.reg.schema()[0]
        self.assertEqual(item["name"], "echo_add")
        self.assertNotIn(".", item["name"])
        self.assertIn("properties", item["input_schema"])
        self.assertNotIn("inputSchema", item)

    def test_execute_strips_prefix(self):
        result = self.reg.execute("echo_add", {"a": 3, "b": 5})
        self.assertTrue(result.ok)
        self.assertEqual(result.observation, "8")

    def test_unprefixed_name_does_not_hit_server(self):
        result = self.reg.execute("add", {"a": 3, "b": 5})
        self.assertFalse(result.ok)
        self.assertEqual(result.observation, "unknown tool: add")

    def test_unknown_tool_is_observation(self):
        result = self.reg.execute("echo_nope", {})
        self.assertFalse(result.ok)
        self.assertIn("Unknown tool", result.observation)

    def test_timeout_is_observation(self):
        class Fake:
            def discover(self):
                return _discover_ok({"tools": {}})

            def call_tool(self, name, arguments):
                raise TimeoutError("mcp timeout after 0.5s")

        reg = McpRegistry(Fake())
        reg.connect()
        result = reg.execute("echo_add", {"a": 1, "b": 2})
        self.assertFalse(result.ok)
        self.assertIn("mcp timeout", result.observation)

    def test_unsupported_version_refuses_connect(self):
        class Fake:
            def discover(self):
                return {
                    "supportedVersions": ["1999-01-01"],
                    "capabilities": {"tools": {}},
                    "_meta": {
                        "io.modelcontextprotocol/serverInfo": {"name": "echo"}
                    },
                }

        with self.assertRaises(RuntimeError):
            McpRegistry(Fake()).connect()

    def test_schema_skips_list_tools_without_capability(self):
        class Fake:
            def discover(self):
                return _discover_ok({})

            def list_tools(self):
                raise AssertionError("list_tools should not be called")

        reg = McpRegistry(Fake())
        reg.connect()
        self.assertEqual(reg.schema(), [])


class CompositeRegistryTest(unittest.TestCase):
    def setUp(self):
        self.client = McpClient(StdioTransport(ECHO, cwd=ROOT))
        self.client.start()
        mcp = McpRegistry(self.client)
        mcp.connect()
        self.reg = CompositeRegistry(local_registry, mcp)

    def tearDown(self):
        self.client.close()

    def test_schema_merges_local_and_mcp(self):
        names = [item["name"] for item in self.reg.schema()]
        self.assertIn("get_celsius", names)
        self.assertIn("echo_add", names)

    def test_execute_routes_by_name(self):
        local = self.reg.execute("get_celsius", {"city": "北京"})
        self.assertEqual(local.observation, "26.0")
        remote = self.reg.execute("echo_add", {"a": 3, "b": 5})
        self.assertEqual(remote.observation, "8")

    def test_unknown_tool(self):
        result = self.reg.execute("nope", {})
        self.assertFalse(result.ok)
        self.assertEqual(result.observation, "unknown tool: nope")

    def test_agent_loop_unchanged(self):
        model = FakeModel(
            [
                ModelOutput(
                    kind="tool_call",
                    name="echo_add",
                    arguments={"a": 3, "b": 5},
                ),
                ModelOutput(kind="final_answer", content="8"),
            ]
        )
        agent = Agent(model=model, registry=self.reg, max_steps=6)
        self.assertEqual(agent.run("3 加 5 等于多少？"), "8")
