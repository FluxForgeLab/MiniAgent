import unittest

from context import build
from memory import Memory, Step


class ContextTest(unittest.TestCase):
    def test_build_includes_observation(self):
        memory = Memory(task="北京气温再换华氏度")
        memory.append(
            Step(
                tool_call={
                    "id": "call_1",
                    "name": "get_celsius",
                    "arguments": {"city": "北京"},
                },
                observation="26.0",
            )
        )
        messages = build(memory)
        self.assertEqual(messages[0]["content"], "北京气温再换华氏度")
        self.assertEqual(messages[-1]["content"], "26.0")
        self.assertEqual(messages[-1]["tool_call_id"], "call_1")
        self.assertEqual(messages[1]["tool_calls"][0]["id"], "call_1")

    def test_build_includes_error(self):
        memory = Memory(task="北京气温")
        memory.append(
            Step(
                tool_call={"name": "nope", "arguments": {}},
                error="unknown tool: nope",
            )
        )
        messages = build(memory)
        self.assertEqual(messages[-1]["content"], "unknown tool: nope")

if __name__ == "__main__":
    unittest.main()