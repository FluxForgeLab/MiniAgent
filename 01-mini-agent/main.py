import os
from pathlib import Path

from dotenv import load_dotenv

from agent import Agent
from model import OpenAIModel, make_http_post
from tools import registry

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def main() -> None:
    model = OpenAIModel(
        model_id=os.environ.get("MODEL_ID", "kimi-k3"),
        post=make_http_post(
            api_base=os.environ["OPENAI_BASE_URL"],
            api_key=os.environ["OPENAI_API_KEY"],
        ),
    )
    agent = Agent(model=model, registry=registry, max_steps=6)
    result = agent.run("北京现在多少摄氏度？再把它换成华氏度。")
    print(result)


if __name__ == "__main__":
    main()
