from protocol import encode_request, parse_response


class McpError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class McpClient:
    def __init__(self, transport):
        self.transport = transport
        self._next_id = 1

    def start(self):
        self.transport.start()

    def close(self):
        self.transport.close()

    def discover(self):
        return self._rpc("server/discover")

    def list_tools(self):
        return self._rpc("tools/list")["tools"]

    def call_tool(self, name, arguments):
        return self._rpc(
            "tools/call",
            {"name": name, "arguments": arguments},
        )

    def _rpc(self, method, extra_params=None):
        req_id = self._next_id
        self._next_id += 1
        line = encode_request(req_id, method, extra_params)
        msg = parse_response(self.transport.request(line))
        if "error" in msg:
            err = msg["error"]
            raise McpError(err.get("code"), err.get("message", ""))
        return msg["result"]