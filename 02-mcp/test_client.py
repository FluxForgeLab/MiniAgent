import sys
import unittest
from pathlib import Path

from client import McpClient, McpError
from transport import StdioTransport

ROOT = Path(__file__).resolve().parent
ECHO = [sys.executable, str(ROOT / "servers" / "echo.py")]


class McpClientTest(unittest.TestCase):
    def setUp(self):
        self.client = McpClient(StdioTransport(ECHO, cwd=ROOT))
        self.client.start()

    def tearDown(self):
        self.client.close()

    def test_discover(self):
        result = self.client.discover()
        self.assertEqual(result["resultType"], "complete")
        info = result["_meta"]["io.modelcontextprotocol/serverInfo"]
        self.assertEqual(info["name"], "echo")

    def test_list_tools(self):
        tools = self.client.list_tools()
        self.assertEqual(tools[0]["name"], "add")

    def test_call_tool_add(self):
        result = self.client.call_tool("add", {"a": 3, "b": 5})
        self.assertEqual(result["content"][0]["text"], "8")

    def test_unknown_tool_is_rpc_error(self):
        with self.assertRaises(McpError) as ctx:
            self.client.call_tool("nope", {})
        self.assertIn("Unknown tool", ctx.exception.message)