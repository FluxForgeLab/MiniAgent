import sys
import unittest
from pathlib import Path

from client import McpClient
from transport import StdioTransport

from registry import CompositeRegistry, McpRegistry
from agent import Agent
from model import FakeModel, ModelOutput
from tools import registry as local_registry

ROOT = Path(__file__).resolve().parent
FS = [sys.executable, str(ROOT / "servers" / "filesystem.py")]


class FilesystemServerTest(unittest.TestCase):
    def setUp(self):
        self.client = McpClient(StdioTransport(FS, cwd=ROOT))
        self.client.start()

    def tearDown(self):
        self.client.close()

    def test_discover(self):
        info = self.client.discover()["_meta"]["io.modelcontextprotocol/serverInfo"]
        self.assertEqual(info["name"], "filesystem")

    def test_read_hello(self):
        result = self.client.call_tool("read_file", {"path": "hello.txt"})
        self.assertIn("hello from sandbox", result["content"][0]["text"])

    def test_list_dir(self):
        result = self.client.call_tool("list_dir", {"path": "."})
        self.assertIn("hello.txt", result["content"][0]["text"])

    def test_parent_path_is_denied(self):
        result = self.client.call_tool("read_file", {"path": "../protocol.py"})
        self.assertTrue(result["isError"])
        text = result["content"][0]["text"]
        self.assertIn("outside sandbox", text)
        self.assertNotIn("PROTOCOL", text)

class FilesystemHostTest(unittest.TestCase):
    def setUp(self):
        self.client = McpClient(StdioTransport(FS, cwd=ROOT))
        self.client.start()
        mcp = McpRegistry(self.client)
        mcp.connect()
        self.reg = CompositeRegistry(local_registry, mcp)

    def tearDown(self):
        self.client.close()

    def test_schema_uses_server_prefix(self):
        names = [item["name"] for item in self.reg.schema()]
        self.assertIn("get_celsius", names)
        self.assertIn("filesystem_read_file", names)
        self.assertIn("filesystem_list_dir", names)

    def test_execute_read_hello(self):
        result = self.reg.execute("filesystem_read_file", {"path": "hello.txt"})
        self.assertTrue(result.ok)
        self.assertIn("hello from sandbox", result.observation)

    def test_escape_becomes_observation(self):
        result = self.reg.execute(
            "filesystem_read_file",
            {"path": "../protocol.py"},
        )
        self.assertFalse(result.ok)
        self.assertIn("outside sandbox", result.observation)

    def test_agent_loop_unchanged(self):
        model = FakeModel(
            [
                ModelOutput(
                    kind="tool_call",
                    name="filesystem_read_file",
                    arguments={"path": "hello.txt"},
                ),
                ModelOutput(
                    kind="final_answer",
                    content="hello from sandbox",
                ),
            ]
        )
        agent = Agent(model=model, registry=self.reg, max_steps=6)
        self.assertIn("hello from sandbox", agent.run("读 sandbox 里的 hello.txt"))