import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "01-mini-agent"))

from dotenv import load_dotenv

from client import McpClient
from registry import CompositeRegistry, McpRegistry
from transport import StdioTransport

from agent import Agent
from model import OpenAIModel, make_http_post
from tools import registry as local_registry

load_dotenv(ROOT.parent / ".env")

ECHO = [sys.executable, str(ROOT / "servers" / "echo.py")]


def main():
    client = McpClient(StdioTransport(ECHO, cwd=ROOT))
    client.start()
    try:
        mcp = McpRegistry(client)
        mcp.connect()
        model = OpenAIModel(
            model_id=os.environ.get("MODEL_ID", "kimi-k3"),
            post=make_http_post(
                api_base=os.environ["OPENAI_BASE_URL"],
                api_key=os.environ["OPENAI_API_KEY"],
            ),
        )
        agent = Agent(
            model=model,
            registry=CompositeRegistry(local_registry, mcp),
            max_steps=6,
        )
        print(agent.run("计算 37 * 19，并告诉我结果。"))
    finally:
        client.close()


if __name__ == "__main__":
    main()
