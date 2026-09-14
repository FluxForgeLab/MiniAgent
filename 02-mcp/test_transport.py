import sys
import unittest
from pathlib import Path

from protocol import encode_request, parse_response
from transport import StdioTransport

ROOT = Path(__file__).resolve().parent
ECHO = [sys.executable, str(ROOT / "servers" / "echo.py")]


class StdioTransportTest(unittest.TestCase):
    def test_request_add(self):
        t = StdioTransport(ECHO, cwd=ROOT)
        t.start()
        try:
            line = encode_request(
                1,
                "tools/call",
                {"name": "add", "arguments": {"a": 3, "b": 5}},
            )
            msg = parse_response(t.request(line))
            self.assertEqual(msg["id"], 1)
            self.assertEqual(msg["result"]["content"][0]["text"], "8")
        finally:
            t.close()

    def test_request_timeout(self):
        hang = [sys.executable, "-c", "import sys; sys.stdin.read()"]
        t = StdioTransport(hang, timeout=0.5)
        t.start()
        try:
            with self.assertRaises(TimeoutError):
                t.request("{}")
        finally:
            t.close()