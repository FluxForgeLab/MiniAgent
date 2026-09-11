import unittest

from memory import Memory, Step

class MemoryTest(unittest.TestCase):
    def test_append_observation(self):
        memory = Memory(task="北京气温再换华氏度")
        memory.append(
            Step(
                tool_call={"name": "get_celsius", "arguments": {"city": "北京"}},
                observation="26.0",
            )
        )
        self.assertEqual(len(memory.steps), 1)
        self.assertEqual(memory.steps[0].observation, "26.0")

if __name__ == "__main__":
    unittest.main()