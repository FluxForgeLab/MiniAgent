import json
import unittest

from protocol import PROTOCOL, encode_request, parse_response


class ProtocolTest(unittest.TestCase):
    def test_encode_request_puts_meta_in_params(self):
        line = encode_request(1, "server/discover")
        msg = json.loads(line)
        self.assertNotIn("\n", line)
        self.assertEqual(msg["id"], 1)
        self.assertEqual(msg["method"], "server/discover")
        meta = msg["params"]["_meta"]
        self.assertEqual(meta["io.modelcontextprotocol/protocolVersion"], PROTOCOL)

    def test_encode_request_keeps_tool_params(self):
        line = encode_request(
            2,
            "tools/call",
            {"name": "add", "arguments": {"a": 3, "b": 5}},
        )
        params = json.loads(line)["params"]
        self.assertEqual(params["name"], "add")
        self.assertEqual(params["arguments"]["a"], 3)
        self.assertIn("_meta", params)

    def test_parse_response_result(self):
        line = '{"jsonrpc":"2.0","id":1,"result":{"resultType":"complete"}}'
        msg = parse_response(line)
        self.assertEqual(msg["id"], 1)
        self.assertEqual(msg["result"]["resultType"], "complete")

    def test_parse_response_error(self):
        line = '{"jsonrpc":"2.0","id":4,"error":{"code":-32602,"message":"Unknown tool: x"}}'
        msg = parse_response(line)
        self.assertEqual(msg["error"]["code"], -32602)
        self.assertNotIn("result", msg)


if __name__ == "__main__":
    unittest.main()