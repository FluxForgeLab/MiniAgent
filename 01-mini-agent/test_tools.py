import unittest

from tools import Tool, ToolRegistry, registry

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

    def test_optional_argument_is_not_required(self):
        search = Tool(
            name="search",
            description="搜索",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索词"},
                    "limit": {"type": "integer", "description": "最多返回几条"},
                },
                "required": ["query"],
            },
            handler=lambda query, limit=10: f"{query}:{limit}",
        )
        local = ToolRegistry()
        local.register(search)

        ok = local.execute("search", {"query": "foo"})
        self.assertTrue(ok.ok)
        self.assertEqual(ok.observation, "foo:10")

        missing = local.execute("search", {})
        self.assertFalse(missing.ok)
        self.assertIn("missing arguments", missing.observation)

if __name__ == "__main__":
    unittest.main()
