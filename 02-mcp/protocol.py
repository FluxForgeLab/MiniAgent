import json

PROTOCOL = "2026-07-28"

def client_meta():
    return {
        "io.modelcontextprotocol/protocolVersion": PROTOCOL,
        "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {
            "name": "mini-agent",
            "version": "0.1",
        },
    }

def encode_request(req_id, method, extra_params=None):
    params = dict(extra_params or {})
    params["_meta"] = client_meta()
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        },
        ensure_ascii=False,
    )

def parse_response(line):
    return json.loads(line)