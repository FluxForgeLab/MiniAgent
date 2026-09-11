import unittest

from tools import registry

class ToolRegistryTest(unittest.TestCase):
    def test_execute_success(self):
        result = registry.execute("get_celsius", {"city":"北京"})
        self.assertTrue(result.ok)
        self.assertEqual(result.observation, "26.0")

    def test_missing_argument(self):
        result = registry.execute("get_celsius", {})
        self.assertFalse(result.ok)
        self.assertIn("missing arguments", result.observation)

    def test_unknown_tool(self):
        result = registry.execute("nope", {})
        self.assertFalse(result.ok)
        self.assertEqual(result.observation, "unknown tool: nope")

if __name__ == "__main__":
    unittest.main()