# Stage 1 第 8 课：Mini Agent v1 设计冻结

不变量、场景、模块边界已对齐。本文件冻结类型；实现从 `01-mini-agent/tools.py` 开始，干中学。

## 模块

```text
tools.py   注册 + 执行，返回 observation / error，不碰 memory
model.py   调 LLM，吐出 tool_call 或 final_answer，不管 max_steps
memory.py  存这次 run 的 steps，不派生 messages
context.py 从 memory 派生 messages，不执行工具
agent.py   while / 停 / 调用上面四层
main.py    组装并发起 run
```

observation：**tool 产生，agent 写入 memory。**  
messages：每次从 memory 派生，不是权威状态。  
max_steps：只在 `agent.py` 判断。

## 类型（最少字段）

表 A 补上 `Model` 和 `Agent`。`context` 不是仓库里的一类记录，是 `build(memory)` 的产物。

| 类型 | 最少字段 / 行为 | 为什么不能是一个 str |
|---|---|---|
| `Tool` | `name`, `description`, `input_schema`, `execute(arguments)` | schema 要给模型发现工具 |
| `ToolResult` | `ok`, `observation: str` | 失败也是一段观察，不把 run 炸掉 |
| `ModelOutput` | `kind: tool_call \| final_answer`；call 时有 `name+arguments`，answer 时有 `content` | 禁止第三种含糊状态 |
| `Step` | `tool_call`, `observation`, `error` | Step2 必须能读到上一圈的 `26.0` |
| `Memory` | `task`, `steps: list[Step]` | 仓库是列表，不是一坨字符串 |
| `Agent` | `max_steps`, `run(task)` | 循环和停止只放这里 |

成功停：方案 A，模型不再 tool call。强制停：`max_steps`。`StopCondition` 稍后插，本步不实现。

不做：Planner、MCP、长期 Memory、CodeAgent、`final_answer` 魔法工具。
