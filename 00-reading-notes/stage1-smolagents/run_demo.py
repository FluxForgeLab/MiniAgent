import os
from pathlib import Path

from dotenv import load_dotenv
from smolagents import OpenAIModel, ToolCallingAgent, tool

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@tool
def get_celsius(city: str) -> float:
    """返回指定城市当前气温（摄氏度）。
    Args:
        city: 城市名称
    """
    return 26.0

@tool
def celsius_to_fahrenheit(c: float)  -> float:
    """把摄氏度换成华氏度。
    Args:
        c: 摄氏度
    """
    return c * 9 / 5 + 32


model = OpenAIModel(
    model_id=os.environ.get("MODEL_ID", "gpt-4o-mini"),
    api_base=os.environ.get("OPENAI_BASE_URL"),  # 官方 OpenAI 可省略
    api_key=os.environ["OPENAI_API_KEY"],
)

agent = ToolCallingAgent(
    tools=[get_celsius, celsius_to_fahrenheit],
    model=model,
    max_steps=6,
)

if __name__  == "__main__":
    # result = agent.run("北京现在多少摄氏度？再把它换成华氏度。")
    result = agent.run("写一首五言绝句，不要调用任何工具。")
    print("RESULT:", result)