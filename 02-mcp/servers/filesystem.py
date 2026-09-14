import json
import sys
from pathlib import Path

PROTOCOL = "2026-07-28"
ROOT = Path(__file__).resolve().parent.parent / "sandbox"

LIST_DIR = {
    "name": "list_dir",
    "description": "列出目录中的文件名",
    "inputSchema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "相对 sandbox 的目录"},
        },
        "required": ["path"],
    },
}

READ_FILE = {
    "name": "read_file",
    "description": "读取文本文件",
    "inputSchema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "相对 sandbox 的文件"},
        },
        "required": ["path"],
    },
}


def ok_text(req_id, text, is_error=False):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "resultType": "complete",
            "content": [{"type": "text", "text": text}],
            "isError": is_error,
        },
    }


def ok_tools(req_id):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "resultType": "complete",
            "tools": [LIST_DIR, READ_FILE],
            "ttlMs": 0,
            "cacheScope": "public",
        },
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
                    "name": "filesystem",
                    "version": "0.1",
                }
            },
        },
    }


def rpc_error(req_id, code, message):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }


def resolve_path(user_path):
    root = ROOT.resolve()
    target = (root / user_path).resolve()
    if not target.is_relative_to(root):
        raise PermissionError(f"path outside sandbox: {user_path}")
    return target


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

    try:
        if name == "list_dir":
            target = resolve_path(args["path"])
            names = sorted(p.name for p in target.iterdir())
            return ok_text(req_id, "\n".join(names))

        if name == "read_file":
            target = resolve_path(args["path"])
            return ok_text(req_id, target.read_text(encoding="utf-8"))
    except OSError as exc:
        return ok_text(req_id, f"{type(exc).__name__}: {exc}", is_error=True)

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