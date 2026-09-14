import json
import sys

PROTOCOL = "2026-07-28"

ADD_TOOL = {
    "name": "add",
    "description": "两个数相加",
    "inputSchema": {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "加数"},
            "b": {"type": "number", "description": "加数"},
        },
        "required": ["a", "b"],
    }
}

MULTIPLY_TOOL = {
    "name": "multiply",
    "description": "两个数相乘",
    "inputSchema": {
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "乘数"},
            "b": {"type": "number", "description": "乘数"},
        },
        "required": ["a", "b"],
    },
}

def ok_text(req_id, text):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "resultType": "complete",
            "content": [{"type": "text", "text": text}],
            "isError": False,
        },
    }

def ok_tools(req_id):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "resultType": "complete",
            "tools": [ADD_TOOL, MULTIPLY_TOOL]
        }
    }

def ok_discover(req_id):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "resultType": "complete",
            "supportedVersions": [PROTOCOL],
            "capabilities": {"tools": {}},
            "ttlMs": 0,
            "cacheScope": "public",
            "_meta": {
                "io.modelcontextprotocol/serverInfo": {
                    "name": "echo",
                    "version": "0.1",
                }
            },
        },
    }

def rpc_error(req_id, code, message):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": code,
            "message": message,
        },
    }

def handle(req):
    method = req.get("method")
    params = req.get("params") or {}
    req_id = req.get("id")

    if method == "server/discover":
        return ok_discover(req_id)

    if method == "tools/list":
        return ok_tools(req_id)

    if method != "tools/call":
        return None

    name = params.get("name")
    args = params.get("arguments") or {}

    if name == "add":
        return ok_text(req_id, str(args["a"] + args["b"]))
    if name == "multiply":
        return ok_text(req_id, str(args["a"] * args["b"]))
    return rpc_error(req_id, -32603, f"Unknown tool: {name}")

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        req = json.loads(line)
        resp = handle(req)
        if resp is None:
            continue

        print(json.dumps(resp, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
