import unittest

from agent import Agent
from model import FakeModel, ModelOutput
from tools import registry

class AgentTest(unittest.TestCase):
    def test_temperature_three_steps(self):
        model = FakeModel(
            [
                ModelOutput(kind="tool_call", name="get_celsius", arguments={"city": "北京"}),
                ModelOutput(kind="tool_call", name="celsius_to_fahrenheit", arguments={"c": 26}),
                ModelOutput(kind="final_answer", content="北京约 26.0°C，即 78.8°F"),
            ]
        )
        agent = Agent(model=model, registry=registry, max_steps=6)
        result = agent.run("北京现在多少摄氏度？再把它换成华氏度。")
        self.assertIn("78.8", result)

    def test_max_steps_stops_loop(self):
        model = FakeModel(
            [
                ModelOutput(kind="tool_call", name="get_celsius", arguments={"city": "北京"}),
                ModelOutput(kind="tool_call", name="celsius_to_fahrenheit", arguments={"c": 26}),
                ModelOutput(kind="final_answer", content="不应走到这里"),
            ]
        )
        agent = Agent(model=model, registry=registry, max_steps=2)
        result = agent.run("北京现在多少摄氏度？再把它换成华氏度。")
        self.assertEqual(result, "stopped: max_steps")

    def test_poem_stops_without_tools(self):
        model = FakeModel(
            [
                ModelOutput(kind="final_answer", content="月落寒江夜，星垂远树低。"),
            ]
        )
        agent = Agent(model=model, registry=registry, max_steps=6)
        result = agent.run("写一首五言绝句，不要调用任何工具。")
        self.assertIn("月落", result)

    def test_tool_error_does_not_stop_run(self):
        model = FakeModel(
            [
                ModelOutput(kind="tool_call", name="nope", arguments={}),
                ModelOutput(kind="tool_call", name="get_celsius", arguments={"city": "北京"}),
                ModelOutput(kind="final_answer", content="北京约 26.0°C"),
            ]
        )
        agent = Agent(model=model, registry=registry, max_steps=6)
        result = agent.run("北京现在多少摄氏度？")
        self.assertIn("26.0", result)

if __name__ == "__main__":
    unittest.main()