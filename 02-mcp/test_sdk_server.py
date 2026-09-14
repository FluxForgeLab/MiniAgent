import sys
import unittest
from pathlib import Path

from client import McpClient
from transport import StdioTransport

ROOT = Path(__file__).resolve().parent
SDK = [sys.executable, str(ROOT / "servers" / "sdk_add.py")]


class OurClientOfficialServerTest(unittest.TestCase):
    def setUp(self):
        self.client = McpClient(StdioTransport(SDK, cwd=ROOT))
        self.client.start()

    def tearDown(self):
        self.client.close()

    def test_discover(self):
        result = self.client.discover()
        self.assertIn("2026-07-28", result["supportedVersions"])
        info = result["_meta"]["io.modelcontextprotocol/serverInfo"]
        self.assertEqual(info["name"], "sdk-add")

    def test_list_and_call_add(self):
        tools = self.client.list_tools()
        names = [item["name"] for item in tools]
        self.assertIn("add", names)
        result = self.client.call_tool("add", {"a": 3, "b": 5})
        self.assertEqual(result["content"][0]["text"], "8.0")