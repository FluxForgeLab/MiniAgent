import unittest

from model import (
    FakeModel,
    ModelOutput,
    OpenAIModel,
    parse_completion,
    to_openai_tools,
    build_chat_request,
    completion_url,
    auth_headers,
    format_http_error
)

class ModelOutputTest(unittest.TestCase):
    def test_tool_call(self):
        out = ModelOutput(kind="tool_call", name="get_celsius", arguments={"city": "北京"})
        self.assertEqual(out.kind, "tool_call")
        self.assertEqual(out.name, "get_celsius")

    def test_final_answer(self):
        out = ModelOutput(kind="final_answer", content="78.8°F")
        self.assertEqual(out.kind, "final_answer")
        self.assertIsNone(out.name)

    def test_fake_model_returns_scripted_outputs(self):
        model = FakeModel(
            [
                ModelOutput(kind="tool_call", name="get_celsius", arguments={"city": "北京"}),
                ModelOutput(kind="final_answer", content="done"),
            ]
        )
        first = model.generate(messages=[], tools_schema=[])
        second = model.generate(messages=[], tools_schema=[])
        self.assertEqual(first.name, "get_celsius")
        self.assertEqual(second.kind, "final_answer")

    def test_parse_completion_final_answer(self):
        payload = {
            "choices": [
                {"message": {"content": "月落寒江夜，星垂远树低。"}}
            ]
        }
        out = parse_completion(payload)
        self.assertEqual(out.kind, "final_answer")
        self.assertEqual(out.content, "月落寒江夜，星垂远树低。")

    def test_parse_completion_tool_call(self):
        payload = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "function": {
                                    "name": "get_celsius",
                                    "arguments": '{"city": "北京"}',
                                }
                            }
                        ]
                    }
                }
            ]
        }
        out = parse_completion(payload)
        self.assertEqual(out.kind, "tool_call")
        self.assertEqual(out.name, "get_celsius")
        self.assertEqual(out.arguments, {"city": "北京"})
        self.assertEqual(out.tool_call_id, "call_1")

    def test_to_openai_tools(self):
        schema = [
            {
                "name": "get_celsius",
                "description": "返回指定城市当前气温（摄氏度）。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "城市名称"},
                    },
                    "required": ["city"],
                },
            }
        ]
        tools = to_openai_tools(schema)
        fn = tools[0]["function"]
        self.assertEqual(tools[0]["type"], "function")
        self.assertEqual(fn["name"], "get_celsius")
        self.assertEqual(fn["parameters"]["required"], ["city"])
        self.assertEqual(fn["parameters"]["properties"]["city"]["type"], "string")

    def test_to_openai_tools_keeps_optional_out_of_required(self):
        schema = [
            {
                "name": "search",
                "description": "搜索",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索词"},
                        "limit": {"type": "integer", "description": "最多返回几条"},
                    },
                    "required": ["query"],
                },
            }
        ]
        params = to_openai_tools(schema)[0]["function"]["parameters"]
        self.assertEqual(params["required"], ["query"])
        self.assertIn("limit", params["properties"])
        self.assertNotIn("limit", params["required"])

    def test_build_chat_request(self):
        messages = [{"role": "user", "content": "北京气温"}]
        schema = [
            {
                "name": "get_celsius",
                "description": "气温",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "城市"},
                    },
                    "required": ["city"],
                },
            }
        ]
        body = build_chat_request("kimi-k3", messages, schema)
        self.assertEqual(body["model"], "kimi-k3")
        self.assertEqual(body["messages"], messages)
        self.assertEqual(body["tools"][0]["function"]["name"], "get_celsius")

    def test_openai_model_generate_final_answer(self):
        def fake_post(body: dict) -> dict:
            self.assertEqual(body["model"], "kimi-k3")
            self.assertEqual(body["messages"][0]["content"], "写诗")
            return {"choices": [{"message": {"content": "月落寒江夜"}}]}

        model = OpenAIModel(model_id="kimi-k3", post=fake_post)
        out = model.generate(
            messages=[{"role": "user", "content": "写诗"}],
            tools_schema=[],
        )
        self.assertEqual(out.kind, "final_answer")
        self.assertEqual(out.content, "月落寒江夜")

    def test_completion_url_and_headers(self):
        self.assertEqual(
            completion_url("https://api.moonshot.cn/v1"),
            "https://api.moonshot.cn/v1/chat/completions",
        )
        self.assertEqual(
            completion_url("https://api.moonshot.cn/v1/"),
            "https://api.moonshot.cn/v1/chat/completions",
        )
        headers = auth_headers("sk-test")
        self.assertEqual(headers["Authorization"], "Bearer sk-test")
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_format_http_error_includes_body(self):
        text = format_http_error(400, '{"error":{"message":"tool_call_id  is not found"}}')
        self.assertIn("400", text)
        self.assertIn("tool_call_id", text)

if __name__ == "__main__":
    unittest.main()
