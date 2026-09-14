import os
import sys
import unittest
from pathlib import Path

from mcp import StdioServerParameters
from mcp.client import Client

ROOT = Path(__file__).resolve().parent
ECHO = [sys.executable, str(ROOT / "servers" / "echo.py")]

FS = [sys.executable, str(ROOT / "servers" / "filesystem.py")]


def echo_params():
    return stdio_params(ECHO)


def stdio_params(command):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return StdioServerParameters(
        command=command[0],
        args=command[1:],
        cwd=ROOT,
        env=env,
        encoding="utf-8",
    )

class OfficialClientOurEchoTest(unittest.IsolatedAsyncioTestCase):
    async def test_server_info_and_add(self):
        async with Client(echo_params()) as client:
            self.assertEqual(client.server_info.name, "echo")
            listed = await client.list_tools()
            names = [tool.name for tool in listed.tools]
            self.assertIn("add", names)
            result = await client.call_tool("add", {"a": 3, "b": 5})
            self.assertFalse(result.is_error)
            self.assertEqual(result.content[0].text, "8")

class OfficialClientOurFilesystemTest(unittest.IsolatedAsyncioTestCase):
    async def test_read_and_deny_escape(self):
        async with Client(stdio_params(FS)) as client:
            self.assertEqual(client.server_info.name, "filesystem")
            listed = await client.list_tools()
            names = [tool.name for tool in listed.tools]
            self.assertIn("read_file", names)

            ok = await client.call_tool("read_file", {"path": "hello.txt"})
            self.assertFalse(ok.is_error)
            self.assertIn("hello from sandbox", ok.content[0].text)

            denied = await client.call_tool(
                "read_file",
                {"path": "../protocol.py"},
            )
            self.assertTrue(denied.is_error)
            self.assertIn("outside sandbox", denied.content[0].text)
            self.assertNotIn("PROTOCOL", denied.content[0].text)