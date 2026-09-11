# Mini Agent v1

Stage 1 最小 Tool-Calling Agent。循环在 `agent.py`，其余文件各管一层。

## 文件

| 文件 | 职责 |
|---|---|
| `tools.py` | 注册、执行工具；返回 `ToolResult`，不写 memory |
| `model.py` | `FakeModel` / `OpenAIModel`；把 API JSON 翻成 `ModelOutput` |
| `memory.py` | 本次 `run` 的 `steps` |
| `context.py` | 从 memory 派生 messages（含 `tool_call_id`） |
| `agent.py` | `while` / 成功停 / `max_steps` |
| `main.py` | 读环境变量，接真模型，发起 `run` |
| `test_*.py` | 对应模块的 unittest |

不做：Planner、MCP、长期记忆、CodeAgent、`final_answer` 魔法工具。

## 运行

在本目录下。密钥只用**仓库根目录**的 `.env`（对照根目录 `env.example`），不要把 key 写进这个文件夹。

```powershell
python -m unittest discover -v
python main.py
```

`main.py` 会调用 Kimi，消耗 token。单测走 `FakeModel`，不联网。
